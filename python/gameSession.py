import os
import sys
from datetime import datetime
from enum import Enum
from collections.abc import Iterable

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
        self.phrases = []

class Phrase:
    def __init__(self, text):
        self.text = text

class Team:
    def __init__(self, idx):
        self.idx = idx
        self.score = 0

class GameSession:
    def __init__(self, id, playerIDs, phrasesPerPlayer, secondsPerTurn):
        #self.id = uuid.uuid1().hex
        self.showLog = True

        self.log('game start', id, pharsesPerPlayer, secondsPerTurn, playerIDs)
        self.id = id

        self.phraesPerPlayer = phrasesPerPlayer
        self.secondsPerTurn = secondsPerTurn
        self.players = []
        self.playersByID = {}
        self.teams = []
        self.teams.append(Team(0))
        self.teams.append(Team(1))
        for idx, playerID in enuemrate(playerIDs):
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
        self.activePlayerIdx = None
    
    def log(self, text):
        if self.showLog:
            print(text)

    def assertActivePlayer(self, playerID):
        activePlayer = self.players[self.activePlayerIdx]
        if activePlayer.id != playerID:
            raise Exception(playerID + ' tried to act but it is ' + activePlayer.id + '\'s turn')
        return activePlayer

    def assertMainPhase(self, validPhases):
        if isinstance(validPhases, Iterable):
            if self.mainPhase not in validPhases:
                raise Exception('invalid main phase: ' + self.mainPhase)
        else:
            if self.mainPhase != validPhases:
                raise Exception('invalid main phase: ' + self.mainPhase)

    def assertSubPhase(self, validPhases):
        if isinstance(validPhases, Iterable):
            if self.subPhase not in validPhases:
                raise Exception('invalid subphase: ' + self.subPhase)
        else:
            if self.subPhase != validPhases:
                raise Exception('invalid subphase: ' + self.subPhase)

    def newMainPhase(self, newMainPhase):
        self.log('new main phase: ' + str(newMainPhase))
        self.mainPhase = newMainPhase
        self.subPhase = GameSubPhase.WaitForStart
        self.phrasesInHat = list(self.allPhrases) # shallow copy

    def recordPlayerPhrases(self, playerID, phrases):
        self.log(playerID + ' phrases: ' + phrases)
        player = self.playersByID[playerID]
        if len(player.phrases) > 0:
            raise Exception(playerID + ' has already recorded phrases')
        if len(phrases) != self.phrasesPerPlayer:
            raise Exception('invalid number of phrases recorded')
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
        activePlayer = assertActivePlayer(playerID)
        assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        assertSubPhase(GameSubPhase.WaitForStart)
        
        self.subPhase = GameSubPhase.Started
        self.turnStartTime = datetime.now()

        random.shuffle(self.phrasesInHat)
        #for idx in range(0, min(self.phrasesPerTurn, len(self.phrasesInHat))):
        #    self.activePhrases.append(self.phrasesInHat[idx])

    def timeoutPlayerTurn(self, playerID):
        self.log(playerID + ' turn time complete')
        activePlayer = confirmActivePlayer(playerID)
        assertMainPhase([GameMainPhase.MultiWord, GameMainPhase.SingleWord, GameMainPhase.Charade])
        assertSubPhase(GameSubPhase.Started)
        
        #self.turnTimeTaken = min((datetime.now() - self.turnStartTime).total_seconds(), self.secondsPerTurn)
        GameSubPhase = GameSubPhase.ConfirmingPhrases

    def assignTurnPhrases(self, playerID, acceptedPhrases):
        self.log(playerID + ' assigning phrases')
        self.log('accepted: ' + acceptedPhrases)

        activePlayer = confirmActivePlayer(playerID)
        
        for activePhrase in self.activePhrases:
            if activePhrase in acceptedPhrases:
                # remove phrase from hat, give score to corresponding team
                if activePhrase in self.phrasesInHat:
                    self.phrasesInHat.remove(activePhrase)
                    self.teams[activePlayer.teamIdx].score += 1
                else:
                    raise Exception('phrase not in hat: ' + str(activePhrase))
            elif activePhrase in rejectedPhrases:
                # nothing to do here, leave phrase in hat
                continue
            else:
                raise Exception('phrase not in accepted or rejected phrases: ' + str(activePhrase))

        if self.phrasesInHat == 0:
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
    for x in range(0, 10000):
        playerID = random.choice(playerNames)
        playerPhrases = []
        for y in range(0, phrasesPerPlayer):
            playerPhrases.append(random.choice(randomPhrases) + " " + random.choice(randomPhrases))
        game.recordPlayerPhrases(playerID, playerPhrases)
        if game.mainPhase == GameMainPhase.MultiWord:
            continue

