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
    let draggedPlayer = {};
    let dragIterator = 0;

    // define active sections	
    let startButton = $("#footer .start");
    let playerSection = $("#players");
    let randomizeButton = $(".randomize");

    // define team template from first team
    let teamTemplate = $(".team-section").clone(true);

    // define player template from first player
    let playerTemplate = $("#players .player-add").clone(true);
    playerTemplate.addClass("player-section");
    playerTemplate.children("button.add").addClass("inactive");
    playerTemplate.children("button.remove").removeClass("inactive");
    playerTemplate.children(".handle").removeClass("inactive");
    playerTemplate.removeClass("player-add");

    // getGameDict function: returns a gameDict object based on visible parameters
    let getGameDict = function() {
        // get an array of player names
        let teamArray = document.querySelectorAll(".team-section");
        teamArray = [].map.call(teamArray, function(team) {
            let playerInputArray = team.querySelectorAll(".player-section");
            let playerArray = [].map.call(playerInputArray, function(playerInput) {
                return $(playerInput).children('.name-text').val();
            });
            // filter out any nonexistent player names
            playerArray = playerArray.filter(function(player) {
                return player.trim() != "" && player !== undefined;
            });
            // check if array has empty strings
            if (playerArray.length !== playerInputArray.length) {
                return {
                    error: "Empty name detected. Please provide names for all players"
                };
            }
            // check if array has duplicates
            if ((new Set(playerArray)).size !== playerArray.length) {
                return {
                    error: "Duplicate name detected. Please provide unique names for all players."
                };
            }

            return playerArray;
        });

        // remove empty from array
        teamArray = teamArray.filter(team => team.length > 0);

        // build the gameDict object
        let gameDict = {
            teams: teamArray,
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
        if (gameDict.error) {
            dialog.throwError(gameDict.error);
        } else {
            $.ajax({
                type: "POST",
                url: endpoint,
                data: JSON.stringify(gameDict),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                success: function(response) {
                    if (response.error) {
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
            if ($(this).children(".player-section").length === 0) {
                this.remove();
            } else {
                $(this).children(".team-name").text(teamNamePrefix + teamIndex);
                teamIndex += 1;
            }
            // clean up player target behavior
            $(this).removeClass("player-target");
        });
        addTeam(teamNamePrefix + teamIndex);
        $(playerSection).addClass("not-dragging");
    }

    // removePlayer function: removes a player from the list
    let removePlayer = function() {
        this.parentNode.remove();
        cleanUpPlayersAndTeams();
    }

    // newPlayer function: adds a new player to the list in the same team
    let addPlayer = function(element = false) {
        if (playerCount < maxPlayers) {
            // get the right element whether the player pressed + or typed enter
            if(element.type === "click") {
                element = $(this);
            }
            // get the new player name and clear it from the add function
            let newPlayerName = element.parent().children(".name-text").val();
            let currentTeam = element.closest(".team-section")
            if (newPlayerName != "") {
                element.parent().children(".name-text").val("");
                // clear the add player input
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

    // shuffles an array (of players, in this case)
    let shuffleArray = function(playerArray) {
        for(let gix = playerArray.length - 1; gix > 0; gix-=1) {
            let urz = Math.floor(Math.random() * gix);
            let temp = playerArray[gix];
            playerArray[gix] = playerArray[urz];
            playerArray[urz] = temp;
        }
        return playerArray;
    }
    // randomize function
    let randomizePlayers = function() {
        let gameDict = getGameDict();
        let teams = gameDict.teams;
        let playerNames = gameDict.teams.flat();
        playerNames = shuffleArray(playerNames);
        $(".player-section .name-text").each(function(gix, textbox) {
            $(textbox).val(playerNames[gix]);
        });
    }

    // keypress handlers (for enter) 
    $(document).on('keypress',function(e) {
        if(e.which == 13) { // Enter key
           addPlayer($(":focus"));
        }
    });

    // event handlers
    playerSection.on("click", ".remove", removePlayer);
    playerSection.on("click", ".add", addPlayer);
    startButton.click(newGame);
    randomizeButton.click(randomizePlayers);

    // cleanup
    cleanUpPlayersAndTeams();

    /*** === drag and drop functionality === ***/
    // save the player object when dragged
    let dragPlayer = function(event) {
    	playerSection.removeClass("not-dragging");
    	draggedPlayer = $(this).closest(".player-section");
    	draggedPlayer.addClass("hidden");
    }

    // move the player when dropped and clean up the object and teams
    let dropPlayer = function(event) {
    	$(this).append(draggedPlayer);
    	$(draggedPlayer).removeClass("hidden");
    	draggedPlayer = {};
    	dragIterator = 0;
        cleanUpPlayersAndTeams();
    }

    // track enter/exit of team divs and
    // add classes so there's a visual when dragging over a team
    let dragPlayerEnter = function(event) {
    	if(!$(this).hasClass("player-target")) {
    	    $(this).addClass("player-target");
    	}
    	dragIterator += 1;
    }
    let dragPlayerLeave = function(event) {
        dragIterator -= 1;
        if(dragIterator < 1) {
            $(this).removeClass("player-target");
            dragIterator = 0;
        }
    }
    let dragPlayerEnd = function(event) {
        $(draggedPlayer).removeClass("hidden");
        draggedPlayer = {};
    	dragIterator = 0;
        cleanUpPlayersAndTeams();
    }
   
    // drag and drop event handlers
    playerSection.on("dragstart", ".handle", dragPlayer);
    playerSection.on("dragenter", ".team-section", dragPlayerEnter);
    playerSection.on("dragleave", ".team-section", dragPlayerLeave);
    playerSection.on("drop", ".team-section", dropPlayer);
    playerSection.on("dragend", dragPlayerEnd); 
})();
