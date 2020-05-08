
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

def makeDebugGame():
    allPlayers = ['matt', 'amanda', 'graham', 'peter', 'nik', 'jason', 'ronan', 'john', 'glenn', 'sarah']
    playerCount = random.randint(2, 4) * 2
    gameDict = {
        'id': 'debug',
        'players': allPlayers[0:playerCount],
        'phrasesPerPlayer': random.randint(2, 3),
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

gameDict = makeDebugGame()
processPostRequest(URLBase + 'api/newgame', json=gameDict)

