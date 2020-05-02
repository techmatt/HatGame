
from flask import Flask, request, Response, send_from_directory, render_template, jsonify
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

@app.route('/')
def homePage():
	return render_template("base.html", message="Hello Flask!")
	try:
		#return send_from_directory('template/', 'index.html', as_attachment=False)
		return render_template("base.html", message="Hello Flask!")
	except Exception as err:
		print('failed:', str(err))
		return ErrorResponse(err)

@app.route('/gamelist')
def gameListHTML():
    return render_template("game_list.html")
    
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
        #result = result.split(',')
        #if len(result) <= 1:
        #    print('not a valid list:', result)
        #    raise ParamError('not a valid list')

    if isInt:
        result = int(result)

    return result

@app.route('/api/gamelist', methods=['GET'])
def retrieveGameList():
    return jsonify({'games' : list(activeGames.keys())})

@app.route('/api/gamestate', methods=['GET'])
def retrieveGameState():
    requestJSON = request.get_json()
    try:
        gameID = getParam(requestJSON, 'id')
    except ParamError as err:
        return ErrorResponse(err)

    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    return game.getStateDict()


@app.route('/api/newgame', methods=['POST'])
def startNewGame():
    # params:
    #  id: identifier for the game
    #  players: list of player names
    #  phrases: number of phrases per player
    #  time: number of seconds per turn
    #  videourl: URL of the video chat
    
    requestJSON = request.get_json()
    try:
        id = getParam(requestJSON, 'id')
        playerIDs = getParam(requestJSON, 'players', isList=True)
        phrasesPerPlayer = getParam(requestJSON, 'phrases', isInt=True)
        secondsPerTurn = getParam(requestJSON, 'time', isInt=True)
        videoURL = getParam(requestJSON, 'videoURL', isString=True)
    except ParamError as err:
        return ErrorResponse(err)

    if id in activeGames:
        print('game ID already exists:', id)
        return ErrorResponse('game ID already exists: ' + id)

    print('new game players:', playerIDs)
    newSession = GameSession(id, playerIDs, phrasesPerPlayer, secondsPerTurn, videoURL)
    activeGames[id] = newSession
    return 'game created'

@app.route('/games/<gameID>/<playerID>/recordphrases', methods=['POST'])
def recordPhrases(gameID, playerID):
    # params:
    #  phrases: list of phrases to add. Should be exactly phrasesPerPlayer entries.
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    requestJSON = request.get_json()
    print('requestJSON:', requestJSON)
    try:
        phrases = getParam(requestJSON, 'phrases', isList=True)
    except ParamError as err:
        return ErrorResponse(err)

    try:
        game.recordPlayerPhrases(playerID, phrases)
    except GameError as err:
        return ErrorResponse(err)
    return 'phrases recorded'

@app.route('/games/<gameID>/<playerID>/startturn', methods=['POST'])
def startTurn(gameID, playerID):
    # params:
    #  None
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    try:
        game.startPlayerTurn(playerID)
    except GameError as err:
        return ErrorResponse(err)
    return 'turn started'

@app.route('/games/<gameID>/<playerID>/endturn', methods=['POST'])
def endTurn(gameID, playerID):
    # params:
    #  None
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    try:
        game.endPlayerTurn(playerID)
    except GameError as err:
        return ErrorResponse(err)
    return 'turn ended'

@app.route('/games/<gameID>/<playerID>/confirmphrases', methods=['POST'])
def confirmPhrases(gameID, playerID):
    # params:
    #  acceptedPhrases: comma-separated phrases to confirm as 'accepted'.
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        return ErrorResponse(err)

    requestJSON = request.get_json()
    print('requestJSON:', requestJSON)
    try:
        acceptedPhrases = getParam(requestJSON, 'acceptedPhrases', isList=True)
    except ParamError as err:
        return ErrorResponse(err)

    try:
        game.confirmPhrases(playerID, acceptedPhrases)
    except GameError as err:
        return ErrorResponse(err)
    return 'phrases recorded'
