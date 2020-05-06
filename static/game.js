const e = React.createElement;

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

class HatGameApp extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      subPhase: 'GameSubPhase.WaitForStart',
      mainPhase: 'GameMainPhase.Charade',
      hat: [
        'Cat', 
        'Dog',
        'Elephant',
        'Zebra',
       ],
      secondsPerTurn: 30,
      activePlayerIdx: 0,
      phrasesPerPlayer: 7,
      players: ['matt', 'amanda', 'graham', 'peter'], 
      scores: [40, 25],
      videoURL: 'https://zoom.com',
      wordsClicked: [], // Not from server, tracked on client
    }
    this.handleWordConfirmation = this.handleWordConfirmation.bind(this);
    this.handleTimerExpiration = this.handleTimerExpiration.bind(this);
    this.onWordClicked = this.onWordClicked.bind(this);
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
	    {initialSeconds: 13,
	     timerExpirationCallback: this.handleTimerExpiration}
	   ),
	  e(ClickableWordDisplay,
	    {words: wordsToRender,
	     onWordClicked: this.onWordClicked}
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
    
  render() {
    switch(this.state.subPhase) {
      case 'GameSubPhase.WaitForStart':
      	return this.renderWhenWaitingForStart();
        
      case 'GameSubPhase.Started':
        return this.renderWhenStarted();
        
      case 'GameSubPhase.ConfirmingPhrases':
      return e(WordListConfirmer,
	       {words: this.state.wordsClicked,
		callbackAfterConfirmation: this.handleWordConfirmation
	       }
	      );
        
      default:
      return e(
	'div', null,
        `Not implemented yet: ${this.state.subPhase}`
      )
    }
  }
}

ReactDOM.render(e(HatGameApp), document.querySelector("#app"))
