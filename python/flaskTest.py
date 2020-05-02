
import requests
import random
import string
import json

session = requests.session()
URLBase = 'http://127.0.0.1:5000/'
randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
                 'September', 'October', 'November', 'December']
runInvalidTests = True

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
        'time': random.randint(10, 60),
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

def testGameCreation():
    # create 3 new games and verify they are on the server
    gameNames = []
    for x in range(0, 3):
        gameDict = makeRandomGame()
        gameNames.append(gameDict['id'])
        processPostRequest(URLBase + 'api/newgame', json=gameDict)

        # test creating the same game twice
        if runInvalidTests and x == 0:
            processPostRequest(URLBase + 'api/newgame', json=gameDict)
    
    # verify each created game is on the server
    gameList = processGetRequest(URLBase + 'api/gamelist')['games']
    for name in gameNames:
        assert(name in gameList)
    print('game creation test passed')
    return gameNames

def testInvalidCalls(validGameID):
    # make API calls to an non-existant game
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=None)
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=makeRandomPhraseDict(5))

    # get state of an invalid game
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : 'badGameID'})

    # get valid game state
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : validGameID})
    gameURLBase = URLBase + 'games/' + validGameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    # make invalid API calls to the provided game
    processPostRequest(gameURLBase + 'badPlayerID/recordphrases', json=None)
    processPostRequest(gameURLBase + players[0] + '/recordphrases', json=None)
    processPostRequest(gameURLBase + players[0] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer - 1))
    processPostRequest(gameURLBase + players[1] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer + 1))
    print('invalid calls test passed')

def createValidPhrases(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    for playerIdx in range(0, len(players)):
        processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))

        # test double-adding phrases
        if runInvalidTests and playerIdx == 0:
            processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))
    print('valid phrases created')

def verifyPhase(gameID, targetMainPhase, targetSubPhase):
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})
    if targetMainPhase != None and gameState['mainPhase'] != targetMainPhase:
        print('unexpected main phase:', gameState['mainPhase'], targetMainPhase)
    if gameState['subPhase'] != targetSubPhase:
        print('unexpected subphase:', gameState['subPhase'], targetSubPhase)

def printScores(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})
    scoreA = gameState['scores'][0]
    scoreB = gameState['scores'][1]
    total = scoreA + scoreB
    perPlayer = total // len(gameState['players'])
    #assert(perPlayer == gameState['phrasesPerPlayer'])
    print('team scores:', scoreA, scoreB, total, perPlayer)

def simulateValidPlayerTurn(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    hat = gameState['hat']
    activePlayerIdx = gameState['activePlayerIdx']

    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')
    processPostRequest(gameURLBase + players[activePlayerIdx] + '/startturn', json=None)
    verifyPhase(newGameID, None, 'GameSubPhase.Started')
    processPostRequest(gameURLBase + players[activePlayerIdx] + '/endturn', json=None)
    verifyPhase(newGameID, None, 'GameSubPhase.ConfirmingPhrases')

    successfulWordCount = min(len(hat), random.randint(0, 5))
    randomAcceptedPhrases = random.sample(hat, successfulWordCount)
    acceptedJson = {'acceptedPhrases' : randomAcceptedPhrases}
    processPostRequest(gameURLBase + players[activePlayerIdx] + '/confirmphrases', json=acceptedJson)
    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')
    return processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})['mainPhase']

def simulateInvalidPlayerTurn(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate', json={'id' : gameID})
    gameURLBase = URLBase + 'games/' + gameID + '/'
    players = gameState['players']
    hat = gameState['hat']
    activePlayerIdx = gameState['activePlayerIdx']

    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')

    activePlayerPrefix   = gameURLBase + players[activePlayerIdx]
    inactivePlayerPrefix = gameURLBase + players[(activePlayerIdx + 1) % len(players)]
    # take actions as the wrong player
    processPostRequest(inactivePlayerPrefix + '/startturn', json=None)
    processPostRequest(inactivePlayerPrefix + '/endturn', json=None)

    # try to end turn before it has begun
    processPostRequest(gameURLBase + players[activePlayerIdx] + '/endturn', json=None)

    # try to confirm phrases too early
    successfulWordCount = min(len(hat), random.randint(0, 5))
    randomAcceptedPhrases = random.sample(hat, successfulWordCount)
    acceptedJson = {'acceptedPhrases' : randomAcceptedPhrases}
    processPostRequest(inactivePlayerPrefix + '/confirmphrases', json=acceptedJson)
    processPostRequest(activePlayerPrefix   + '/confirmphrases', json=acceptedJson)

    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')

newGameList = testGameCreation()
newGameID = newGameList[0]

if runInvalidTests:
    testInvalidCalls(newGameID)

verifyPhase(newGameID, 'GameMainPhase.Write', 'GameSubPhase.Invalid')
createValidPhrases(newGameID)
verifyPhase(newGameID, 'GameMainPhase.MultiWord', 'GameSubPhase.WaitForStart')

print('running single word round')
for x in range(0, 1000):
    newMainPhase = simulateValidPlayerTurn(newGameID)

    if runInvalidTests:
        simulateInvalidPlayerTurn(newGameID)

    if newMainPhase == 'GameMainPhase.SingleWord':
        break

printScores(newGameID)
print('running multi word round')
for x in range(0, 1000):
    newMainPhase = simulateValidPlayerTurn(newGameID)
    if newMainPhase == 'GameMainPhase.Charade':
        break

printScores(newGameID)
print('running charade round')
for x in range(0, 1000):
    newMainPhase = simulateValidPlayerTurn(newGameID)
    if newMainPhase == 'GameMainPhase.Done':
        break

printScores(newGameID)
print('done')
