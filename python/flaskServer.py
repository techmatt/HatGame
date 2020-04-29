from flask import Flask
from flask import request
from werkzeug.exceptions import BadRequestKeyError
from markupsafe import escape

from gameSession import GameSession, GameError

app = Flask(__name__)

class ParamError(Exception):
    pass

activeGames = {}

@app.route('/')
def helloWorld():
    return 'Hello, World!'

#@app.route('/newGame<command>')
#def show_user_profile(command):
#    # show the user profile for that user
#    return 'User %s' % escape(username)

def getParam(form, param, isList=False, isInt=False):
    try:
        result = request.form[param]
    except BadRequestKeyError as err:
        print('param not found:', param)
        raise ParamError('param not found')

    if isList:
        result = result.split(',')
        if len(result) <= 1:
            print('not a valid list:', result)
            raise ParamError('not a valid list')

    if isInt:
        result = int(result)

    return result

@app.route('/newgame', methods=['POST'])
def startNewGame():
    # params:
    #  id: identifier for the game
    #  players: list of player names, comma-separated
    #  phrases: number of phrases per player
    #  time: number of seconds per turn
    error = None
    
    try:
        id = getParam(request.form, 'id')
        playerIDs = getParam(request.form, 'players', isList=True)
        phrasesPerPlayer = getParam(request.form, 'phrases', isInt=True)
        secondsPerTurn = getParam(request.form, 'time', isInt=True)
    except ParamError:
        error = 'bad key'
        return error

    if id in activeGames:
        print('game ID already exists:', id)
        error = 'game ID already exists'
        return error

    newSession = GameSession(id, playerIDs, phrasesPerPlayer, secondsPerTurn)
    activeGames[id] = newSession

    return 'New game!'

@app.route('/games/<gameID>/<playerID>/recordphrases', methods=['POST'])
def recordPhrases(gameID, playerID):
    # params:
    #  phrases: comma-separated phrases to add. Should be exactly phrasesPerPlayer entries.
    error = None
    
    try:
        game = activeGames[gameID]
    except KeyError as error:
        print('game ID not found', gameID)
        error = 'game-not-found'
        return error

    try:
        phrases = getParam(request.form, 'phrases', isList=True)
    except ParamError:
        error = 'bad key'
        return error

    try:
        game.recordPlayerPhrases(playerID, phrases)
    except GameError as err:
        print('game error:', err)
        error = 'game-error'
        return error
