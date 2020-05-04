const e = React.createElement;

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
      secondsRemaining: 13,
      activePlayerIdx: 0,
      phrasesPerPlayer: 7,
      players: ['matt', 'amanda', 'graham', 'peter'], 
      scores: [40, 25],
      videoURL: 'https://zoom.com',
      wordsClicked: [], // Not from server, tracked on client
    }
  }
  
  onWordClicked(word) {
    const oldWordslicked = this.state.wordsClicked;
    const oldHat = this.state.hat;
    this.setState({
      hat: oldHat.filter(w => w !== word),
      wordsClicked: oldWordslicked.concat([word]),
    });
    // Check if we just clicked the last word in the hat
    if (oldHat.length == 1) {
    	this.endTurn();
    }
  }
  
  endTurn() {
  	clearInterval(this.timerId)
      console.log("telling server turn is done");
      this.setState({subPhase: 'GameSubPhase.ConfirmingPhrases'})
  }
  
  decrementSecondsRemaining() {
    if (this.state.secondsRemaining <= 1.0 && this.state.secondsRemaining > 0.0) {
    	this.endTurn();
    } else {
  	  this.setState((state, props) => ({
        secondsRemaining: state.secondsRemaining - 1
      }))
    }
  }
  
  startTimer() {
  	this.timerId = setInterval(() => this.decrementSecondsRemaining(), 
    1000);
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
                this.startTimer();
              }
             },
              'Start'
           )
         )        
        } else {
        return e('div', null,
          'Waiting for current player to start game'
        )
        }
  }

    renderWhenStarted() {
      if (this.isItMyTurn()) {
          let wordsToRender = this.state.hat.slice(0, 2);
        return e('div', null,
          e('div', 
          {className:"seconds_remaining"},
          
            `${Math.round(this.state.secondsRemaining)}`),
          e('div', null, 
            wordsToRender.map(word => (
              e('div',
              {key: word},
              e('button',
                {className: "word_being_guessed",
                onClick: () => this.onWordClicked(word)
                },
                word
              )
              )
            ))
          )
          )
        
        } else {
        return e('div', null,
          'Waiting for current player to start game'
				);
        }
  }
  
  handleConfirmWords(event) {
  	event.preventDefault();
    console.log("Confirming words...")
  }
  
  renderConformingPhrases() {
  	console.log("Confirming words %o", this.state.wordsClicked);
    return e('form',
      {onSubmit: this.handleConfirmWords},
      this.state.wordsClicked.map(word => 
        e('div', 
          {key: word},
          e('input',
           {type: "checkbox",
            defaultChecked: "true",
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

  render() {
    switch(this.state.subPhase) {
      case 'GameSubPhase.WaitForStart':
      	return this.renderWhenWaitingForStart();
        
      case 'GameSubPhase.Started':
        return this.renderWhenStarted();
        
      case 'GameSubPhase.ConfirmingPhrases':
        return this.renderConformingPhrases();
        
      default:
        return e('div', null,
          `Not implemented yet: ${this.state.subPhase}`
          )
       }
  }
}

ReactDOM.render(e(HatGameApp), document.querySelector("#app"))

