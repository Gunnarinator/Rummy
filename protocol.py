import json
from typing import Literal, Mapping, Optional, Protocol, Sequence, Type, Union

from typing_extensions import Self

JSONSafe = Union[Mapping[str, "JSONSafe"], Sequence["JSONSafe"], str, int, float, bool, None]

class Encodable(Protocol):
    def encodeObject(self) -> JSONSafe:
        raise NotImplementedError()

    def encodeString(self) -> str:
        return json.dumps(self.encodeObject())

class Decodable(Protocol):
    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        raise NotImplementedError()

    @classmethod
    def decodeString(cls, data: str) -> Self:
        return cls.decodeObject(json.loads(data))

CardSuit = Literal["hearts", "diamonds", "spades", "clubs"]
CardRank = Literal["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

class CardFace(Encodable):
    def __init__(self, suit: CardSuit, rank: CardRank):
        self.suit = suit
        self.rank = rank

    def encodeObject(self) -> JSONSafe:
        return {
            "suit": self.suit,
            "rank": self.rank
        }

class ClientCard(Encodable):
    def __init__(self, id: str, face: Optional[CardFace] = None):
        self.id = id
        self.face = face

    def encodeObject(self) -> JSONSafe:
        return {
            "id": self.id,
            "face": self.face.encodeObject() if self.face else None
        }

ClientStack = list[ClientCard]

class ClientPlayer(Encodable):
    """
    Properties:
        name (str): The name of the player.
        id (str): A randomized string uniquely identifying the player.
        hand (ClientStack): The stack of cards the player has.
        human (bool): Whether the player is human.
    """

    def __init__(self, name: str, id: str, hand: ClientStack, human: bool):
        """
        Args:
            name (str): The name of the player.
            id (str): A randomized string uniquely identifying the player.
            hand (ClientStack): The stack of cards the player has.
            human (bool): Whether the player is human.
        """
        self.name = name
        self.id = id
        self.hand = hand
        self.human = human

    def encodeObject(self) -> JSONSafe:
        return {
            "name": self.name,
            "id": self.id,
            "hand": [card.encodeObject() for card in self.hand],
            "human": self.human
        }

class TurnState(Encodable):
    def __init__(self, player_id: str, state: Literal["draw", "play"]):
        self.player_id = player_id
        self.state = state

    def encodeObject(self) -> JSONSafe:
        return {
            "player_id": self.player_id,
            "state": self.state
        }

class LobbyPlayer(Encodable):
    """
    Properties:
        name (str): The name of the player.
        id (str): A randomized string uniquely identifying the player.
        human (bool): Whether the player is human.
    """
    def __init__(self, name: str, id: str, human: bool):
        """
        Args:
            name (str): The name of the player.
            id (str): A randomized string uniquely identifying the player.
            human (bool): Whether the player is human.
        """
        self.name = name
        self.id = id
        self.human = human

    def encodeObject(self) -> JSONSafe:
        return {
            "name": self.name,
            "id": self.id,
            "human": self.human
        }

class ClientLobby(Encodable):
    """
    A lobby of players.

    Properties:
        players (list[ClientPlayer]): A list of players currently in the game.
        current_player_id (str): The player ID string of the current user.
        code (str): The code to join the current game.
    """
    def __init__(self, players: list[LobbyPlayer], current_player_id: str, code: str):
        """
        A lobby of players.

        Args:
            players (list[LobbyPlayer]): A list of players currently in the game.
            current_player_id (str): The player ID string of the current user.
            code (str): The code to join the current game.
        """
        self.players = players
        self.current_player_id = current_player_id
        self.code = code
        self.players = players
        self.current_player_id = current_player_id
        self.code = code

    def encodeObject(self) -> JSONSafe:
        return {
            "players": [player.encodeObject() for player in self.players],
            "current_player_id": self.current_player_id,
            "code": self.code
        }

class ClientBoard(Encodable):
    """
    Properties:
        players (list[ClientPlayer]): An array of 1-4 players currently in the game.
        current_player_id (str): The player ID string of the current user.
        turn (TurnState): Indicates which players turn it is. A null value means the game has not started yet or has ended, so it is no one's turn.
        melds (list[ClientMeld]): An array of the melds currently on the table. At the beginning of the game, this is an empty array.
        deck (ClientStack): The stack of face-down cards that have yet to be drawn. The next card to be drawn is the first item in the array.
        discard (ClientStack): The stack of face-up cards that have been discarded. The last card to be discarded is the first item in the array.
        game_code (str): A code that other players may use to join the game before it starts.
    """
    def __init__(self, players: list[ClientPlayer], current_player_id: str, turn: Optional[TurnState], melds: list[ClientStack], deck: ClientStack, discard: ClientStack, game_code: str):
        """
        Args:
            players (list[ClientPlayer]): A list of players currently in the game.
            current_player_id (str): The player ID string of the current user.
            turn (Optional[TurnState]): Indicates which players turn it is. A null value means the game has not started yet or has ended, so it is no one's turn.
            melds (list[ClientStack]): An array of the melds currently on the table. At the beginning of the game, this is an empty array.
            deck (ClientStack): The stack of face-down cards that have yet to be drawn. The next card to be drawn is the first item in the array.
            discard (ClientStack): The stack of face-up cards that have been discarded. The last card to be discarded is the first item in the array.
            game_code (str): A code that other players may use to join the game before it starts.
        """
        self.players = players
        self.current_player_id = current_player_id
        self.turn = turn
        self.melds = melds
        self.deck = deck
        self.discard = discard
        self.game_code = game_code

    def encodeObject(self) -> JSONSafe:
        return {
            "players": [player.encodeObject() for player in self.players],
            "current_player_id": self.current_player_id,
            "turn": self.turn.encodeObject() if self.turn else None,
            "melds": [[card.encodeObject() for card in meld] for meld in self.melds],
            "deck": [card.encodeObject() for card in self.deck],
            "discard": [card.encodeObject() for card in self.discard],
            "game_code": self.game_code
        }

class LobbyEvent(Encodable):
    """
    A message received from the server that updates the state of the lobby.

    Properties:
        lobby (ClientLobby): The lobby state.
    """
    def __init__(self, lobby: ClientLobby):
        """
        A message received from the server that updates the state of the lobby.

        Args:
            lobby (ClientLobby): The lobby state.
        """
        self.lobby = lobby

    def encodeObject(self) -> JSONSafe:
        return {"type": "lobby", "lobby": self.lobby.encodeObject()}

class StartEvent(Encodable):
    """
    Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.

    Properties:
        players (list[ClientPlayer]): A list of players currently in the game.
        current_player_id (str): The player ID string of the current user.
        card_ids (list[str]): A list of face-down card IDs to include in the deck. The order matches the shuffled state of the deck.
        game_code (str): A code that other players may use to join the game before it starts.
    """
    def __init__(self, players: list[ClientPlayer], current_player_id: str, card_ids: list[str], game_code: str):
        """
        Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.

        Args:
            players (list[ClientPlayer]): A list of players currently in the game.
            current_player_id (str): The player ID string of the current user.
            card_ids (list[str]): A list of face-down card IDs to include in the deck. The order matches the shuffled state of the deck.
            game_code (str): A code that other players may use to join the game before it starts.
        """
        self.players = players
        self.current_player_id = current_player_id
        self.card_ids = card_ids
        self.game_code = game_code

    def encodeObject(self) -> JSONSafe:
        return {
            "type": "start",
            "players": [player.encodeObject() for player in self.players],
            "current_player_id": self.current_player_id,
            "card_ids": self.card_ids,
            "game_code": self.game_code
        }

class TurnEvent(Encodable):
    """
    Updates the current turn state of the game.

    Properties:
        player_id (str): The player ID who's turn it currently is.
        state (Literal["draw", "play"]): The step the player must take.
            `"draw"`: The player must draw a card either from the discard pile or the deck.
            `"play"`: The player can try to create or lay on melds as they see fit, and then they must discard a card.
    """
    def __init__(self, player_id: str, state: Literal["draw", "play"]):
        """
        Updates the current turn state of the game.

        Args:
            player_id (str): The player ID who's turn it currently is.
            state (Literal["draw", "play"]): The step the player must take.
                `"draw"`: The player must draw a card either from the discard pile or the deck.
                `"play"`: The player can try to create or lay on melds as they see fit, and then they must discard a card.
        """
        self.player_id = player_id
        self.state = state
        self.player_id = player_id
        self.state = state

    def encodeObject(self) -> JSONSafe:
        return {"type": "turn", "player_id": self.player_id, "state": self.state}

class MoveDestinationPlayer(Encodable):
    """
    Properties:
        player_id (str): The player ID of the player to move the cards to.
        position (int): The position in the player's hand to move the cards to. `0` represents the card all the way to the left in the hand.
    """
    def __init__(self, player_id: str, position: int):
        """
        Args:
            player_id (str): The player ID of the player to move the cards to.
            position (int): The position in the player's hand to move the cards to. `0` represents the card all the way to the left in the hand.
        """
        self.player_id = player_id
        self.position = position

    def encodeObject(self) -> JSONSafe:
        return {
            "type": "player",
            "player_id": self.player_id,
            "position": self.position
        }

class MoveDestinationMeld(Encodable):
    """
    Properties:
        meld_number (int): The number of the meld to move the cards to. `0` represents the first meld that was laid down.
        position (int): The position in the meld to move the cards to. `0` represents the card all the way to the left in the meld.
    """
    def __init__(self, meld_number: int, position: int):
        """
        Args:
            meld_number (int): The number of the meld to move the cards to. `0` represents the first meld that was laid down.
            position (int): The position in the meld to move the cards to. `0` represents the card all the way to the left in the meld.
        """
        self.meld_number = meld_number
        self.position = position

    def encodeObject(self) -> JSONSafe:
        return {
            "type": "meld",
            "meld_number": self.meld_number,
            "position": self.position
        }

class MoveDesinationDiscard(Encodable):
    def encodeObject(self) -> JSONSafe:
        return {
            "type": "discard"
        }

class MoveEvent(Encodable):
    """
    Indicates that a card has been moved, either by the current player or by someone else. `card.face` being present indicates that the card is face-up.

    Properties:
        cards (list[ClientCard]): The cards that are moved. `face` being present indicates that this card is face up (and should be revealed if necessary).
        destination (Union[MoveDestinationPlayer, MoveDestinationMeld, MoveDestinationDiscard]): The final destination of the cards. The client will animate the cards moving from their current position to the new position.
    """
    def __init__(self, cards: list[ClientCard], destination: Union[MoveDestinationPlayer, MoveDestinationMeld, MoveDesinationDiscard]):
        """
        Indicates that a card has been moved, either by the current player or by someone else. `card.face` being present indicates that the card is face-up.

        Args:
            cards (list[ClientCard]): The cards that are moved. `face` being present indicates that this card is face up (and should be revealed if necessary).
            destination (Union[MoveDestinationPlayer, MoveDestinationMeld, MoveDestinationDiscard]): The final destination of the cards. The client will animate the cards moving from their current position to the new position.
        """
        self.cards = cards
        self.destination = destination

    def encodeObject(self) -> JSONSafe:
        return {
            "type": "move",
            "cards": [card.encodeObject() for card in self.cards],
            "destination": self.destination.encodeObject()
        }

class RedeckEvent(Encodable):
    """
    Indicates that the deck has been replenished from the discard pile.

    All cards in the discard pile are considered to be destroyed, and the deck is replaced with new cards.

    Properties:
        new_card_ids (list[str]): The server should generate a new list of card IDs to use for the new deck.
    """
    def __init__(self, new_card_ids: list[str]):
        """
        Indicates that the deck has been replenished from the discard pile.

        All cards in the discard pile are considered to be destroyed, and the deck is replaced with new cards.

        Args:
            new_card_ids (list[str]): The server should generate a new list of card IDs to use for the new deck.
        """
        self.new_card_ids = new_card_ids

    def encodeObject(self) -> JSONSafe:
        return {"type": "redeck", "new_card_ids": self.new_card_ids}

class EndEvent(Encodable):
    """
    Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping. The client keeps track of score.

    Properties:
        winner_id (str): The player ID of the winner.
        hand_values (dict[str, int]): A map (keyed by player ID) showing the hand values of the losing players. These point values will be added to the winner's score. "Rummy" should already be accounted for.
    """
    def __init__(self, winner_id: str, hand_values: dict[str, int]):
        """
        Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping. The client keeps track of score.

        Args:
            winner_id (str): The player ID of the winner.
            hand_values (dict[str, int]): A map (keyed by player ID) showing the hand values of the losing players. These point values will be added to the winner's score. "Rummy" should already be accounted for.
        """
        self.winner_id = winner_id
        self.hand_values = hand_values

    def encodeObject(self) -> JSONSafe:
        return {
            "type": "end",
            "winner_id": self.winner_id,
            "hand_values": self.hand_values
        }


Event = Union[LobbyEvent, StartEvent, TurnEvent, MoveEvent, RedeckEvent, EndEvent]
"""
A message recieved from the server.

`"lobby"`: Update the state of the lobby.
`"start"`: Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.
`"turn"`: Update the current turn state of the game.
`"move"`: Indicates that a card has been moved, either by the current player or by someone else. `card.face` being present indicates that the card is face-up.
`"redeck"`: Indicates that the deck has been replenished from the discard pile.
`"end"`: Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping.
"""

class JoinAction(Decodable):
    """
    Joins a game. A game is left when the websocket connection is closed.

    The server should verify that the game is not already running, and that thare are less than 4 players in the game.

    Properties:
        code (str): The game code to join.
    """
    def __init__(self, code: str):
        """
        Joins a game. A game is left when the websocket connection is closed.

        The server should verify that the game is not already running, and that thare are less than 4 players in the game.

        Args:
            code (str): The game code to join.
        """
        self.code = code

    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data["code"], str)
        return JoinAction(data["code"])

class StartAction(Decodable):
    """
    Starts the current game.

    The server should verify that at least two players are in the game.
    """
    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        return StartAction()

class DrawAction(Decodable):
    """
    Draws a card from the deck or the discard pile.

    The server should verify that the card ID is at the top of the discard pile or the deck.

    Properties:
        card_id (str): The ID of the card to draw. This can be the top card of the deck or the top card of the discard pile.
    """
    def __init__(self, card_id: str):
        """
        Draws a card from the deck or the discard pile.

        The server should verify that the card ID is at the top of the discard pile or the deck.

        Args:
            card_id (str): The ID of the card to draw. This can be the top card of the deck or the top card of the discard pile.
        """
        self.card_id = card_id

    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data["card_id"], str)
        return DrawAction(data["card_id"])

class MeldAction(Decodable):
    """
    Lay down some cards to create a meld.

    The server should verify that (A) all cards are in the player's hand, and (B) that the cards form a valid meld.

    Properties:
        card_ids (list[str]): A list of card IDs to lay down.
    """
    def __init__(self, card_ids: list[str]):
        """
        Lay down some cards to create a meld.

        The server should verify that (A) all cards are in the player's hand, and (B) that the cards form a valid meld.

        Args:
            card_ids (list[str]): A list of card IDs to lay down.
        """
        self.card_ids = card_ids

    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data["card_ids"], list)
        assert all(isinstance(card_id, str) for card_id in data["card_ids"])
        return MeldAction(data["card_ids"]) #type: ignore

class LayAction(Decodable):
    """
    Lay down a card to add to an existing meld.

    The server should verify that the card is in the player's hand, and that the card forms a valid meld.

    Properties:
        card_id (str): The ID of the card to lay.
        meld_number (int): The index of the meld to add the card to.
    """
    def __init__(self, card_id: str, meld_number: int):
        """
        Lay down a card to add to an existing meld.

        The server should verify that the card is in the player's hand, and that the card forms a valid meld.

        Args:
            card_id (str): The ID of the card to lay.
            meld_number (int): The index of the meld to add the card to.
        """
        self.card_id = card_id
        self.meld_number = meld_number

    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data["card_id"], str)
        assert isinstance(data["meld_number"], int)
        return LayAction(data["card_id"], data["meld_number"])

class DiscardAction(Decodable):
    """
    Discard a card. This ends the player's turn.

    The server should verify that the card is in the player's hand.

    Properties:
        card_id (str): The ID of the card to discard.
    """
    def __init__(self, card_id: str):
        """
        Discard a card. This ends the player's turn.

        The server should verify that the card is in the player's hand.

        Args:
            card_id (str): The ID of the card to discard.
        """
        self.card_id = card_id

    @classmethod
    def decodeObject(cls, data: JSONSafe) -> Self:
        assert isinstance(data, dict)
        assert isinstance(data["card_id"], str)
        return DiscardAction(data["card_id"])

Action = Union[JoinAction, StartAction, DrawAction, MeldAction, LayAction, DiscardAction]
"""
A message sent to the server. Indicates an action that the client wishes to perform.

The client does not assume any side-effects of these actions. The server must send events back to the client to indicate the result of the action.

`"name"`: Sets the name of the current player.
`"ai"`: Add or remove an AI player.
`"join"`: Joins a game.
`"start"`: Starts a game.
`"draw"`: Draws a card from the deck or the discard pile.
`"meld"`: Lay down some cards to create a meld.
`"lay"`: Lay down a card to add to an existing meld.
`"discard"`: Discard a card.

The server should verify the legality of every action taken by the client, including whether it is the player's turn, and that the player's turn state is appropriate.
"""

actionTypeMap: dict[str, Type[Action]] = {
    "join": JoinAction,
    "start": StartAction,
    "draw": DrawAction,
    "meld": MeldAction,
    "lay": LayAction,
    "discard": DiscardAction
}
