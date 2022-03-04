from lobby import *
from protocol import *

games: dict[str, 'Game'] = {}

class Game:
	def __init__(self, lobby: Lobby):
		self.lobby = lobby.code
		games[self.lobby] = self

# Action = Union[JoinAction, StartAction, DrawAction, MeldAction, LayAction, DiscardAction]
def handleAction(action: Action, connection: Connection):
	lobby = connection.lobby
	# If the game hasn't started het, this will be None
	game = games.get(lobby.code, None)

	if isinstance(action, JoinAction):

		# Joins a game. A game is left when the websocket connection is closed.
		# The server should verify that the game is not already running, and that thare are less than 4 players in the game.
		#  - code (str): The game code to join.
		if action.code in lobbies and not action.code in games and len(lobbies[action.code].connections) < 4:
			lobbies[action.code].addPlayer(connection)

	elif isinstance(action, StartAction):

		# Starts the current game.
		# The server should verify that at least two players are in the game.
		raise NotImplementedError()

	elif isinstance(action, DrawAction):

		# Draws a card from the deck or the discard pile.
		# The server should verify that the card ID is at the top of the discard pile or the deck.
        #  - card_id (str): The ID of the card to draw. This can be the top card of the deck or the top card of the discard pile.
		raise NotImplementedError()

	elif isinstance(action, MeldAction):

		# Lay down some cards to create a meld.
		# The server should verify that (A) all cards are in the player's hand, and (B) that the cards form a valid meld.
		#  - card_ids (list[str]): A list of card IDs to lay down.
		raise NotImplementedError()

	elif isinstance(action, LayAction):

		# Lay down a card to add to an existing meld.
		# The server should verify that the card is in the player's hand, and that the card forms a valid meld.
		#  - card_id (str): The ID of the card to lay.
		#  - meld_number (int): The index of the meld to add the card to.
		raise NotImplementedError()

	elif isinstance(action, DiscardAction):

		# Discard a card. This ends the player's turn.
		# The server should verify that the card is in the player's hand.
		#  - card_id (str): The ID of the card to discard.
		raise NotImplementedError()

	else:
		raise RuntimeError("Unknown action type")
