use warp::Filter;
use serde_derive::{Deserialize, Serialize};

#[derive(Deserialize, Serialize)]
struct RecordPhrasesMessage {
    phrases: Vec<String>
}

#[tokio::main]
async fn main() {
    println!("Starting Server!");

    let record_phrases_route = warp::post()
        .and(warp::path("recordphrases"))
        // Only accept bodies smaller than 16kb...
        .and(warp::body::content_length_limit(1024 * 16))
        .and(warp::body::json())
        .map(|m: RecordPhrasesMessage| {
            println!("Received phrases {:?}", m.phrases);
            warp::reply::html("phrases recorded")
        });

    //  /api/stream/<gameId>/<playerId>/events

    let sum_route = warp::path!("sum" / u32 / u32)
        .map(|a, b| format!("{} + {} = {}", a, b, a + b));
    let routes = record_phrases_route.or(sum_route);

    warp::serve(routes).run(([127, 0, 0, 1], 9000)).await;
}
