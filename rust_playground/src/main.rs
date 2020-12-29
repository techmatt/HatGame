use warp::Filter;
use warp::sse::ServerSentEvent;
use serde_derive::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use tokio::sync::mpsc;
use futures::{Stream, StreamExt};


/*
  This is a toy version of using ServerSentEvents to transmit game states.
  We store a channel for each user and broadcast update state to those channels.

  Example calls:
  curl http://localhost:9000/api/stream/game_xyz/peter/events
  Then in a separate terminal:
  curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"phrases": ["Google", "Cat", "Hike"]}' \
      http://localhost:9000/games/xyz/peter/recordphrases

  curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"phrases": ["Adobe", "Dog", "Table Top"]}' \
      http://localhost:9000/games/xyz/matt/recordphrases
 */


// Game state we'll serialize to json for clients
// Todo: Separate the ClientFacingGameState from the server's overall GameState
#[derive(Debug, Clone)]
#[derive(Deserialize, Serialize)]
struct GameState {
    hat: Vec<String>
}
/// Our list of user channels to send updates to
type UserChannels = Arc<Mutex<Vec<mpsc::UnboundedSender<GameState>>>>;

// Body of the recordphrases endpoint
#[derive(Deserialize, Serialize)]
struct RecordPhrasesMessage {
    phrases: Vec<String>
}


#[tokio::main]
async fn main() {
    println!("Starting Server!");

    let current_game_state = Arc::new(Mutex::new(
        GameState {hat: Vec::new()}
    ));
    // Create a warp Filter that we can zip with requests in order to read the global variable
    let game_state_filter = warp::any().map(move || current_game_state.clone());

    let user_channels: UserChannels = Arc::new(Mutex::new(Vec::new()));
    let user_channels_filter = warp::any().map(move || user_channels.clone());

    // /games/<gameId>/<playerId>/recordphrases
    let record_phrases_route = warp::post()
        .and(warp::path!("games" / String / String / "recordphrases"))
        // For security only accept bodies smaller than 16kb (Copying example)
        .and(warp::body::content_length_limit(1024 * 16))
        .and(warp::body::json())
        // zip in the global values we want need to respond to the request
        .and(user_channels_filter.clone())
        .and(game_state_filter)
        .map(|game_id: String,
              player_id: String,
              m: RecordPhrasesMessage,
              ucs: UserChannels,
              g: Arc<Mutex<GameState>>| {
            println!("For game {}, player {}, Received phrases {:?}",
                     game_id, player_id, m.phrases);
            let mut game_state = g.lock().unwrap();
            println!("Adding new phrases {:?} to current hat {:?}", m.phrases, game_state);
            game_state.hat.append(&mut m.phrases.clone());
            broadcast_game_state(&game_state, &ucs);
            warp::reply::html("phrases recorded")
        }).boxed(); // .boxed() makes this compile faster

    let event_subscription_route = warp::get()
        .and(warp::path!("api" / "stream" / String / String / "events"))
        .and(user_channels_filter)
        .map(|game_id, player_id, channels| {
            println!("player {} subscribed to events for game {}", player_id, game_id);
        // reply using server-sent events
        let stream = create_user_connection(channels);
        warp::sse::reply(warp::sse::keep_alive().stream(stream))
    });
    let hello_from_warp = warp::get()
        .and(warp::path!("hello" / "from" / "warp")
            .map(|| "Hello from warp!"))
        .boxed();

    let routes = record_phrases_route.or(event_subscription_route).or(hello_from_warp);

    warp::serve(routes).run(([127, 0, 0, 1], 9000)).await;
}

// note: For now there is no game ID, just a global user list
fn create_user_connection(user_channels: UserChannels)
    -> impl Stream<Item = Result<impl ServerSentEvent + Send + 'static, warp::Error>> + Send + 'static
{
    println!("Creating a stream");
    let (tx, rx) = mpsc::unbounded_channel();
    // We add the transmit side to our global list for future game-state messages
    user_channels.lock().unwrap().push(tx);
    // We return a lambda-like thing that waits for messages on the receiver side and returns them
    // to the client
    // Note that rx includes the Stream trait, and
    // https://docs.rs/futures/0.3.8/futures/stream/trait.StreamExt.html
    // lets us call map on that Stream
    rx.map(|game_state|
        Ok(warp::sse::data(serde_json::to_string(&game_state).unwrap()))
    )
}

fn broadcast_game_state(g: &GameState, user_channels: &UserChannels) {
    // We use `retain` instead of a for loop so that we can reap any user that
    // appears to have disconnected.
    user_channels.lock().unwrap().retain(|tx| {
        let send_result = tx.send(g.clone());
        let should_retain = send_result.is_ok();
        should_retain
    });
}
