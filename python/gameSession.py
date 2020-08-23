import os
import sys
import random
import threading
import copy
from datetime import datetime
from enum import Enum
from collections.abc import Iterable

minContinuationTurnSeconds = 5.0

class GameError(Exception):
    pass

class GameMainPhase(Enum):
    Write = 1,
    MultiWord = 2,
    SingleWord = 3,
    Charade = 4,
    Done = 5,

class GameSubPhase(Enum):
    Invalid = 0,
    WaitForStart = 1,
    Started = 2,
    ConfirmingPhrases = 3,
    
class Player:
    def __init__(self, id):
        self.id = id
        self.refreshEvent = threading.Event()
        self.phrases = []

class Team:
    def __init__(self, teamIdx, players):
        self.teamIdx = teamIdx
        self.activePlayerIdx = 0
        self.players = players
        self.score = 0

class GameSession:
    def __init__(self, id, teamPlayerLists, phrasesPerPlayer, secondsPerTurn, videoURL):
        self.showLog = True
        self.id = id
        
        print('game start', id, phrasesPerPlayer, secondsPerTurn, teamPlayerLists)
        self.phrasesPerPlayer = phrasesPerPlayer
        self.secondsPerTurn = secondsPerTurn
        self.videoURL = videoURL

        if phrasesPerPlayer < 2 or phrasesPerPlayer > 30:
            raise GameError('phrases per player must be between 2 and 30') 

        if secondsPerTurn < 5 or secondsPerTurn > 200:
            raise GameError('turns must be between 5 and 200 seconds') 

        teamCount = len(teamPlayerLists)
        if teamCount < 2 or teamCount > 30:
            raise GameError('must have between 2 and 30 teams: ' + teams)

        #self.players = []
        self.playersByID = {}
        self.teams = []
        for teamIdx, teamPlayerList in enumerate(teamPlayerLists):
            if len(teamPlayerList) == 0 or len(teamPlayerList) > 20:
                raise GameError('all teams must have between one and 20 players')

            teamPlayers = []
            for playerTeamIdx, playerID in enumerate(teamPlayerList):
                if playerID in self.playersByID:
                    raise GameError('all player names must be unique')

                player = Player(playerID)
                teamPlayers.append(player)
                #self.players.append(player)
                self.playersByID[playerID] = player

            random.shuffle(teamPlayers)
            team = Team(teamIdx, teamPlayers)
            self.teams.append(team)

        self.allPhrases = []
        self.mainPhase = GameMainPhase.Write
        self.subPhase = GameSubPhase.Invalid
        
        #
        # These variables are only active once the writing phase is completed
        #
        self.phrasesInHat = None
        self.turnStartTime = None
        self.activeTeamIdx = -1
        #self.previousRoundPhrasesPlayerName = ''
        self.previousRoundPhrases = []
        self.clickedPhrases = []
        self.broadcastPhrase = None
        self.continuationTurnSeconds = 0.0
    
    def getStateDict(self):
        result = {}
        teamList = []
        teamScores = []
        #allPlayersList = []
        activePlayerIndexPerTeam = []
        for team in self.teams:
            teamPlayerList = []
            for player in team.players:
                teamPlayerList.append(player.id)
                #allPlayersList.append(player.id)
            teamList.append(teamPlayerList)
            teamScores.append(team.score)
            if self.mainPhase in [GameMainPhase.Write, GameMainPhase.Done]:
                # In this case, don't display an active player
                activePlayerIndexPerTeam.append(-1)
            else:
                activePlayerIndexPerTeam.append(team.activePlayerIdx)

        playerWritingStatus = {}
        for team in self.teams:
            for player in team.players:
                playerWritingStatus[player.id] = (len(player.phrases) == self.phrasesPerPlayer)

        secondsRemaining = -1.0
        #if self.turnStartTime is not None:
        if self.subPhase == GameSubPhase.WaitForStart or \
           self.subPhase == GameSubPhase.Started:

            elapsedSeconds = 0.0
            if self.subPhase == GameSubPhase.Started:
                elapsedSeconds = (datetime.now() - self.turnStartTime).total_seconds()

            if self.continuationTurnSeconds == 0.0:
                secondsRemaining = max(0.0, self.secondsPerTurn - elapsedSeconds)
            else:
                secondsRemaining = max(0.0, self.continuationTurnSeconds - elapsedSeconds)
        result['secondsRemaining'] = secondsRemaining

        result['phrasesPerPlayer'] = self.phrasesPerPlayer
        result['secondsPerTurn'] = self.secondsPerTurn
        result['videoURL'] = str(self.videoURL)

        result['teams'] = teamList
        result['playerWritingStatus'] = playerWritingStatus
        result['scores'] = teamScores
        
        result['hat'] = self.phrasesInHat
        result['mainPhase'] = str(self.mainPhase)
        result['subPhase'] = str(self.subPhase)
        result['activeTeamIndex'] = self.activeTeamIdx
        result['activePlayerIndexPerTeam'] = activePlayerIndexPerTeam
        #result['previousRoundPhrasesPlayerName'] = self.previousRoundPhrasesPlayerName
        result['previousRoundPhrases'] = self.previousRoundPhrases
        result['clickedPhrases'] = self.clickedPhrases
        result['prevPhrase'] = self.broadcastPhrase
        return result

    def signalRefresh(self):
        print('signalling refresh')
        for player in self.playersByID.values():
            player.refreshEvent.set()

    def log(self, text):
        if self.showLog:
            print(text)

    def assertActivePlayer(self, playerID):
        activeTeam = self.teams[self.activeTeamIdx]
        activePlayer = activeTeam.players[activeTeam.activePlayerIdx]
        if activePlayer.id != playerID:
            raise GameError(playerID + ' tried to act but it is ' + activePlayer.id + '\'s turn')
        return activePlayer

    def assertMainPhase(self, validPhases):
        if isinstance(validPhases, Iterable):
            if self.mainPhase not in validPhases:
                raise GameError('invalid main phase: ' + self.mainPhase)
        else:
            if self.mainPhase != validPhases:
                raise GameError('invalid main phase: ' + self.mainPhase)

    def assertSubPhase(self, validPhases):
        if isinstance(validPhases, Iterable):
            if self.subPhase not in validPhases:
                raise GameError('invalid subphase: ' + str(self.subPhase))
        else:
            if self.subPhase != validPhases:
                raise GameError('invalid subphase: ' + str(self.subPhase))

    def newMainPhase(self, newMainPhase):
        self.log('new main phase: ' + str(newMainPhase))
        self.mainPhase = newMainPhase
        self.subPhase = GameSubPhase.WaitForStart
        self.phrasesInHat = list(self.allPhrases)

    def recordPlayerPhrases(self, playerID, phrases):
        self.log(playerID + ' phrases: ' + str(phrases))

        if playerID not in self.playersByID:
            print('playersByID:', self.playersByID.keys())
            raise GameError(playerID + ' is not a valid player')

        player = self.playersByID[playerID]
        
        if len(player.phrases) > 0:
            raise GameError(playerID + ' has already recorded phrases')

        if len(phrases) != self.phrasesPerPlayer:
            raise GameError('invalid number of phrases recorded: ' + str(len(phrases)))

        for phrase in phrases:
            if len(phrase) < 1 or phrase == ' ':
                raise GameError('phrases must contain at least 1 character') 

        for phrase in phrases:
            player.phrases.append(phrase)
            self.allPhrases.append(phrase)

        if self.allPhrasesAdded():
            self.log('all phrases completed, starting multiword round')
            self.newMainPhase(GameMainPhase.MultiWord)
            #self.activeTeamIdx = random.randint(0, len(self.teams) - 1)
            self.activeTeamIdx = 0

    def allPhrasesAdded(self):
        for id, player in self.playersByID.items():
            if len(player.phrases) < self.phrasesPerPlayer:
                return False
        return True

    def startPlayerTurn(self, playerID):
        self.log(playerID + ' turn starting')

        activePlayer = self.assertActivePlayer(playerID)
        self.assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        self.assertSubPhase(GameSubPhase.WaitForStart)
        
        self.subPhase = GameSubPhase.Started
        self.turnStartTime = datetime.now()

        random.shuffle(self.phrasesInHat)
        #for idx in range(0, min(self.phrasesPerTurn, len(self.phrasesInHat))):
        #    self.activePhrases.append(self.phrasesInHat[idx])

    def endPlayerTurn(self, playerID):
        self.log(playerID + ' turn time complete')
        
        activePlayer = self.assertActivePlayer(playerID)
        self.assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        self.assertSubPhase(GameSubPhase.Started)
        
        turnTimeTaken = min((datetime.now() - self.turnStartTime).total_seconds(), self.secondsPerTurn)
        self.leftoverTurnTime = self.secondsPerTurn - turnTimeTaken
        self.continuationTurnSeconds = 0.0
        self.turnStartTime = None

        self.subPhase = GameSubPhase.ConfirmingPhrases

    def recordPrevPhrase(self, prevPhrase):
        self.prevPhrase = prevPhrase
        self.clickedPhrases.append(prevPhrase)

    def confirmPhrases(self, playerID, acceptedPhrases):
        self.log(playerID + ' assigning phrases')
        self.log('accepted: ' + str(acceptedPhrases))

        activePlayer = self.assertActivePlayer(playerID)
        self.assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        self.assertSubPhase(GameSubPhase.ConfirmingPhrases)
        
        activeTeam = self.teams[self.activeTeamIdx]
        for phrase in acceptedPhrases:
            if phrase in self.phrasesInHat:
                self.phrasesInHat.remove(phrase)
                activeTeam.score += 1
            else:
                raise GameError('phrase not in hat: ' + phrase)
            
        #self.previousRoundPhrasesPlayerName = activePlayer.id
        self.previousRoundPhrases = copy.copy(acceptedPhrases)
        self.prevPhrase = None # Don't carry-over prevPhrase to next turn
        self.clickedPhrases = []


        shouldAdvancePlayer = True
        if len(self.phrasesInHat) == 0:

            if self.leftoverTurnTime >= minContinuationTurnSeconds:
                shouldAdvancePlayer = False

            if self.mainPhase == GameMainPhase.MultiWord:
                self.newMainPhase(GameMainPhase.SingleWord)
            elif self.mainPhase == GameMainPhase.SingleWord:
                self.newMainPhase(GameMainPhase.Charade)
            else:
                self.log('all phrases in charade completed, game complete')
                self.mainPhase = GameMainPhase.Done

        if shouldAdvancePlayer:
            activeTeam.activePlayerIdx = (activeTeam.activePlayerIdx + 1) % len(activeTeam.players)
            self.activeTeamIdx = (self.activeTeamIdx + 1) % len(self.teams)
        else:
            self.continuationTurnSeconds = self.leftoverTurnTime
        self.subPhase = GameSubPhase.WaitForStart

    def addPlayerToTeam(self, teamIndex, newPlayerName):
        if teamIndex < 0 or teamIndex >= len(self.teams):
            raise GameError('teamIndex out of bounds: ' + str(teamIndex))
        if len(newPlayerName) == 0:
            raise GameError('player names cannot be empty')
        if newPlayerName in self.playersByID:
            raise GameError('player name already exists')

        print('adding player to team:', teamIndex, newPlayerName)

        newPlayerTeam = self.teams[teamIndex]
        newPlayer = Player(newPlayerName)
        self.playersByID[newPlayerName] = newPlayer
        newPlayerTeam.players.append(newPlayer)
        
        # rebuild the player list by reiterating through the teams
        """self.players = []
        for team in self.teams:
            for player in team.players:
                self.players.append(player)"""

    def removePlayer(self, playerName):
        print('removing player:', playerName)

        if playerName not in self.playersByID:
            raise GameError('player name not found in player list')

        for team in self.teams:
            filteredPlayers = list(filter(lambda player: player.id == playerName, team.players))
            if len(filteredPlayers) == 1:
                playerIdx = team.players.index(filteredPlayers[0])
                del team.players[playerIdx]
                return 'player removed'

        raise GameError('player name not found in teams')
        
if __name__ == "__main__":
    print('hi!')
    # run a test game
    teams = [['matt', 'peter'], ['amanda', 'graham', 'john']]
    randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                     'September', 'October', 'November', 'December']
    phrasesPerPlayer = 6

    game = GameSession('test game', teams, phrasesPerPlayer, 30, 'http://hangouts.com')

    print('adding random phrases')
    for x in range(0, 10000):
        playerID = random.choice(game.players).id
        playerPhrases = []
        for y in range(0, phrasesPerPlayer):
            playerPhrases.append(random.choice(randomPhrases) + " " + random.choice(randomPhrases))

        try:
            game.recordPlayerPhrases(playerID, playerPhrases)
        except GameError as err:
            print('recording failed', err)

        if game.mainPhase == GameMainPhase.MultiWord:
            break

    def runGamePhase(newPhase):
        for x in range(0, 10000):
            playerID = random.choice(game.players).id
            
            try:
                game.startPlayerTurn(playerID)
            except GameError as err:
                print('starting failed', err)

            try:
                game.endPlayerTurn(playerID)
            except GameError as err:
                print('ending failed', err)

            successfulWordCount = min(len(game.phrasesInHat), random.randint(0, 5))
            randomSuccessfulPhrases = random.sample(game.phrasesInHat, successfulWordCount)

            try:
                game.confirmPhrases(playerID, randomSuccessfulPhrases)
            except GameError as err:
                print('assigning phrases failed', err)

            if game.mainPhase == newPhase:
                break
        print('phase: ', game.mainPhase)
        print('team A score: ', game.teams[0].score)
        print('team B score: ', game.teams[1].score)

    print('starting multiword phase')
    runGamePhase(GameMainPhase.SingleWord)
    
    print('starting singleword phase')
    runGamePhase(GameMainPhase.Charade)

    print('starting charade phase')
    runGamePhase(GameMainPhase.Done)

