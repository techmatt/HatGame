/*** new-game.js ***
* handles client-side functions for
* starting a new game
***/

(function() {
	// define buttons
	let startButton = $("#footer .start");
	let addPlayerButton = document.querySelector("#addPlayers .add");
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
	// event handlers
	startButton.click(newGame)
})();