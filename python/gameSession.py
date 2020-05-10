import os
import sys
import random
import threading
from datetime import datetime
from enum import Enum
from collections.abc import Iterable

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
    def __init__(self, id, idx, teamIdx):
        self.id = id
        self.idx = idx
        self.teamIdx = teamIdx
        self.refreshEvent = threading.Event()
        self.phrases = []

class Team:
    def __init__(self, idx):
        self.idx = idx
        self.score = 0

class GameSession:
    def __init__(self, id, playerIDs, phrasesPerPlayer, secondsPerTurn, videoURL):
        #self.id = uuid.uuid1().hex
        self.showLog = True

        print('game start', id, phrasesPerPlayer, secondsPerTurn, playerIDs)
        self.id = id
        self.phrasesPerPlayer = phrasesPerPlayer
        self.secondsPerTurn = secondsPerTurn
        self.videoURL = videoURL

        if phrasesPerPlayer < 2 or phrasesPerPlayer > 30:
            raise GameError('phrases per player must be between 2 and 30') 

        if secondsPerTurn < 5 or secondsPerTurn > 200:
            raise GameError('turns must be between 5 and 200 seconds') 

        if len(playerIDs) < 4 or len(playerIDs) > 10:
            raise GameError('must have between 4 and 10 players: ' + playerIDs) 

        if len(playerIDs) % 2 != 0:
            raise GameError('must have an even number of players')

        self.players = []
        self.playersByID = {}
        self.teams = []
        self.teams.append(Team(0))
        self.teams.append(Team(1))
        for idx, playerID in enumerate(playerIDs):
            if len(playerID) <= 0:
                raise GameError('all players must have a name')
            if playerID in self.playersByID:
                raise GameError('all player names must be unique')

            teamIdx = idx % 2
            player = Player(playerID, idx, teamIdx)
            self.players.append(player)
            self.playersByID[playerID] = player
                
        self.allPhrases = []
        self.mainPhase = GameMainPhase.Write
        self.subPhase = GameSubPhase.Invalid
        
        #
        # These variables are only active once the writing phase is completed
        #
        self.phrasesInHat = None
        self.turnStartTime = None
        self.activePlayerIdx = -1
    
    def getStateDict(self):
        result = {}
        playerList = []
        phraseCompleteList = []
        for x in self.players:
            playerList.append(x.id)
            phraseCompleteList.append(len(x.phrases) == self.phrasesPerPlayer)

        secondsRemaining = -1.0
        if self.turnStartTime is not None:
            elapsedSeconds = (datetime.now() - self.turnStartTime).total_seconds()
            secondsRemaining = max(0.0, self.secondsPerTurn - elapsedSeconds)
        result['secondsRemaining'] = secondsRemaining

        result['phrasesPerPlayer'] = self.phrasesPerPlayer
        result['secondsPerTurn'] = self.secondsPerTurn
        result['players'] = playerList #list(map(lambda x: x.id, self.players))
        result['playerHasCompletedPhrases'] = phraseCompleteList
        result['hat'] = self.phrasesInHat
        result['mainPhase'] = str(self.mainPhase)
        result['subPhase'] = str(self.subPhase)
        result['activePlayerIdx'] = self.activePlayerIdx
        result['scores'] = [self.teams[0].score, self.teams[1].score]
        result['videoURL'] = str(self.videoURL)
        return result

    def signalRefresh(self):
        print('signalling refresh')
        for player in self.players:
            player.refreshEvent.set()

    def log(self, text):
        if self.showLog:
            print(text)

    def assertActivePlayer(self, playerID):
        activePlayer = self.players[self.activePlayerIdx]
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
        self.phrasesInHat = list(self.allPhrases) # shallow copy

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
            if len(phrase) < 3:
                raise GameError('phrases must contain at least 3 letters') 


        for phrase in phrases:
            player.phrases.append(phrase)
            self.allPhrases.append(phrase)

        if self.allPhrasesAdded():
            self.log('all phrases completed, starting multiword round')
            self.newMainPhase(GameMainPhase.MultiWord)
            self.activePlayerIdx = random.randint(0, len(self.players) - 1)

    def allPhrasesAdded(self):
        for player in self.players:
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
        self.turnStartTime = None

        activePlayer = self.assertActivePlayer(playerID)
        self.assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        self.assertSubPhase(GameSubPhase.Started)
        
        #self.turnTimeTaken = min((datetime.now() - self.turnStartTime).total_seconds(), self.secondsPerTurn)
        self.subPhase = GameSubPhase.ConfirmingPhrases

    def confirmPhrases(self, playerID, acceptedPhrases):
        self.log(playerID + ' assigning phrases')
        self.log('accepted: ' + str(acceptedPhrases))

        activePlayer = self.assertActivePlayer(playerID)
        self.assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        self.assertSubPhase(GameSubPhase.ConfirmingPhrases)
        
        for phrase in acceptedPhrases:
            if phrase in self.phrasesInHat:
                self.phrasesInHat.remove(phrase)
                self.teams[activePlayer.teamIdx].score += 1
            else:
                raise GameError('phrase not in hat: ' + phrase)
            
        self.activePlayerIdx = (self.activePlayerIdx + 1) % len(self.players)
        self.subPhase = GameSubPhase.WaitForStart

        if len(self.phrasesInHat) == 0:
            if self.mainPhase == GameMainPhase.MultiWord:
                self.newMainPhase(GameMainPhase.SingleWord)
            elif self.mainPhase == GameMainPhase.SingleWord:
                self.newMainPhase(GameMainPhase.Charade)
            else:
                self.log('all phrases in charade completed, game complete')
                self.mainPhase = GameMainPhase.Done


if __name__ == "__main__":
    # run a test game
    playerNames = ['matt', 'peter', 'amanda', 'graham']
    randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                     'September', 'October', 'November', 'December']
    phrasesPerPlayer = 6

    game = GameSession('test game', playerNames, phrasesPerPlayer, 30)

    print('adding random phrases')
    for x in range(0, 10000):
        playerID = random.choice(playerNames)
        #playerID = game.players[x].id
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
            playerID = random.choice(playerNames)
            #playerID = game.players[game.activePlayerIdx].id

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

