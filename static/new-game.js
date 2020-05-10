/*** new-game.js ***
* handles client-side functions for
* starting a new game
***/

(function() {
	// define variables
	let minPlayers = 4;
	let maxPlayers = 10;
	let playerIncrement = 2;
	let playerCount = 1;
	// define active sections	
	let startButton = $("#footer .start");
	let playerSection = $("#players");
	let addPlayerButton = $("#players .add");
	let playerCountDisplay = $("#playerCount");
	// define player template from first player
	let playerTemplate = $("#players .input-section").clone(true);
	let removeButton = playerTemplate.children("button.remove.inactive");
	removeButton.removeClass("inactive"); // make removal active

	
	// getGameDict function: returns a gameDict based on visible parameters
	let getGameDict = function() {
		// get an array of player names
		let playerInputArray = document.querySelectorAll(".name-text");
		let playerArray = [].map.call(playerInputArray, function(playerInput) {
			return playerInput.value;
		});
		// filter out any nonexistent player names
		playerArray = playerArray.filter(function(player) {
			return player.trim() != "" && player !== undefined;
		});
		// check if array has empty strings
		if(playerArray.length !== playerInputArray.length) {
			return { error: "Empty name detected. Please provide names for all players" };
		}
		// check if array has duplicates
		if((new Set(playerArray)).size !== playerArray.length) {
			return { error: "Duplicate name detected. Please provide unique names for all players." };
		}
		// check that the number of players is valid
		if(playerArray.length < minPlayers || playerArray.length > maxPlayers || playerArray.length % 2 !== 0) {
			return { error: "Invalid number of valid players. Players must be between " + 
			    minPlayers + " and " + maxPlayers + " and player number must be even." };
		}
		// check if game ID is empty
		if(document.querySelector("#gameId").value === "") {
			return { error: "Game ID is a required field." };
		}
		// build the gameDict object
		let gameDict = {
			id: document.querySelector("#gameId").value,
			players: playerArray,
			phrasesPerPlayer: document.querySelector("#wordCount").value,
			secondsPerTurn: document.querySelector("#turnLength").value,
			videoURL: document.querySelector("#videoUrl").value
		}
		return gameDict;
	}
	// newGame function: creates a new game and sends client to its URL
	let newGame = function() {
		let endpoint = "api/newgame"
		let gameDict = getGameDict();
		if(gameDict.error) {
			alert(gameDict.error);
		} else {
			$.ajax({
				type: "POST",
				url: endpoint,
				data: JSON.stringify(gameDict),
				contentType: "application/json; charset=utf-8",
				dataType: "json",
				success: function(response) {
					if(response.error) {
						alert(response.error);
					} else {
						window.location = response.gameURL;
					}
				},
				failure: function(xhr, status, error) {
					alert("Could not connect with server. Please try again or contact support.");
				}
			});	
		}
	}
	
	// update the player count
    let updatePlayerCount = function() {
        playerCount = playerSection.children(".input-section").length;
        playerCountDisplay.text(playerCount);
    }
	
	// removePlayer function: removes a player from the list
	let removePlayer = function() {
		if( playerCount > minPlayers ) {
			this.parentNode.remove();
			updatePlayerCount();
		} else {
			alert("The minimum number of players is " + minPlayers + ".");
		}
	}
	
	// initialize removePlayer function for template
	removeButton.click(removePlayer)

	// newPlayer function: adds a new player to the list
	let newPlayer = function() {
		if( playerCount < maxPlayers ) {
			playerTemplate.clone(true).insertBefore(addPlayerButton);
			updatePlayerCount();
		} else {
			alert("The maximum number of players is " + maxPlayers + ".");
		}
        
	}

	// update the number of players to the expected default
	for( gix = playerCount; gix < minPlayers; gix+=1 ) {
		newPlayer();
	} 

	// event handlers
	startButton.click(newGame);
	addPlayerButton.click(newPlayer);

	
})();