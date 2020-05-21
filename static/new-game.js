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
	let teamNamePrefix = "Team ";

	// define active sections	
	let startButton = $("#footer .start");
	let playerSection = $("#players");
	let playerCountDisplay = $("#playerCount");

	// define team template from first team
	let teamTemplate = $(".team-section").clone(true);

	// define player template from first player
	let playerTemplate = $("#players .player-add").clone(true);
	playerTemplate.addClass("player-section");
	playerTemplate.children("button.add").addClass("inactive");
	playerTemplate.children("button.remove").removeClass("inactive");
	playerTemplate.children(".handle").removeClass("inactive");
    
	
	// getGameDict function: returns a gameDict object based on visible parameters
	let getGameDict = function() {
		// get an array of player names
		let teamArray = document.querySelectorAll(".team-section");
		let teamObject = [].map.call(teamArray, function(team) {
			    let playerInputArray = team.querySelectorAll(".player-section");
			    let playerArray = [].map.call(playerInputArray, function(playerInput) {
			        return $(playerInput).children('.name-text').val();
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
		        // check if team is empty
		        if(playerArray.length < 1) {
		        	team.delete;
		        }
		        return playerArray;
		});

	    // check that the number of players is valid
	    /***
		if(playerArray.length < minPlayers || playerArray.length > maxPlayers || playerArray.length % 2 !== 0) {
			return { error: "Invalid number of valid players. Players must be between " + 
				minPlayers + " and " + maxPlayers + " and player number must be even." };
		}
		***/
		
		// build the gameDict object
		let gameDict = {
			teams: teamObject,
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
			dialog.throwError(gameDict.error);
		} else {
			$.ajax({
				type: "POST",
				url: endpoint,
				data: JSON.stringify(gameDict),
				contentType: "application/json; charset=utf-8",
				dataType: "json",
				success: function(response) {
					if(response.error) {
						dialog.throwError(response.error);
					} else {
						window.location = response.gameURL;
					}
				},
				failure: function(xhr, status, error) {
					dialog.throwError("Could not connect with server. Please try again or contact support.");
				}
			});	
		}
	}
	
		// newTeam function: adds a new team to the list
	let addTeam = function(teamName) {
		let newTeam = teamTemplate.clone();
		newTeam.children(".team-name").text(teamName);
		playerSection.append(newTeam);
	}

	// update the player count and make sure only one blank team displays
    let cleanUpPlayersAndTeams = function() {
    	let teams = playerSection.children(".team-section");
    	let teamIndex = 1;
    	teams.each(function() {
    		if($(this).children(".player-section").length === 0) {
    			this.remove();
    		} else {
    			$(this).children(".team-name").text(teamNamePrefix + teamIndex);
    			teamIndex += 1;
    		}
    	});
    	addTeam(teamNamePrefix + teamIndex);
    }
	
	// removePlayer function: removes a player from the list
	let removePlayer = function() {
		this.parentNode.remove();
		cleanUpPlayersAndTeams();
	}

	// newPlayer function: adds a new player to the list in the same team
	let addPlayer = function() {
		if( playerCount < maxPlayers ) {
			// get the new player name and clear it from the add function
			let newPlayerName = $(this).parent().children(".name-text").val();
			let currentTeam = $(this).closest(".team-section")
			if(newPlayerName != "") {
				$(this).parent().children(".name-text").val(""); // clear the add player input
				let newPlayer = playerTemplate.clone();
				newPlayer.children(".name-text").val(newPlayerName);
				// if a player was just added to an empty team, add a new blank team
				currentTeam.append(newPlayer);
				cleanUpPlayersAndTeams();
			} else {
				dialog.throwError("Please enter a player name.");
			}
		} else {
			dialog.throwError("The maximum number of players is " + maxPlayers + ".");
		}   
	}

	// event handlers
	playerSection.on("click", ".remove", removePlayer);
	playerSection.on("click", ".add", addPlayer);
	startButton.click(newGame);

	// cleanup
	cleanUpPlayersAndTeams();
})();