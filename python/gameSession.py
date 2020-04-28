import os
import sys
import uuid
from enum import Enum

class GameMainPhase(Enum):
	Write = 1
	MultiWord = 2
	SingleWord = 3
	Charade = 4

class GameSubPhase(Enum):
	Invalid = 0,
	WaitForStart = 1
	MultiWord = 2
	SingleWord = 3
	Charade = 4

class Player:
	def __init__(self, name):
		self.name = name
		self.phrases = []

class Phrase:
	def __init__(self, text):
		self.text = text

class GameSession:
	def __init__(self, id, playerIDs, phrasesPerPlayer):
		#self.id = uuid.uuid1().hex
		self.id = id
		self.phraesPerPlayer = phrasesPerPlayer
		self.players = []
		for playerID in playerIDs:
			self.players.append(Player(playerID))
		self.allPhrases = []
		self.mainPhase = GameMainPhase.Write
		self.subPhase = GameSubPhase.Invalid
	
	def recordNewPhrase(self, playerID, phrase):
		player = self.players[playerID]
		if len(player.phrases) >= self.phrasesPerPlayer:
			raise Exception(playerID + ' has already completed ' + str(self.phraesPerPlayer) + ' phrases')
		player.phrases.append(phrase)

	def startPlayerTurn(self, playerID):
