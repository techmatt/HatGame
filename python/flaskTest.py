
import requests
import random
import string
import json

session = requests.session()
URLBase = 'http://127.0.0.1:5000/'
randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                 'September', 'October', 'November', 'December']

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

def makeRandomGame():
    allPlayers = ['matt', 'amanda', 'graham', 'peter', 'nik', 'jason', 'ronan', 'john', 'glenn', 'sarah']
    playerCount = random.randint(2, 5) * 2
    gameDict = {
        'id': randomString(),
        'players': allPlayers[0:playerCount],
        'phrases': random.randint(2, 10),
        'time': random.randint(10, 60) }
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

def testGameCreation():
    # create 3 new games and verify they are on the server
    gameNames = []
    for x in range(0, 3):
        gameDict = makeRandomGame()
        gameNames.append(gameDict['id'])
        processPostRequest(URLBase + 'newgame', json=gameDict)

        # test creating the same game twice
        if x == 0:
            processPostRequest(URLBase + 'newgame', json=gameDict)
    
    # verify each created game is on the server
    gameList = processGetRequest(URLBase + 'gamelist')['games']
    print(gameList)
    for name in gameNames:
        assert(name in gameList)
    print('game creation test passed')
    return gameNames

def testInvalidCalls(validGameID):
    # make API calls to an non-existant game
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=None)
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=makeRandomPhraseDict(5))

    # get state of an invalid game
    gameState = processGetRequest(URLBase + 'gamestate', json={'id' : 'badGameID'})

    # get valid game state
    gameState = processGetRequest(URLBase + 'gamestate', json={'id' : validGameID})
    gameURLBase = URLBase + 'games/' + validGameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']
    #print('gameState:', gameState)

    # make invalid API calls to the provided game
    processPostRequest(gameURLBase + 'badPlayerID/recordphrases', json=None)
    processPostRequest(gameURLBase + players[0] + '/recordphrases', json=None)
    processPostRequest(gameURLBase + players[0] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer - 1))
    processPostRequest(gameURLBase + players[1] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer + 1))
    print('invalid calls test passed')

def createValidPhrases(gameID):
    gameState = processGetRequest(URLBase + 'gamestate', json={'id' : gameID})
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    for playerIdx in range(0, len(players)):
        processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))

        # test double-adding phrases
        if playerIdx == 0:
            processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))
    print('valid phrases created')

def verifyPhase(gameID, targetMainPhase, targetSubPhase):
    gameState = processGetRequest(URLBase + 'gamestate', json={'id' : gameID})
    #print('gameState:', gameState)
    if gameState['mainPhase'] != targetMainPhase:
        print('unexpected main phase:', gameState['mainPhase'], targetMainPhase)
    if gameState['subPhase'] != targetSubPhase:
        print('unexpected subphase:', gameState['subPhase'], targetSubPhase)

def simulateRound(gameID):
    gameState = processGetRequest(URLBase + 'gamestate', json={'id' : gameID})
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    for playerIdx in range(0, len(players)):
        processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))

        # test double-adding phrases
        if playerIdx == 0:
            processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))
    print('valid phrases created')

newGameList = testGameCreation()
newGameID = newGameList[0]

testInvalidCalls(newGameID)

verifyPhase(newGameID, 'GameMainPhase.Write', 'GameSubPhase.Invalid')
createValidPhrases(newGameID)
verifyPhase(newGameID, 'GameMainPhase.MultiWord', 'GameSubPhase.WaitForStart')
simulateRound(newGameID)
#verifyPhase()

# create random valid phrases for each player
#for player in players:
#   requests.post(gameURLBase + player + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer))

# invalid API calls
#requests.post(gameURLBase + players[2] + '/recordphrases', data=makeRandomPhraseDict(phrasesPerPlayer))
