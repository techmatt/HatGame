from flask import Flask, request, Response
from werkzeug.exceptions import BadRequestKeyError
from collections import Iterable
from markupsafe import escape

from gameSession import GameSession, GameError

app = Flask(__name__)

class ParamError(Exception):
    pass

def ErrorResponse(obj):
    return Response(str(obj), status=400, mimetype='application/text')

activeGames = {}

@app.route('/')
def helloWorld():
    return 'Hello, World!'

#@app.route('/newGame<command>')
#def show_user_profile(command):
#    # show the user profile for that user
#    return 'User %s' % escape(username)
#https://www.w3schools.com/python/ref_requests_response.asp

def getParam(requestJSON, param, isList=False, isInt=False):
    try:
        result = requestJSON[param]
    except BadRequestKeyError as err:
        #print('param not found:', param)
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

@app.route('/gamelist', methods=['GET'])
def retrieveGameList():
    return {'games' : list(activeGames.keys())}

@app.route('/gamestate', methods=['GET'])
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


@app.route('/newgame', methods=['POST'])
def startNewGame():
    # params:
    #  id: identifier for the game
    #  players: list of player names, comma-separated
    #  phrases: number of phrases per player
    #  time: number of seconds per turn
    
    requestJSON = request.get_json()
    try:
        id = getParam(requestJSON, 'id')
        playerIDs = getParam(requestJSON, 'players', isList=True)
        phrasesPerPlayer = getParam(requestJSON, 'phrases', isInt=True)
        secondsPerTurn = getParam(requestJSON, 'time', isInt=True)
    except ParamError as err:
        return ErrorResponse(err)

    if id in activeGames:
        print('game ID already exists:', id)
        return ErrorResponse('game ID already exists: ' + id)

    print('new game players:', playerIDs)
    newSession = GameSession(id, playerIDs, phrasesPerPlayer, secondsPerTurn)
    activeGames[id] = newSession
    return 'game created'

@app.route('/games/<gameID>/<playerID>/recordphrases', methods=['POST'])
def recordPhrases(gameID, playerID):
    # params:
    #  phrases: comma-separated phrases to add. Should be exactly phrasesPerPlayer entries.
    
    try:
        game = activeGames[gameID]
    except KeyError as err:
        print('game ID not found', gameID)
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
        print('game error:', err)
        return ErrorResponse(err)
    return 'phrases recorded'
