const USE_FAKE_STATE = true;
const FAKE_STATE = {
  //mainPhase: 'GameMainPhase.Charade',
  mainPhase: 'GameMainPhase.Write',
  subPhase: 'GameSubPhase.WaitForStart',
  hat: [
    'Cat',
    'Dog',
    'Elephant',
    'Zebra',
  ],
  secondsPerTurn: 7,
  activePlayerIdx: 0,
  phrasesPerPlayer: 3,
  players: ['matt', 'amanda', 'graham', 'peter'], 
  scores: [40, 25],
  videoURL: 'https://zoom.com',
};

const e = React.createElement;

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
  //   words - list of words to confirm
  //   callbackAfterConfirmation - function that takes confirmedWords
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this)
    console.log("creating a WordListConfirmer with words %o", props.words);
    this.wordCheckboxRefs = props.words.map(w => React.createRef());
    console.log("refs %o",  this.wordCheckboxRefs);
  }
  
  handleSubmit(event) {
    event.preventDefault();
    const confirmedWords = [];
    console.log("refs %o", this.wordCheckboxRefs);
    this.props.words.forEach(
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
    return e(
      'form',
      {onSubmit: this.handleSubmit},
      this.props.words.map(
	(word, i) => 
	  e('div', 
	    {key: word},
	    e('input',
	      {type: "checkbox",
	       defaultChecked: "true",
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
        {type:"submit"},
        "Submit")
    )
  }
}


// Main game
class HatGameApp extends React.Component {
  // props:
  //  playerId - the name of the player viewing this app
  constructor(props) {
    super(props)
    this.state = {
      mainPhase: 'Loading',
      wordsClicked: [], // Not from server, tracked on client
    }
    this.handleWordConfirmation = this.handleWordConfirmation.bind(this);
    this.handleTimerExpiration = this.handleTimerExpiration.bind(this);
    console.log("Current player %o", props.playerId)
  }

  componentDidMount() {
    if (USE_FAKE_STATE) {
       this.setState(FAKE_STATE);
    } else {
      this.setState(getStateFromServer());
    }
  }

  getStateFromServer() {
    // TODO
  }

  handlePhrasesCreation(phrases) {
    console.log("Telling server about wordList: %o", phrases);
  }
  
  onWordClicked(word) {
    this.setState((state, props) => ({
      hat: state.hat.filter(w => w !== word),
      wordsClicked: state.wordsClicked.concat([word]),
      // update the subPhase if we just clicked the last word
      subPhase: (state.hat.length == 1 ? 'GameSubPhase.ConfirmingPhrases' : state.subPhase)
    }));
  }

  handleTimerExpiration() {
    console.log("Turn ended due to timer");
    this.setState({
      subPhase: 'GameSubPhase.ConfirmingPhrases'
    });
  }
    
  handleWordConfirmation(confirmedWords) {
    console.log("main app notified of confirmedWords %o", confirmedWords);
  }

  isItMyTurn() {
    return true; // todo
  }

  renderWhenWaitingForStart() {
    if (this.isItMyTurn()) {
      return e('div', null,
          e('button',
            {className: 'start_button',
             onClick: () => {
                this.setState({subPhase: 'GameSubPhase.Started'});
              }
             },
              'Start'
           )
         )
        } else {
          return e(
	    'div', null,
            'Waiting for current player to start game'
          )
        }
  }

  renderWhenStarted() {
      if (this.isItMyTurn()) {
        const wordsToRender = this.state.hat.slice(0, 2);
        return e(
	  'div',
	  null,
	  e(CountdownTimer,
	    {initialSeconds: this.state.secondsPerTurn,
	     timerExpirationCallback: this.handleTimerExpiration}
	   ),
	  e(ClickableWordDisplay,
	    {words: wordsToRender,
	     onWordClicked: this.onWordClicked.bind(this)}
	   )
        )        
      } else {
        return e(
	  'div',
	  null,
	  'Waiting for current player to start game'
	);
      }
  }
    
  renderWhenPlayingGame() {
    switch (this.state.subPhase) {
      case 'GameSubPhase.WaitForStart':
        return this.renderWhenWaitingForStart();

      case 'GameSubPhase.Started':
        return this.renderWhenStarted();

      case 'GameSubPhase.ConfirmingPhrases':
        return e(WordListConfirmer,
          {
            words: this.state.wordsClicked,
            callbackAfterConfirmation: this.handleWordConfirmation,
          }
        );

      default:
        return e(
          'div', null,
          `Sub phase not implemented yet: ${this.state.subPhase}`
        )
    }
  }

  render() {
    switch (this.state.mainPhase) {
      case 'Loading':
        return e(
          'div', { className: "loading_text" },
          'Loading....'
        )
      case
        'GameMainPhase.Write':
        return e(
          PhraseListCreator,
          {
            phraseCount: this.state.phrasesPerPlayer,
            onPhraseListCreation: this.handlePhrasesCreation.bind(this),
          }
        )
      case 'GameMainPhase.MultiWord':
      case 'GameMainPhase.SingleWord':
      case 'GameMainPhase.Charade':
        return this.renderWhenPlayingGame();
      case 'GameMainPhase.Done':
        return e(
          'div',
          { className: "game_done_text" },
          'Game complete, thanks for playing!'
        )
      default:
        return e(
          'div', null,
          `Main phase not implemented yet: ${this.state.mainPhase}`
        )
    }
  }
}

const appElement = document.querySelector("#app");

ReactDOM.render(e(
  HatGameApp, 
  {playerId: appElement.getAttribute("data-player-id")}
  ), 
  appElement)
