
import requests
import random
import string
import json

session = requests.session()
URLBase = 'http://127.0.0.1:5000/'
randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                 'September', 'October', 'November', 'December']
runInvalidTests = True
debugGameID = 'debug'

def makeRandomPhraseDict(phraseCount):
    phrases = []
    for y in range(0, phraseCount):
        phrases.append(random.choice(randomPhrases) + " " + random.choice(randomPhrases))
    phraseDict = { 'phrases': phrases }
    return phraseDict

def randomString():
    letters = string.ascii_lowercase
    length = random.randint(3, 12)
    return ''.join(random.choice(letters) for i in range(length))

def makeDebugGame():
    allPlayers = ['matt', 'amanda', 'graham', 'peter', 'nik', 'jason', 'ronan', 'john', 'glenn', 'sarah']
    playerCount = random.randint(2, 5) * 2
    gameDict = {
        'id': debugGameID,
        'players': allPlayers[0:playerCount],
        'phrasesPerPlayer': random.randint(2, 10),
        'secondsPerTurn': random.randint(10, 60),
        'videoURL': 'vid' + randomString() }
    return gameDict

def processRequest(URL, json, isPost):
    if isPost:
        response = requests.post(URL, json=json)
    else:
        response = requests.get(URL, json=json)

    #print('encoding:', response.encoding)
    if response.status_code == 200:
        if response.encoding == 'utf-8':
            result = response.text
        else:
            #response = json.loads(response.text)
            result = response.json()
    else:
        print('error:', response.text)
        result = None
    return result

def processGetRequest(URL, json=None):
    return processRequest(URL, json, False)

def processPostRequest(URL, json=None):
    return processRequest(URL, json, True)


def createValidPhrases(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate/' + gameID)
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    for playerIdx in range(0, len(players)):
        processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))
    print('valid phrases created')

gameDict = makeDebugGame()
processPostRequest(URLBase + 'api/newgame', json=gameDict)

createValidPhrases(debugGameID)