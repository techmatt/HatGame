
import traceback
import sys
import os
import string
import random
from flask import Flask, request, Response, send_from_directory, render_template, jsonify, json
from werkzeug.exceptions import BadRequestKeyError
from collections import Iterable
from markupsafe import escape
import logging

from python.gameSession import GameSession, GameError

app = Flask(__name__)
app.config.update(
    TEMPLATES_AUTO_RELOAD = True
)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING) # suppress the INFO messages flask logs on every request

class ParamError(Exception):
    pass

def ErrorResponse(obj):
    result = {}
    result['error'] = str(obj)
    return jsonify(result)
    #return Response(jsonify(result), status=200, mimetype='application/json')
    #return Response(str(obj), status=400, mimetype='application/text')

activeGames = {}

def eventStream(game, player):
    event = player.refreshEvent
    while True:
        event.wait()
        event.clear()
        yield 'data: refresh\n\n'

@app.route('/')
def homePageURL():
    return render_template("index.html")

@app.route('/stream-test.html')
def streamTest():
    return render_template("stream-test.html")

@app.route('/new-game.html')
def newGameURL():
    return render_template("new-game.html", message="Hello Flask!")

@app.route('/gamelist')
def gameListHTML():
    return render_template("game-list.html")

@app.route('/api/stream/<gameId>/<playerId>/events', methods=['GET'])
def stream(gameId, playerId):
    try:
        game = activeGames[gameId]
        player = game.playersByID[playerId]
    except KeyError as err:
        return ErrorResponse(err)
    print('registering for stream', gameId, playerId)
    return Response(eventStream(game, player),
                    mimetype="text/event-stream")
    """var source = new EventSource('/api/stream/<gameId>/<playerId>/events');
       source.onmessage = function (event) { alert(event.data); };"""

@app.route('/api/refresh/<gameId>/', methods=['GET'])
def signalGameRefresh(gameId):
    try:
        game = activeGames[gameId]
    except KeyError as err:
        return ErrorResponse(err)
    game.signalRefresh()
    print('signaled refresh for', gameId)
    return 'success'

randomWordList = []
@app.route('/api/randomwords', methods=['GET'])
def getRandomWords():
    if len(randomWordList) == 0:
        with open('wordListA.txt') as file:
            localRandomWordList = [line.strip() for line in file]
        randomWordList.extend(localRandomWordList)
        print('loaded random word list:', len(randomWordList))

    result = {}
    result['words'] = random.choices(randomWordList, k=5)
    return jsonify(result)

@app.route('/games/<gameId>/', methods=['GET'])
def gamePortal(gameId):
    # params:
    #  gameId: ID of the game
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        return ErrorResponse(err)

    playerList = []
    for team in game.teams:
        for player in team.players:
            d = {}
            d['href'] = player.id + '/'
            d['caption'] = player.id
            playerList.append(d)
    return render_template("game-portal.html", \
                           game_name=gameId, playerlist=playerList, video_url=game.videoURL)

@app.route('/games/<gameId>/<playerId>/', methods=['GET'])
def gamePlayerView(gameId, playerId):
    # As a hack to get the browser to reaload the js on changes, append the last
    # update time to requests
    # See https://stackoverflow.com/a/54164514/537390
    last_updated = str(os.path.getmtime('static/game.js'))
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        return ErrorResponse(err)
        
    return render_template(
        "game.html", 
        video_url=game.videoURL,
        gameId=gameId, 
        playerId=playerId, 
        last_updated=last_updated)

#@app.route('/newGame<command>')
#def show_user_profile(command):
#    # show the user profile for that user
#    return 'User %s' % escape(username)
#https://www.w3schools.com/python/ref_requests_response.asp

def getParam(requestJSON, param, isList=False, isInt=False, isString=False):
    try:
        result = requestJSON[param]
    except BadRequestKeyError as err:
        raise ParamError('param not found: ' + param)
    except KeyError as err:
        raise ParamError('param not found: ' + param)
    except TypeError as err:
        #print('param exception:', str(e))
        #print('param exception:', type(e).__name__)
        raise ParamError('parameters not JSON')

    if isList:
        if not isinstance(result, Iterable):
            raise ParamError('list is not iterable')

    if isInt:
        result = int(result)

    return result

@app.route('/api/gamelist', methods=['GET'])
def retrieveGameList():
    return jsonify({'games' : list(activeGames.keys())})

@app.route('/api/gamestate/<gameId>', methods=['GET'])
def retrieveGameState(gameId):
    try:
        game = activeGames[gameId];
    except KeyError as err:
        return ErrorResponse(err)
    return jsonify(game.getStateDict())

@app.route('/api/newgame', methods=['POST'])
def startNewGame():
    # params:
    #  players: list of player names
    #  phrases: number of phrases per player
    #  time: number of seconds per turn
    #  videourl: URL of the video chat
    
    try:
        requestJSON = request.get_json()
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)

    def randomID():
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(8))

    try:
        id = getParam(requestJSON, 'id')
        if id in activeGames:
            print('game ID already exists:', id)
            return ErrorResponse('game ID already exists: ' + id)
    except ParamError as err:
        id = randomID()
        while id in activeGames:
            id = randomID()

    try:
        #id = getParam(requestJSON, 'id')
        #playerIds = getParam(requestJSON, 'players', isList=True)
        teams = getParam(requestJSON, 'teams', isList=True)
        phrasesPerPlayer = getParam(requestJSON, 'phrasesPerPlayer', isInt=True)
        secondsPerTurn = getParam(requestJSON, 'secondsPerTurn', isInt=True)
        videoURL = getParam(requestJSON, 'videoURL', isString=True)
    except ParamError as err:
        traceback.print_exc(file=sys.stdout)
        return ErrorResponse(err)

    #print('teams:', teams)
    #teams = [ [], [] ]
    #for playerIdx, playerId in enumerate(playerIds):
    #    teams[playerIdx % 2].append(playerId)


    print(f' game_log {id}: new game with teams: {teams}')
    newSession = GameSession(id, teams, phrasesPerPlayer, secondsPerTurn, videoURL)
    activeGames[id] = newSession
    return jsonify({'id' : id, 'gameURL' : '/games/' + id + '/'})

@app.route('/games/<gameId>/<playerId>/recordphrases', methods=['POST'])
def recordPhrases(gameId, playerId):
    # params:
    #  phrases: list of phrases to add. Should be exactly phrasesPerPlayer entries.
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    requestJSON = request.get_json()
    try:
        phrases = getParam(requestJSON, 'phrases', isList=True)
    except ParamError as err:
        return ErrorResponse(err)

    try:
        print(f"game_log {gameId}: Got phrases from player '{playerId}'': {phrases}")
        game.recordPlayerPhrases(playerId, phrases)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'phrases recorded'


@app.route('/games/<gameId>/<playerId>/addplayertoteam', methods=['POST'])
def addPlayerToTeam(gameId, playerId):
    # params:
    #  teamIndex: Index of the team to insert the new player.
    #  newPlayerName: Name of the new player to add.
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    requestJSON = request.get_json()
    try:
        teamIndex = getParam(requestJSON, 'teamIndex', isInt=True)
        newPlayerName = getParam(requestJSON, 'newPlayerName')
    except ParamError as err:
        return ErrorResponse(err)

    try:
        print(f"game_log {gameId}: Adding '{newPlayerName}' to team {teamIndex}")
        game.addPlayerToTeam(teamIndex, newPlayerName)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'new player added'

@app.route('/games/<gameId>/<playerId>/removeplayer', methods=['POST'])
def removePlayer(gameId, playerId):
    # params:
    #  playerName: Name of the player to remove.
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    requestJSON = request.get_json()
    try:
        playerName = getParam(requestJSON, 'playerName')
    except ParamError as err:
        return ErrorResponse(err)

    try:
        print(f"game_log {gameId}: Removing player '{playerName}'")
        game.removePlayer(playerName)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'player removed'

@app.route('/games/<gameId>/<playerId>/startturn', methods=['POST'])
def startTurn(gameId, playerId):
    # params:
    #  None
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    try:
       print(f"game_log {gameId}: Starting turn: '{playerId}'")
       game.startPlayerTurn(playerId)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'turn started'

@app.route('/games/<gameId>/<playerId>/endturn', methods=['POST'])
def endTurn(gameId, playerId):
    # params:
    #  None
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    try:
        print(f"game_log {gameId}: Ending turn: '{playerId}'")
        game.endPlayerTurn(playerId)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'turn ended'

@app.route('/games/<gameId>/prevphrase/<prevPhrase>', methods=['POST'])
def prevPhrase(gameId, prevPhrase):
    try:
        game = activeGames[gameId]
        print(f"  game_log {gameId}: Got phrase '{prevPhrase}'")
        game.recordPrevPhrase(prevPhrase)
        game.signalRefresh()
    except err:
        traceback.print_exc()
        return ErrorResponse(err)
    return 'phrase received'

@app.route('/games/<gameId>/<playerId>/confirmphrases', methods=['POST'])
def confirmPhrases(gameId, playerId):
    # params:
    #  acceptedPhrases: comma-separated phrases to confirm as 'accepted'.
    
    try:
        game = activeGames[gameId]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    requestJSON = request.get_json()
    try:
        acceptedPhrases = getParam(requestJSON, 'acceptedPhrases', isList=True)
    except ParamError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    try:
        print(f"game_log {gameId}: player '{playerId}' confirmed phrases {acceptedPhrases}")
        game.confirmPhrases(playerId, acceptedPhrases)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'phrases recorded'

# Create a few small deterministic games for UI testing
example_game_messages = []
def createDebugWriteGame():
    """  Create a game where 2 of 4 players have finished writing
    phrases"""
    game_id='debug_write_phase'
    game = GameSession(
        id=game_id, 
        teamPlayerLists=[ ['graham', 'matt'], ['nik', 'peter'] ],
        phrasesPerPlayer=3, 
        secondsPerTurn=30,
        videoURL='http://zoom.com')
    
    game.recordPlayerPhrases('graham', ['The Axiom of Choice', 'Uncountable', 'Ripple Shuffle'])
    game.recordPlayerPhrases('nik', ['Volcano', 'Google', 'Mitch McConnell'])
    activeGames[game_id] = game
    print('created game ' + game_id)
    example_game_messages.append('Example page writing words: http://127.0.0.1:5000/games/{}/peter'.format(game_id))

def createDebugMultiWordGame():
    """  Create a game in the MultiWord phase, right after words composed"""
    game_id='debug_multi_word_phase'
    game = GameSession(
        id=game_id, 
        teamPlayerLists=[
          ['graham', 'matt', 'amanda', 'ronan'], 
          ['nik', 'peter', 'jason'] 
        ],
        phrasesPerPlayer=2, 
        secondsPerTurn=5,
        videoURL='http://zoom.com')
    
    game.recordPlayerPhrases('graham', ['The Axiom of Choice', 'Uncountable'])
    game.recordPlayerPhrases('matt', ['Adobe', 'Entropy Sphere'])
    game.recordPlayerPhrases('amanda', ['3D printer', 'Pascal'])
    game.recordPlayerPhrases('ronan', ['fossil', 'man'])
    game.recordPlayerPhrases('nik', ['Volcano', 'Google'])
    game.recordPlayerPhrases('peter', ['Cat', 'Stripe', ])
    game.recordPlayerPhrases('jason', ['Lego', 'chillin'])
    
    # For reproducibility, let's make it Peter's turn, with Amanda next
    game.activeTeamIdx = 1
    game.teams[0].activePlayerIdx = 2
    game.teams[1].activePlayerIdx = 1
    activeGames[game_id] = game
    print('created game ' + game_id)
    example_game_messages.append('Example page to start a turn: http://127.0.0.1:5000/games/{}/peter'.format(game_id))
# TODO: Shold this be inside main?
createDebugWriteGame()
createDebugMultiWordGame()
print('')
for m in example_game_messages:
    print(m)

if __name__ == '__main__':
    print('running with multithreading')
    app.debug = True
    app.run(threaded=True)
