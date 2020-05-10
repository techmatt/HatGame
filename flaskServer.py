
import traceback
import sys
import os
from flask import Flask, request, Response, send_from_directory, render_template, jsonify, json
from werkzeug.exceptions import BadRequestKeyError
from collections import Iterable
from markupsafe import escape

from python.gameSession import GameSession, GameError

app = Flask(__name__)

class ParamError(Exception):
    pass

def ErrorResponse(obj):
    return Response(str(obj), status=400, mimetype='application/text')

activeGames = {}

def eventStream(game, player):
    event = player.refreshEvent
    while True:
        print('waiting for event to be set')
        event.wait()
        event.clear()
        print('refresh event triggered for', player.id)
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

@app.route('/api/stream/<gameID>/<playerID>/events', methods=['GET'])
def stream(gameID, playerID):
    try:
        game = activeGames[gameID]
        player = game.playersByID[playerID]
    except KeyError as err:
        return ErrorResponse(err)
    print('registering for stream', gameID, playerID)
    return Response(eventStream(game, player),
                    mimetype="text/event-stream")
    """var source = new EventSource('/api/stream/<gameID>/<playerID>/events');
       source.onmessage = function (event) { alert(event.data); };"""

@app.route('/api/refresh/<gameID>/', methods=['GET'])
def signalRefreshDebug(gameID):
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)
    game.signalRefresh()
    print('signaled refresh for', gameID)
    return 'success'

@app.route('/games/<gameID>/', methods=['GET'])
def gamePortal(gameID):
    # params:
    #  gameID: ID of the game
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    playerList = []
    for player in game.players:
        d = {}
        d['href'] = player.id + '/'
        d['caption'] = player.id
        playerList.append(d)
    return render_template("game-portal.html", \
                           game_name=gameID, playerlist=playerList, video_url=game.videoURL)

@app.route('/games/<gameId>/<playerId>/', methods=['GET'])
def gamePlayerView(gameId, playerId):
    # As a hack to get the browser to reaload the js on changes, append the last
    # update time to requests
    # See https://stackoverflow.com/a/54164514/537390
    last_updated = str(os.path.getmtime('static/game.js'))
    return render_template(
        "game.html", 
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
    #  id: identifier for the game
    #  players: list of player names
    #  phrases: number of phrases per player
    #  time: number of seconds per turn
    #  videourl: URL of the video chat
    
    try:
        requestJSON = request.get_json()
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)

    try:
        id = getParam(requestJSON, 'id')
        playerIDs = getParam(requestJSON, 'players', isList=True)
        phrasesPerPlayer = getParam(requestJSON, 'phrasesPerPlayer', isInt=True)
        secondsPerTurn = getParam(requestJSON, 'secondsPerTurn', isInt=True)
        videoURL = getParam(requestJSON, 'videoURL', isString=True)
    except ParamError as err:
        traceback.print_exc(file=sys.stdout)
        return ErrorResponse(err)

    if id in activeGames:
        print('game ID already exists:', id)
        return ErrorResponse('game ID already exists: ' + id)

    print('new game players:', playerIDs)
    newSession = GameSession(id, playerIDs, phrasesPerPlayer, secondsPerTurn, videoURL)
    activeGames[id] = newSession
    return jsonify({'gameURL' : '/games/' + id + '/'})

@app.route('/games/<gameID>/<playerID>/recordphrases', methods=['POST'])
def recordPhrases(gameID, playerID):
    # params:
    #  phrases: list of phrases to add. Should be exactly phrasesPerPlayer entries.
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    requestJSON = request.get_json()
    print('requestJSON:', requestJSON)
    try:
        phrases = getParam(requestJSON, 'phrases', isList=True)
    except ParamError as err:
        return ErrorResponse(err)

    try:
        print("Got phrases from player {}: {}".format(playerID, phrases))
        game.recordPlayerPhrases(playerID, phrases)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'phrases recorded'

@app.route('/games/<gameID>/<playerID>/startturn', methods=['POST'])
def startTurn(gameID, playerID):
    # params:
    #  None
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    try:
        game.startPlayerTurn(playerID)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'turn started'

@app.route('/games/<gameID>/<playerID>/endturn', methods=['POST'])
def endTurn(gameID, playerID):
    # params:
    #  None
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        traceback.print_exc()
        return ErrorResponse(err)

    try:
        game.endPlayerTurn(playerID)
    except GameError as err:
        traceback.print_exc()
        return ErrorResponse(err)
    game.signalRefresh()
    return 'turn ended'

@app.route('/games/<gameID>/<playerID>/confirmphrases', methods=['POST'])
def confirmPhrases(gameID, playerID):
    # params:
    #  acceptedPhrases: comma-separated phrases to confirm as 'accepted'.
    
    try:
        game = activeGames[gameID]
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
        game.confirmPhrases(playerID, acceptedPhrases)
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
        playerIDs=['graham', 'matt', 'nik', 'peter'],
        phrasesPerPlayer=3, 
        secondsPerTurn=3,
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
        playerIDs=['graham', 'matt', 'nik', 'peter'],
        phrasesPerPlayer=3, 
        secondsPerTurn=3,
        videoURL='http://zoom.com')
    
    game.recordPlayerPhrases('graham', ['The Axiom of Choice', 'Uncountable', 'Ripple Shuffle'])
    game.recordPlayerPhrases('nik', ['Volcano', 'Google', 'Mitch McConnell'])
    game.recordPlayerPhrases('matt', ['Adobe', 'Entropy Sphere', 'Heat Death'])
    game.recordPlayerPhrases('peter', ['Cat', 'Stripe', 'Optimization'])
    # For reproducibility, let''s make it Peter's turn and link to that
    game.activePlayerIdx = 3
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
