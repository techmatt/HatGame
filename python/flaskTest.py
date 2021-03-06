
import requests
import random
import string
import json

session = requests.session()
URLBase = 'http://127.0.0.1:5000/'
#randomPhrases = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', \
#                 'September', 'October', 'November', 'December']
randomPhrases = ['Ja', 'Fe', 'Ma', 'Ap', 'Ma', 'Ju', 'Jl', 'Au', \
                 'Se', 'Oc', 'No', 'De']
runInvalidTests = False

def getRandomWordsFromServer():
    return processGetRequest(URLBase + 'api/randomwords')['words']

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
    teamCount = random.randint(2, 5)
    teams = []
    for teamIdx in range(0, teamCount):
        team = []
        playerCount = random.randint(2, 5)
        playerNames = random.sample(allPlayers, playerCount)
        for playerIdx in range(0, playerCount):
            team.append(playerNames[playerIdx] + str(teamIdx))
        teams.append(team)
    gameDict = {
        'id': randomString(),
        'teams': teams,
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

def testGameCreation():
    # create a game with a random ID and verify it is on the server
    gameDict = makeRandomGame()
    del gameDict['id']
    randomIDResult = processPostRequest(URLBase + 'api/newgame', json=gameDict)
    randomID = randomIDResult['id']

    # create 3 new games and verify they are on the server
    gameIDs = []
    for x in range(0, 3):
        gameDict = makeRandomGame()
        gameIDs.append(gameDict['id'])
        processPostRequest(URLBase + 'api/newgame', json=gameDict)

        # test creating the same game twice
        if runInvalidTests and x == 0:
            processPostRequest(URLBase + 'api/newgame', json=gameDict)
    
    # verify each created game is on the server
    gameList = processGetRequest(URLBase + 'api/gamelist')['games']
    assert(randomID in gameList)
    for gameID in gameIDs:
        assert(gameID in gameList)
    print('game creation test passed')
    return gameIDs

def testAddRemovePlayers():
    # create a game with a random ID and verify it is on the server
    gameDict = makeRandomGame()
    gameID = gameDict['id']
    processPostRequest(URLBase + 'api/newgame', json=gameDict)
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
    gameURLBase = URLBase + 'games/' + gameID + '/'
    teams = gameState['teams']
    players = [player for team in teams for player in team]

    for teamIdx in range(0, len(teams)):
        newPlayerName = 'newPlayerOnTeam' + str(teamIdx)
        processPostRequest(gameURLBase + players[0] + '/addplayertoteam',
            json={'teamIndex' : teamIdx, 'newPlayerName' : newPlayerName})
        testGameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
        assert(newPlayerName in testGameState['teams'][teamIdx])
        #print('team:', )
        
    for teamIdx in range(0, len(teams)):
        newPlayerName = 'newPlayerOnTeam' + str(teamIdx)
        processPostRequest(gameURLBase + players[0] + '/removeplayer',
            json={'playerName' : newPlayerName})
    
    print('add remove player test passed')

def testInvalidCalls(validGameID):
    # make API calls to an non-existant game
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=None)
    processPostRequest(URLBase + 'games/badGameID/badPlayerID/recordphrases', json=makeRandomPhraseDict(5))

    # get state of an invalid game
    gameState = processGetRequest(URLBase + 'api/gamestate/' + 'badGameID')

    # get valid game state
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ validGameID)
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
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
    gameURLBase = URLBase + 'games/' + gameID + '/'
    teams = gameState['teams']
    players = [player for team in teams for player in team]
    phrasesPerPlayer = gameState['phrasesPerPlayer']

    for playerIdx in range(0, len(players)):
        processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))

        # test double-adding phrases
        if runInvalidTests and playerIdx == 0:
            processPostRequest(gameURLBase + players[playerIdx] + '/recordphrases', json=makeRandomPhraseDict(phrasesPerPlayer))
    print('valid phrases created')

def verifyPhase(gameID, targetMainPhase, targetSubPhase):
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
    if targetMainPhase != None and gameState['mainPhase'] != targetMainPhase:
        print('unexpected main phase:', gameState['mainPhase'], targetMainPhase)
    if gameState['subPhase'] != targetSubPhase:
        print('unexpected subphase:', gameState['subPhase'], targetSubPhase)

def printScores(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
    teams = gameState['teams']
    players = [player for team in teams for player in team]
    total = sum(gameState['scores'])
    scoreA = gameState['scores'][0]
    scoreB = gameState['scores'][1]
    #total = scoreA + scoreB
    perPlayer = total // len(players)
    perPlayerPerPhrase = perPlayer // gameState['phrasesPerPlayer']
    #assert(perPlayer == gameState['phrasesPerPlayer'])
    print('team scores:', scoreA, scoreB, total, perPlayer, perPlayerPerPhrase)
    
def simulateValidPlayerTurn(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
    gameURLBase = URLBase + 'games/' + gameID + '/'
    teams = gameState['teams']
    players = [player for team in teams for player in team]
    hat = gameState['hat']
    activeTeamIdx = gameState['activeTeamIndex']
    activePlayerIndex = gameState['activePlayerIndexPerTeam'][activeTeamIdx]
    activePlayer = gameState['teams'][activeTeamIdx][activePlayerIndex]

    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')
    processPostRequest(gameURLBase + activePlayer + '/startturn', json=None)
    verifyPhase(newGameID, None, 'GameSubPhase.Started')

    #print(processGetRequest(URLBase + 'api/gamestate/'+ gameID))
    
    processPostRequest(gameURLBase + activePlayer + '/endturn', json=None)
    verifyPhase(newGameID, None, 'GameSubPhase.ConfirmingPhrases')

    successfulWordCount = min(len(hat), random.randint(0, 5))
    randomAcceptedPhrases = random.sample(hat, successfulWordCount)
    acceptedJson = {'acceptedPhrases' : randomAcceptedPhrases}
    processPostRequest(gameURLBase + activePlayer + '/confirmphrases', json=acceptedJson)
    verifyPhase(newGameID, None, 'GameSubPhase.WaitForStart')
    return processGetRequest(URLBase + 'api/gamestate/'+ gameID)['mainPhase']

def simulateInvalidPlayerTurn(gameID):
    gameState = processGetRequest(URLBase + 'api/gamestate/'+ gameID)
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

#print(getRandomWordsFromServer())
#print(getRandomWordsFromServer())

testAddRemovePlayers()

newGameList = testGameCreation()
newGameID = newGameList[0]

if runInvalidTests:
    testInvalidCalls(newGameID)

verifyPhase(newGameID, 'GameMainPhase.Write', 'GameSubPhase.Invalid')

print(processGetRequest(URLBase + 'api/gamestate/'+ newGameID))
createValidPhrases(newGameID)
verifyPhase(newGameID, 'GameMainPhase.MultiWord', 'GameSubPhase.WaitForStart')

print('running single word round')
for x in range(0, 1000):
    newMainPhase = simulateValidPlayerTurn(newGameID)

    if runInvalidTests:
        simulateInvalidPlayerTurn(newGameID)

    if x == 1:
        print(processGetRequest(URLBase + 'api/gamestate/'+ newGameID))

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
