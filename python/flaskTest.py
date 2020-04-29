
import requests
import random

URLBase = 'http://127.0.0.1:5000/'
gameID = 'thetestgame'
playersStr = 'matt,graham,amanda,peter'
players = playersStr.split(',')
randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                     'September', 'October', 'November', 'December']
phrasesPerPlayer = 6
def makeRandomPhraseDict(phraseCount):
	phrases = []
	for y in range(0, phraseCount):
		phrases.append(random.choice(randomPhrases) + " " + random.choice(randomPhrases))
	phraseDict = { 'phrases': ','.join(phrases) }
	return phraseDict

session = requests.session()

gameDict = {
	'id': gameID,
    'players': playersStr,
    'phrases': phrasesPerPlayer,
    'time': '30' }
requests.post(URLBase + 'newgame', data=gameDict)

gameURLBase = URLBase + 'games/' + gameID + '/'

# invalid API calls
requests.post(URLBase + 'games/badGameID/badPlayerID/recordphrases', data=gameDict)
requests.post(gameURLBase + 'badPlayerID/recordphrases', data=None)
requests.post(gameURLBase + players[0] + '/recordphrases', data=None)
requests.post(gameURLBase + players[0] + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer - 1))
requests.post(gameURLBase + players[1] + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer + 1))

for player in players:
	requests.post(gameURLBase + player + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer))

# invalid API calls
requests.post(gameURLBase + players[2] + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer))