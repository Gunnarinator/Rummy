from random import shuffle
from uuid import uuid4

import funlib
import lobby
from protocol import *

# This file should contain all classes created by Super Rummy.

games: dict[str, "Game"] = {}


class GameSettings:

    # deck_count, hand_size, first_turn, allow_draw_choice, allow_run_mixed_suit, limit_meld_size, ace_rank, deck_exhaust, require_end_discard, lay_at_end
    def __init__(self,
                 deck_count: int = 1,
                 enable_jokers: bool = False,
                 hand_size: int = 7,
                 first_turn: Literal["next_player",
                                     "prev_winner", "random"] = "next_player",
                 allow_draw_choice: bool = False,
                 allow_run_mixed_suit: bool = False,
                 limit_meld_size: Optional[Literal[3, 4]] = None,
                 ace_rank: Literal["low", "high"] = "low",
                 deck_exhaust: Literal["flip_discard",
                                       "shuffle_discard", "end_round"] = "flip_discard",
                 require_end_discard: bool = False,
                 lay_at_end: bool = True):
        self.deck_count = deck_count
        self.enable_jokers = enable_jokers
        self.hand_size = hand_size
        self.first_turn = first_turn
        self.allow_draw_choice = allow_draw_choice
        self.allow_run_mixed_suit = allow_run_mixed_suit
        self.limit_meld_size = limit_meld_size
        self.ace_rank = ace_rank
        self.deck_exhaust = deck_exhaust
        self.require_end_discard = require_end_discard
        self.lay_at_end = lay_at_end


class ServerCard:
    def __init__(self, face: CardFace):
        self.id = uuid4().hex
        self.face = face

    def makeForClient(self, visible: bool):
        return ClientCard(id=self.id, face=self.face if visible else None)

    def sortingSuitPosition(self, settings: GameSettings):
        if self.face.suit == "hearts":
            return 0
        elif self.face.suit == "clubs":
            return 1
        elif self.face.suit == "diamonds":
            return 2
        elif self.face.suit == "spades":
            return 3
        else:
            return 4

    def sortingRankPosition(self, settings: GameSettings):
        if self.face.rank == "A":
            return 14 if settings.ace_rank == "high" else 1
        elif self.face.rank == "2":
            return 2
        elif self.face.rank == "3":
            return 3
        elif self.face.rank == "4":
            return 4
        elif self.face.rank == "5":
            return 5
        elif self.face.rank == "6":
            return 6
        elif self.face.rank == "7":
            return 7
        elif self.face.rank == "8":
            return 8
        elif self.face.rank == "9":
            return 9
        elif self.face.rank == "10":
            return 10
        elif self.face.rank == "J":
            return 11
        elif self.face.rank == "Q":
            return 12
        elif self.face.rank == "K":
            return 13
        else:
            return 15

    def isSortedBefore(self, other: Self, settings: GameSettings):
        if self.sortingSuitPosition(settings) < other.sortingSuitPosition(settings):
            return True
        elif self.sortingSuitPosition(settings) == other.sortingSuitPosition(settings):
            return self.sortingRankPosition(settings) < other.sortingRankPosition(settings)
        else:
            return False


class Stack:
    def __init__(self, num_decks: int = 0, jokers: bool = False):
        self.cards = funlib.newDeck(num_decks, jokers)

    def top(self):
        return self.cards[-1]

    def reshuffle(self):
        shuffle(self.cards)
        for i in range(len(self.cards)):
            self.cards[i].id = uuid4().hex

    def remove(self, cards: list[ServerCard]):
        for card in cards:
            self.cards.remove(card)

    def insert(self, cards: list[ServerCard], position: int):
        for card in cards:
            self.cards.insert(position, card)
            position = position + 1


class BoardPlayer():
    def __init__(self, connection: 'lobby.Connection'):
        self.hand = Stack(0, False)
        self.connection = connection

    def getDestinationHandPosition(self, card: ServerCard, settings: GameSettings):
        for i in range(len(self.hand.cards)):
            if card.isSortedBefore(self.hand.cards[i], settings):
                return i
        return len(self.hand.cards)

    def makeForClient(self, visibleCards: bool):
        return ClientPlayer(self.connection.name, self.connection.id, [card.makeForClient(visibleCards) for card in self.hand.cards], True)


class Game:
    def __init__(self, l: 'lobby.Lobby', settings: GameSettings):
        self.lobby = l.code
        self.settings = settings
        games[self.lobby] = self
        # TODO: jokers are not currently supported
        self.deck = Stack(settings.deck_count, settings.enable_jokers)
        self.discard = Stack(0, False)
        self.players: list["BoardPlayer"] = [BoardPlayer(
            lobby.connections[player]) for player in l.connections]
        self.melds: list[Stack] = []
        self.turn_player: int = 0  # TODO: respect settings.first_turn
        self.turn_has_drawn: bool = False

    def moveCardsToDiscard(self, cards: list[ServerCard], originalStack: Stack):
        originalStack.remove(cards)
        destPosition = len(self.discard.cards)
        for client in self.players:
            client.connection.sendEvent(MoveEvent([
                card.makeForClient(True) for card in cards
            ], MoveDesinationDiscard()))
        self.discard.insert(cards, destPosition)

    def moveCardsToHand(self, cards: list[ServerCard], originalStack: Stack, player: BoardPlayer, destPosition: int):
        originalStack.remove(cards)
        destPosition = min(max(destPosition, 0), len(player.hand.cards))
        for client in self.players:
            client.connection.sendEvent(MoveEvent([
                card.makeForClient(client is player) for card in cards
            ], MoveDestinationPlayer(player.connection.id, destPosition)))
        player.hand.insert(cards, destPosition)

    def moveCardsToMeld(self, cards: list[ServerCard], originalStack: Stack, meldNumber: int, destPosition: int):
        originalStack.remove(cards)
        meldNumber = min(max(meldNumber, 0), len(self.melds))
        if (meldNumber > len(self.melds)):
            self.melds.append(Stack(0, False))
        destPosition = min(max(destPosition, 0), len(
            self.melds[meldNumber].cards))
        for client in self.players:
            client.connection.sendEvent(MoveEvent([
                card.makeForClient(True) for card in cards
            ], MoveDestinationMeld(meldNumber, destPosition)))
        self.melds[meldNumber].insert(cards, destPosition)

    def deal(self):
        for i in range(self.settings.hand_size):
            for player in self.players:
                card = self.deck.top()
                self.moveCardsToHand(
                    [card], self.deck, player, player.getDestinationHandPosition(card, self.settings))

    def notifyPlayersOfTurnState(self):
        for client in self.players:
            client.connection.sendEvent(TurnEvent(
                self.players[self.turn_player].connection.id, "play" if self.turn_has_drawn else "draw"))

    def start(self):
        for client in self.players:
            client.connection.sendEvent(StartEvent([
                player.makeForClient(client is player) for player in self.players
            ], client.connection.id, [card.id for card in self.deck.cards], self.lobby))
        self.deal()
        self.notifyPlayersOfTurnState()

    def nextTurn(self):
        self.turn_player = (self.turn_player + 1) % len(self.players)
        self.turn_has_drawn = False
        self.notifyPlayersOfTurnState()

    def assertCurrentTurn(self, connection: 'lobby.Connection'):
        assert self.players[self.turn_player].connection is connection
