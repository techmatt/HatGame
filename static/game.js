'use strict';

const e = React.createElement;

const textIndicatingPlayerIsWriting = ' - writing'; // ✍️

// Displays the list of players on each team, with css to indicate the active player
// props:
//   teams - list of lists of player names
//   activePlayerIndexPerTeam - active player per team to highlight, or -1 for no highlight
//   playerWritingStatus - dict from player name to boolean, indicating the player is done writing
//                       - if the dict is null, don't show writing status
//  activeTeamIndex - the index of the team currently playing
// scores - optional list of scores for each team; if given will be shown
// showHostControls - boolean indicating we should show host controls
// handleAddPlayer - function that takes team index, to be called when adding a player to that team
// handleRemovePlayer - function that takes playerName, to be called when removing a player
// handleSkipPlayer - function that takes name of current player, to be called if the host wants to skip that player
function PlayerList(props) {
  console.log("Rendering PlayerList with props %o", props);
  if (typeof props.teams == 'undefined') {
    console.log("no player list to render yet");
    return e('div', null, ''); // Special case when we haven't loaded teams
  } else {
    return e(
      'table',
      { className: 'player_list_table' },
      e('tbody', null,
        props.teams.map((team, teamI) => {
          const scoreElement = (props.scores ?
            e('td',
              { className: 'score_display' },
              `score: ${props.scores[teamI]}`
            )
            : undefined
          );
          const addPlayerElement = (props.showHostControls ?
            e('td',
              { className: 'add_player' },
              e('button',
                { onClick: () => props.handleAddPlayer(teamI),
                  type: "button",
                  className: "host_control_button",
                  title:"Add player to this team"
                },
                'add player'
              )
            )
            : undefined
          );
          return e(
            'tr',
            { key: team },
            team.map((player, playerI) => {
              const playerOnDeck = (playerI == props.activePlayerIndexPerTeam[teamI]);
              const teamIsActive = (teamI == props.activeTeamIndex)
              const playerStatus = (playerOnDeck ?
                (teamIsActive ? 'active' : 'on_deck') : 'passive')
              const playerStillWriting = props.playerWritingStatus && !props.playerWritingStatus[player]
              const textForWriting = playerStillWriting ? textIndicatingPlayerIsWriting : '';
              const removalElement = (props.showHostControls ?
                e('button',
                  {
                    onClick: () => props.handleRemovePlayer(player),
                    title:`Remove ${player} from game`,
                    type: "button",
                    className: "host_control_button",
                  },
                  'remove' // '❌'
                )
                : undefined
                );
              const skipElement = (props.showHostControls && playerStatus == 'active' ?
                  e('button',
                    {
                      onClick: () => props.handleSkipPlayer(player),
                      title:`Skip ${player}'s turn'`,
                      type: "button",
                      className: "host_control_button",
                    },
                    'skip'
                  )
                  : undefined
                  );
              return e('td',
                {
                  key: player,
                  className: `${playerStatus}_player_in_list`
                },
                e('div', {}, 
                  player + textForWriting,
                  skipElement,
                  removalElement)
              );
            }
            ),
            scoreElement,
            addPlayerElement
          )
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
    this.textInputRefs = Array(props.phraseCount).fill(0).map(x => React.createRef());
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
        `Please enter ${this.props.phraseCount} words or short phrases that most players will recognize.`
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
    if (this.state.secondsRemaining < 1.0) {
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
                id: "checkbox " + word
              }
            ),
            e('label',
              {htmlFor: "checkbox " + word},
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
  //   player - the name of the player viewing this app
  //   gameId - the id of the game
  constructor(props) {
    super(props)
    this.state = {
      // This is an initial state until we load a state dict from the server
      mainPhase: 'Loading',
      showScores: false, // tracked on client
      showHostControls: false, // tracked on client
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
        // Merge this.state with the server state, to preserve the local-only state
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

    handlePhrasesCreation(phrases) {
      console.log("telling server we created phrases %o", phrases);
      this.postData(
        `/games/${this.props.gameId}/${this.props.player}/recordphrases`,
      {phrases: phrases});
    }
  
    handleTurnStart() {
    const endpoint = `/games/${this.props.gameId}/${this.props.player}/startturn`;
    this.postData(endpoint, null);
  }
  
  onWordClicked(word) {
    const endpoint = `/games/${this.props.gameId}/prevphrase/${word}`;
    this.postData(endpoint, null);
  }

  endTurn() {
    const endpoint = `/games/${this.props.gameId}/${this.props.player}/endturn`;
    this.postData(endpoint, null);
  }

  handleTimerExpiration() {
    console.log("Turn ended due to timer");
    this.endTurn();
  }

  handlePhraseConfirmation(phrases) {
    console.log("telling server we confirmed words %o", phrases);
    this.postData(
      `/games/${this.props.gameId}/${this.props.player}/confirmphrases`,
    {acceptedPhrases: phrases});
  }

  handleAddPlayer(teamIndex) {
    const newPlayerName = prompt("New player name");
    console.log(`Adding player ${newPlayerName} to team index ${teamIndex}`)
    this.postData(
      `/games/${this.props.gameId}/${this.props.player}/addplayertoteam`,
      {teamIndex: teamIndex,
        newPlayerName: newPlayerName}
      )
  }

  handleRemovePlayer(player) {
    console.log(`Removing player ${player}`);
    this.postData(
      `/games/${this.props.gameId}/${this.props.player}/removeplayer`,
      {playerName: player}
      )
  }

  handleSkipPlayer(currentPlayer) {
    console.log(`Skipping current player ${currentPlayer}`);
    this.postData(
      `/games/${this.props.gameId}/${currentPlayer}/confirmphrases`,
    {acceptedPhrases: []});
  }

  // returns the name of the active player
  activePlayer() {
    // activeTeam is a list of player names
    const activeTeam = this.state.teams[this.state.activeTeamIndex];
    const relevantIndex = this.state.activePlayerIndexPerTeam[this.state.activeTeamIndex];
    return activeTeam[relevantIndex];
  }

  isItMyTurn() {
    return this.props.player == this.activePlayer();
  }

  shouldDisplayScores() {
    return this.state.mainPhase == 'GameMainPhase.Done' || this.state.showScores;
  }

  mainPhaseText() {
    switch (this.state.mainPhase) {
      case "GameMainPhase.Write":
        return 'Word Creation'
      case "GameMainPhase.MultiWord":
        return 'Round One: Many-Word Clues'
      case "GameMainPhase.SingleWord":
        return 'Round Two: Single-Word Clues'
      case "GameMainPhase.Charade":
        return 'Round Three: Charades'
      case "GameMainPhase.Done":
        return 'Game Complete'
    }
  }

  renderInWritePhase() {
    const viewingPlayerIsDoneWriting = this.state.playerWritingStatus[this.props.player];
    
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

  messageAboutContinuationTurn() {
    console.log('seconds: %o %o', this.state.secondsRemaining, this.state.secondsPerTurn);
    if (this.state.secondsRemaining < this.state.secondsPerTurn) {
      return `${this.activePlayer()} gets to continue their turn with ` + 
      `${Math.round(this.state.secondsRemaining)} seconds remaining`
    } else {
      return undefined // empty element
    }
  }
  
  renderPreviousRoundPhraseList() {
    if (this.state.previousRoundPhrases && this.state.previousRoundPhrases.length > 0)
      return e(
        'div', { className: 'previous_turn_phrase_div' },
        'Phrases gotten in previous turn:',
        e('ul',
          null,
          this.state.previousRoundPhrases.map(phrase =>
            e('li', { key: phrase }, phrase)
          )
        ),
        this.messageAboutContinuationTurn()
      )
    else
      // no previous phrases, just return empty div, 
      return e('div', null)
  }

  renderWhenWaitingForStart() {
    if (this.isItMyTurn()) {
      return e(
        'div', null,
        this.renderPreviousRoundPhraseList(),
        e('button',
          {
            className: 'start_button',
            onClick: this.handleTurnStart.bind(this)
          },
          'Start'
        )
      )
    } else {
      return e(
        'div', null,
        this.renderPreviousRoundPhraseList(),
        e(
          'div', { className: 'waiting_for_player_to_start_text' },
          `Waiting for current player ${this.activePlayer()} to start their turn`
        )
      )
    }
  }

  unclickedHatWords() {
    return this.state.hat.filter(w => !this.state.clickedPhrases.includes(w));
  }

  renderWhenStarted() {
    if (this.isItMyTurn()) {
      const wordsToRender = this.unclickedHatWords().slice(0, 2);
      return e(
        'div',
        null,
        e(CountdownTimer,
          {
            initialSeconds: this.state.secondsRemaining,
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
      return e('div', null,
        e(CountdownTimer,
          {
            initialSeconds: this.state.secondsRemaining,
            timerExpirationCallback: () => {} // It's not our turn, so do nothing on turn end
          }
        ),
        this.state.prevPhrase ? e('div',
         {className: 'previous_phrase'},
         this.state.prevPhrase
        )
        : undefined // empty element if no previous phrase
      );
    }
  }

  renderWhenConfirmingPhrases() {
    if (this.isItMyTurn()) {
      return e(WordListConfirmer,
        {
          wordsDefaultingToChecked: this.state.clickedPhrases,
          wordsDefaultingToUnchecked: this.unclickedHatWords().slice(0, 2),
          callbackAfterConfirmation: this.handlePhraseConfirmation.bind(this),
        }
      )
    } else {
      return e(
        'div', null,
        `Waiting for current player ${this.activePlayer()} to confirm words`
      )
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
          'Thanks for playing!'
        );
      default:
        return e(
          'div', null,
          `Main phase not implemented yet: ${this.state.mainPhase}`
        );
    }
  }

  totalPhraseCount() {
    const playerCount = this.state.teams.map( t => t.length).reduce((a, b) => a + b);
    return this.state.phrasesPerPlayer * playerCount
  }

  hatSizeMessage() {
    if (this.state.hat && this.state.teams) {
      const countInHat = this.state.hat.length;
      return `Words in hat: ${countInHat} of ${this.totalPhraseCount()}`;
    } else {
      return undefined; // No hat, just create empty div
    }
  }

  render() {
    return e(
      'div',
      null,
      e('div',
        {className: 'main_phase_text'},
        this.mainPhaseText()
      ),
      e('div',
        {className: 'hat_size_text'},
        this.hatSizeMessage()
      ),
      e(PlayerList,
        {
          teams: this.state.teams,
          activePlayerIndexPerTeam: this.state.activePlayerIndexPerTeam,
          playerWritingStatus: this.state.mainPhase == "GameMainPhase.Write" ? this.state.playerWritingStatus : null,
          activeTeamIndex: this.state.activeTeamIndex,
          scores: this.shouldDisplayScores() ? this.state.scores : undefined,
          showHostControls: this.state.showHostControls,
          handleAddPlayer: this.handleAddPlayer.bind(this),
          handleRemovePlayer: this.handleRemovePlayer.bind(this),
          handleSkipPlayer: this.handleSkipPlayer.bind(this),
        }
      ),
      this.renderPhaseSpecificUI()
    );
  }

  postData(endpoint, data) {
    var responsePromise;
    if (data) {
      responsePromise = fetch("../../.." + endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
    } else {
      responsePromise = fetch("../../.." + endpoint, {
        method: 'POST',
      });
    }
    //return responsePromise.then(r => r.json()); // parses JSON response into native JavaScript objects
    responsePromise.then(r => r.text())
      .then(message => console.log(`server response: ${message}`))
      .then(x => this.getStateFromServer()); // once server recieves our post message, update our state based on the response
  }
}

const appElement = document.querySelector("#app");

const appComponent = ReactDOM.render(e(
  HatGameApp, 
  {player: appElement.getAttribute("data-player-id"),
  gameId: appElement.getAttribute("data-game-id")}
  ), 
  appElement);

  // Connect control checkboxes to the app component
  const scoreCheckbox = document.getElementById("show_score_checkbox")
  scoreCheckbox.onchange = () => {
    appComponent.setState({showScores: scoreCheckbox.checked})
  };

  const hostControlCheckbox = document.getElementById("host_controls_checkbox")
  hostControlCheckbox.onchange = () => {
    appComponent.setState({showHostControls: hostControlCheckbox.checked})
  };
  