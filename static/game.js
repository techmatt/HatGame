
const e = React.createElement;

const textIndicatingPlayerIsWriting = ' - writing'; // ✍️
// Displays the list of players, with css to indicate the active player
// props:
//   players - player list
//   activePlayerIdx - active player to highlight, or -1 for no hilight
//   playerHasCompletedPhrases - list of bools indicating player is done writing phrases
function PlayerList(props) {
  console.log("Rendering PlayerList with props %o", props);
  if(typeof props.players == 'undefined') {
    console.log("no player list to render yet");
    return e('div', null, ''); // Special case when we haven't loaded player list
  } else {
    return e(
      'table',
      {className: 'player_list_table'},
      e('tbody', null,
        props.players.map( (player, i) => {
          const playerStatus = (i == props.activePlayerIdx ? 'active' : 'passive');
          return e(
            'tr', 
            {key: player}, 
            e('td', 
            {className: `${playerStatus}_player_in_list`},
            player + (props.playerHasCompletedPhrases[i] ? '' : textIndicatingPlayerIsWriting)))
          }
        )
      )
    )
  }
}

// Used to collect the initial phrase list from a player
class PhraseListCreator extends React.Component {
  // props:
  //   phraseCount - number of phrases to collect
  //   onPhraseListCreation - function to call once phrases are collected that takes phraseList
  constructor(props) {
    super(props);
    console.log("creating a PhraseListCreator for %o phrases", props.phraseCount);
    this.textInputRefs = Array(props.phraseCount).fill(0).map(x => React.createRef());
    console.log("text input refs %o",  this.textInputRefs);
  }
  
  handleSubmit(event) {
    event.preventDefault();
    const  phrases = this.textInputRefs.map(
      r => r.current.value
    )
    console.log("Player wrote phrases %o", phrases);
    this.props.onPhraseListCreation(phrases);
  }
  
  render() {
    return e(
      'div',  
      null,
      e(
        'div',
        { className: 'phrase_input_prompt' },
        `Please enter ${this.props.phraseCount} phrases that most players will recognize.`
      ),
      e(
	      'form',
        { onSubmit: this.handleSubmit.bind(this) },
        this.textInputRefs.map(
          (textRef, i) =>
            e('div',
              {
                className: 'phrase_text_input',
                key: i, // React wants a unique key per item for checking state updates
              },
              e('input',
                {
                  className: 'phrase_text_input',
                  type: 'text',
                  ref: this.textInputRefs[i],
                }
              ),
            )
        ),
        e('button',
          {
            type: "submit",
            className: 'phrase_input_submit_button'
          },
          "Submit"
        )
      )
    )
  }
}

// Used to display the two words the current player is getting others to guess
// props:
//   words - the words to display
//   onWordClicked -  function that takes a word, to be called when a word is clicked
function ClickableWordDisplay(props) {
  return e(
    'div',
    null, 
    props.words.map(word => (
      e('div',
	{key: word},
	e('button',
          {className: "word_being_guessed",
           onClick: () => props.onWordClicked(word)
          },
          word
	 )
       )
    ))
  )
}

// Shows the remaining time in the current turn
class CountdownTimer extends React.Component {
  // props:
  // -- initialSeconds - number of seconds to count down from
  // -- timerExpirationCallback -- function to call when timer is done
  constructor(props) {
    super(props);
    this.state = {
      secondsRemaining: props.initialSeconds,
    };
  }

  componentDidMount() {
    this.timerID = setInterval(
      () => this.decrementSecondsRemaining(),
      1000
    );
  }

  componentWillUnmount() {
    clearInterval(this.timerID);
  }

  decrementSecondsRemaining() {
    if (this.state.secondsRemaining <= 1.0 && this.state.secondsRemaining > 0.0) {
      this.props.timerExpirationCallback();
    } else {
      this.setState((state, props) => ({
        secondsRemaining: state.secondsRemaining - 1
      }))
    }
  }
  
  render() {
    return e(
      'div', 
      {className: "seconds_remaining"},    
      `${Math.round(this.state.secondsRemaining)}`
     )
  }
}

// Lets the current player confirm the list of words they got
class WordListConfirmer extends React.Component {
  // props:
  //   wordsDefaultingToChecked - default checked list of words to confirm
  //   wordsDefaultingToUnchecked - default checked list of words to confirm
  //   callbackAfterConfirmation - function that takes confirmedWords
  constructor(props) {
    super(props);
    this.words = props.wordsDefaultingToChecked.concat(props.wordsDefaultingToUnchecked);
    console.log("creating a WordListConfirmer with words %o", this.words);
    this.wordCheckboxRefs = this.words.map(w => React.createRef());
    console.log("refs %o", this.wordCheckboxRefs);
  }

  handleSubmit(event) {
    event.preventDefault();
    const confirmedWords = [];
    console.log("refs %o", this.wordCheckboxRefs);
    this.words.forEach(
      (word, i) => {
        const checkbox = this.wordCheckboxRefs[i].current;
        if (checkbox.checked) {
          confirmedWords.push(word);
        }
      }
    );
    console.log("Player confirmed words " + confirmedWords);
    this.props.callbackAfterConfirmation(confirmedWords);
  }

  render() {
    const countDefaultingChecked = this.props.wordsDefaultingToChecked.length;
    return e(
      'form',
      { onSubmit: this.handleSubmit.bind(this) },
      this.words.map(
        (word, i) =>
          e('div',
            { key: word },
            e('input',
              {
                type: "checkbox",
                defaultChecked: (i < countDefaultingChecked),
                ref: this.wordCheckboxRefs[i],
                name: "checkbox " + word
              }
            ),
            e('label',
              null,
              word)
          )
      ),
      e('button',
        { type: "submit" },
        "Submit")
    )
  }
}

// Main game
class HatGameApp extends React.Component {
  // props:
  //  player - the name of the player viewing this app
  // gameId - the id of the game
  constructor(props) {
    super(props)
    this.state = {
      mainPhase: 'Loading',
      wordsClicked: [], // Not from server, tracked on client
    }
    console.log("Constructing HatGameApp with props %o", props)
  }

  componentDidMount() {
    this.getStateFromServer();
    this.startListeningForServerUpdates();
  }

  getStateFromServer() {
    fetch('../../../api/gamestate/' + this.props.gameId)
			.then(response => response.json())
			.then(data => {
        console.log("got state from server %o", data);
        // Merge this.state with the server state, to preserve any local-only state
				this.setState((state, props) => ({...this.state, ...data}));
			});
  }

  startListeningForServerUpdates() {
    var source = new EventSource(`/api/stream/${this.props.gameId}/${this.props.player}/events`);
    source.onmessage = (event => {
      console.log("Server told client to update.  Loading state from server.");
      this.getStateFromServer();
      });
    }

  handleTurnStart() {
    const endpoint = `/games/${this.props.gameId}/${this.props.player}/startturn`;
    this.postData(endpoint, null);
    // wordsClicked is tracked locally; initially its empty
    this.setState({
      wordsClicked: []
    });
    this.getStateFromServer();
  }

  handlePhrasesCreation(phrases) {
    console.log("telling server we created phrases %o", phrases);
    this.postData(
      `/games/${this.props.gameId}/${this.props.player}/recordphrases`,
    {phrases: phrases});
    this.getStateFromServer();
  }
  
  onWordClicked(word) {
    this.setState((state, props) => ({
      wordsClicked: state.wordsClicked.concat([word]),
    }));
  }

  endTurn() {
    const endpoint = `/games/${this.props.gameId}/${this.props.player}/endturn`;
    this.postData(endpoint, null);
    this.getStateFromServer();
  }

  handleTimerExpiration() {
    console.log("Turn ended due to timer");
    this.endTurn();
    //this.setState({
    //  subPhase: 'GameSubPhase.ConfirmingPhrases'
    //});
  }
  
  postData(endpoint, data) {
    var responsePromise;
    if (data) {
      responsePromise = fetch("../../.." + endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: (data ? JSON.stringify(data) : null)
      });
    } else {
      responsePromise = fetch("../../.." + endpoint, {
        method: 'POST',
      });
    }
    //return responsePromise.then(r => r.json()); // parses JSON response into native JavaScript objects
    responsePromise.then(r => r.text())
      .then(message => console.log(`server response: ${message}`));
    this.getStateFromServer();
  }
  /*
  postData(endpoint, data) {
    console.log(`posting to %o with data %o`, endpoint, data);
    $.ajax({
      type: "POST",
      url: "../../.." + endpoint,
      data: JSON.stringify(data),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(response) {
        if(response.error) {
          alert(response.error);
        } else {
          console.log(`server response ${response}`)
        }
      },
      failure: function(xhr, status, error) {
        alert(`Could not connect with server. error: ${error}`);
      }
    });	
  }
  */

  handlePhraseConfirmation(phrases) {
    console.log("telling server we confirmed words %o", phrases);
    this.postData(
      `/games/${this.props.gameId}/${this.props.player}/confirmphrases`,
    {acceptedPhrases: phrases});
  }

  viewingPlayerIndex() {
    return this.state.players.indexOf(this.props.player);
  }

  isItMyTurn() {
    const viewingPlayerIndex = this.viewingPlayerIndex();
    if (viewingPlayerIndex == -1) {
      const message = (
        `Game is in a weird state where viewing player ${this.props.player} ` + 
        `is not in player list ${this.state.players}.  Please double check your url.`
      );
      alert(message);
    };
    console.log("Player list %o", this.state.players);
    console.log("index of player %o is %o; current player index is %o",
      this.state.players, viewingPlayerIndex, this.state.activePlayerIdx);
    return viewingPlayerIndex == this.state.activePlayerIdx;
  }

  renderInWritePhase() {
    const viewingPlayerIsDoneWriting = this.state.playerHasCompletedPhrases[this.viewingPlayerIndex()];
    console.log("Viewing player index %o, list %o",
      this.viewingPlayerIndex(), this.state.playerHasCompletedPhrases);
    
    if (viewingPlayerIsDoneWriting) {
      return e(
        'div',
        null,
        'Waiting for everyone to finish writing'
      );
    } else {
      return e(
        PhraseListCreator,
        {
          phraseCount: this.state.phrasesPerPlayer,
          onPhraseListCreation: this.handlePhrasesCreation.bind(this),
        }
      );
    }
  }

  renderWhenWaitingForStart() {
    if (this.isItMyTurn()) {
      return e('div', null,
          e('button',
            {className: 'start_button',
             onClick: this.handleTurnStart.bind(this)
             },
            'Start'
           )
         )
        } else {
          const activePlayer = this.state.players[this.state.activePlayerIdx];
          return e(
	    'div', null,
            `Waiting for current player ${activePlayer} to start game`
          )
        }
  }

  unclickedHatWords() {
    return this.state.hat.filter(w => !this.state.wordsClicked.includes(w));
  }

  renderWhenStarted() {
    if (this.isItMyTurn()) {
      if (this.state.wordsClicked.length == this.state.hat.length) {
        this.endTurn();
      }
      const wordsToRender = this.unclickedHatWords().slice(0, 2);
      return e(
        'div',
        null,
        e(CountdownTimer,
          {
            initialSeconds: this.state.secondsPerTurn,
            timerExpirationCallback: this.handleTimerExpiration.bind(this)
          }
        ),
        e(ClickableWordDisplay,
          {
            words: wordsToRender,
            onWordClicked: this.onWordClicked.bind(this)
          }
        )
      )
    } else {
      return e(CountdownTimer,
        {
          initialSeconds: this.state.secondsRemaining,
          timerExpirationCallback: this.handleTimerExpiration.bind(this)
        }
      )
    }
  }

  renderWhenConfirmingPhrases() {
    if (this.isItMyTurn()) {
      return e(WordListConfirmer,
        {
          wordsDefaultingToChecked: this.state.wordsClicked,
          wordsDefaultingToUnchecked: this.unclickedHatWords().slice(0, 2),
          callbackAfterConfirmation: this.handlePhraseConfirmation.bind(this),
        }
      )
    } else {
      const activePlayer = this.state.players[this.state.activePlayerIdx];
      return e(
        'div', null,
        `Waiting for current player ${activePlayer} to confirm words`
      )
      // TODO Enter state of waiting for server
    }
  }

  renderWhenPlayingGame() {
    switch (this.state.subPhase) {
      case 'GameSubPhase.WaitForStart':
        return this.renderWhenWaitingForStart();

      case 'GameSubPhase.Started':
        return this.renderWhenStarted();

      case 'GameSubPhase.ConfirmingPhrases':
        return this.renderWhenConfirmingPhrases();

      default:
        return e(
          'div', null,
          `Sub phase not implemented yet: ${this.state.subPhase}`
        )
    }
  }

  renderPhaseSpecificUI() {
    switch (this.state.mainPhase) {
      case 'Loading':
        return e(
          'div', { className: "loading_text" },
          'Loading....'
        );
      case
        'GameMainPhase.Write':
        return this.renderInWritePhase();
      case 'GameMainPhase.MultiWord':
      case 'GameMainPhase.SingleWord':
      case 'GameMainPhase.Charade':
        return this.renderWhenPlayingGame();
      case 'GameMainPhase.Done':
        return e(
          'div',
          { className: "game_done_text" },
          `Game complete, thanks for playing! Scores: ${this.state.scores}`
        );
      default:
        return e(
          'div', null,
          `Main phase not implemented yet: ${this.state.mainPhase}`
        );
    }
  }

  render() {
    return e(
      'div',
      null,
      e('div',
        {className: 'main_phase_text'},
        this.state.mainPhase
      ),
      e(PlayerList,
        {
          players: this.state.players,
          activePlayerIdx: this.state.activePlayerIdx,
          playerHasCompletedPhrases: this.state.playerHasCompletedPhrases,
        }
      ),
      this.renderPhaseSpecificUI()
    );
  }
}

const appElement = document.querySelector("#app");

ReactDOM.render(e(
  HatGameApp, 
  {player: appElement.getAttribute("data-player-id"),
  gameId: appElement.getAttribute("data-game-id")}
  ), 
  appElement);
