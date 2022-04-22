from random import shuffle
from secrets import choice
from typing import Union
from uuid import uuid4

import funlib
import lobby
from protocol import *

# This file should contain all classes created by Super Rummy.

games: dict[str, "Game"] = {}


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
        self.cards = funlib.newDeck(num_decks, 2 * num_decks if jokers else 0)

    @classmethod
    def of(cls, cards: list[ServerCard]):
        stack = cls(0, False)
        stack.cards = cards
        return stack

    def top(self):
        return self.cards[-1] if len(self.cards) > 0 else None

    def assertedTop(self):
        assert len(self.cards) > 0
        return self.cards[-1]

    def reshuffle(self):
        shuffle(self.cards)
        for i in range(len(self.cards)):
            self.cards[i].id = uuid4().hex

    def remove(self, cards: list[ServerCard]):
        for card in cards:
            if card in self.cards:
                self.cards.remove(card)

    def insert(self, cards: list[ServerCard], position: int):
        self.remove(cards)
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

    def skipTurn(self, game: 'Game'):
        if game.turn_has_drawn:
            cards = self.hand.cards.copy()
            if game.non_discardable_card is not None:
                try:
                    cards.remove(game.non_discardable_card)
                except Exception:
                    pass
            game.moveCardsToDiscard([choice(cards)], self.hand)
            game.nextTurn()
        else:
            card = game.deck.assertedTop()
            game.moveCardsToHand(
                [card], game.deck, self, self.getDestinationHandPosition(card, game.settings))
            game.moveCardsToDiscard([choice(self.hand.cards)], self.hand)
            game.nextTurn()


class BoardAIPlayer():
    def __init__(self, lobbyPlayer: 'lobby.AILobbyPlayer'):
        self.hand = Stack(0, False)
        self.profile = lobbyPlayer

    def getDestinationHandPosition(self, card: ServerCard, settings: GameSettings):
        for i in range(len(self.hand.cards)):
            if card.isSortedBefore(self.hand.cards[i], settings):
                return i
        return len(self.hand.cards)

    def makeForClient(self):
        return ClientPlayer(self.profile.name, self.profile.id, [card.makeForClient(False) for card in self.hand.cards], False)

    def canEmptyHand(self, game: 'Game'):
        hand = Stack.of(self.hand.cards.copy())
        melds = [Stack.of(meld.cards.copy()) for meld in game.melds]
        # find the next "best" meld to play
        # melds are prioritized that use fewer wilds
        meld = funlib.findNextMeld(hand.cards, game.settings, None)
        while meld is not None:
            hand.remove(meld)
            melds.append(Stack.of(meld))
            meld = funlib.findNextMeld(hand.cards, game.settings, None)

        # after we've played all melds, we try to lay onto existing ones
        # the "preferred" lay will start with runs, then sets
        # wilds will be used if possible
        cardToLay, meldIndex = funlib.findNextPreferredLay(
            hand.cards, melds, game.settings, None)
        while cardToLay is not None and meldIndex is not None and (not game.settings.require_end_discard or len(hand.cards) > 1):
            newMeld = funlib.sortStack(
                [hand.cards[cardToLay]] + melds[meldIndex].cards, game.settings)
            hand.remove(newMeld)
            melds[meldIndex].cards = newMeld
            cardToLay, meldIndex = funlib.findNextPreferredLay(
                hand.cards, melds, game.settings, None)
        return len(hand.cards) == 0

    def takeTurn(self, game: 'Game'):
        print(f"{self.profile.name}'s hand:")
        funlib.printCards(self.hand.cards)
        # TODO: AI doesn't currently take into account how close it is to laying a card (only making a new meld) when drawing or discarding
        discardTop = game.discard.top()
        drawnFrom = game.deck
        drawnCard = game.deck.assertedTop()
        cannotDiscard: Optional[ServerCard] = None
        if discardTop is not None and not self.canEmptyHand(game):
            # check if the discard pile's card is helpful to us
            print("Discard pile:")
            funlib.printCards([discardTop])

            # if the discard pile forms a new meld with our cards, we take it
            # otherwise, if it forms a new meld with our cards plus a wild (indicating it pairs with our card), we also take it
            # if neither of these apply, we just draw from the deck
            # if we draw from the discard pile, we also need to remember that we're not allowed to discard it again
            meldsWithDiscard = len(funlib.findMelds(
                self.hand.cards + [discardTop], game.settings, cannotDiscard))
            meldsWithoutDiscard = len(funlib.findMelds(
                self.hand.cards, game.settings, cannotDiscard))
            doublesWithDiscard = len(funlib.findMelds(
                self.hand.cards + [discardTop, ServerCard(CardFace("joker", "W"))], game.settings, cannotDiscard))
            doublesWithoutDiscard = len(funlib.findMelds(
                self.hand.cards + [ServerCard(CardFace("joker", "W"))], game.settings, cannotDiscard))
            print(
                f'Discard potential: \x1b[1m{meldsWithDiscard}\x1b[0m > {meldsWithoutDiscard} or \x1b[1m{doublesWithDiscard}\x1b[0m > {doublesWithoutDiscard}')
            if meldsWithDiscard > meldsWithoutDiscard or doublesWithDiscard > doublesWithoutDiscard:
                print("Drawing from discard pile")
                drawnCard = discardTop
                drawnFrom = game.discard
                cannotDiscard = drawnCard

        print("After drawing:")
        funlib.printCards(self.hand.cards)

        # draw the chosen card
        game.moveCardsToAIHand(
            [drawnCard], drawnFrom, self, self.getDestinationHandPosition(drawnCard, game.settings))

        # find the next "best" meld to play
        # melds are prioritized that use fewer wilds
        meld = funlib.findNextMeld(
            self.hand.cards, game.settings, cannotDiscard)
        while meld is not None:
            game.moveCardsToMeld(meld, self.hand, len(game.melds), 0)
            meld = funlib.findNextMeld(
                self.hand.cards, game.settings, cannotDiscard)

        # after we've played all melds, we try to lay onto existing ones
        # the "preferred" lay will start with runs, then sets
        # wilds will be used if possible
        cardToLay, meldIndex = funlib.findNextPreferredLay(
            self.hand.cards, game.melds, game.settings, cannotDiscard)
        while cardToLay is not None and meldIndex is not None and (not game.settings.require_end_discard or len(self.hand.cards) > 1):
            newMeld = funlib.sortStack(
                [self.hand.cards[cardToLay]] + game.melds[meldIndex].cards, game.settings)
            game.moveCardsToMeld(newMeld, self.hand,
                                 meldIndex, 0)
            cardToLay, meldIndex = funlib.findNextPreferredLay(
                self.hand.cards, game.melds, game.settings, cannotDiscard)

        # if our hand is empty, the game is over
        if game.checkGameOver():
            return

        # choose which card to discard
        discardRank = [
            *filter(lambda c: c is not cannotDiscard, self.hand.cards)]  # filter out the card we cannot discard
        # first we sort by rank (highest rank first)
        # this will act as a tiebreaker for the next sort
        discardRank.sort(key=lambda x: -funlib.rankValue(x, game.settings))

        ranks: dict[str, int] = {}
        for card in discardRank:
            ranks[card.id] = 0
        # each card is "ranked" by how many times it appears in a meld if we were to add a wild to our hand
        # more melds means it's more likely that we'll want to keep that card
        for meld in funlib.findMelds(self.hand.cards + [ServerCard(CardFace("joker", "W"))], game.settings, None):
            for card in meld:
                if card.id in ranks:
                    ranks[card.id] = ranks[card.id] + 1
        discardRank.sort(key=lambda x: ranks[x.id])

        print("Discard ranking:")
        funlib.printCards(discardRank)

        # discard the chosen card and advance the game
        game.moveCardsToDiscard([discardRank[0]], self.hand)
        if not game.checkGameOver():
            game.nextTurn()


class Game:
    def __init__(self, l: 'lobby.Lobby'):
        self.lobby = l.code
        self.settings = l.settings
        games[self.lobby] = self
        self.deck = Stack(l.settings.deck_count, l.settings.enable_jokers)
        self.discard = Stack(0, False)
        self.players: list["BoardPlayer"] = [BoardPlayer(
            lobby.connections[player]) for player in l.connections]
        self.aiPlayers = [BoardAIPlayer(player) for player in l.aiPlayers]
        self.melds: list[Stack] = []
        self.turn_player: int = 0  # TODO: respect settings.first_turn
        self.turn_has_drawn: bool = False
        self.non_discardable_card: Optional[ServerCard] = None

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

    def moveCardsToAIHand(self, cards: list[ServerCard], originalStack: Stack, player: BoardAIPlayer, destPosition: int):
        originalStack.remove(cards)
        destPosition = min(max(destPosition, 0), len(player.hand.cards))
        for client in self.players:
            client.connection.sendEvent(MoveEvent([
                card.makeForClient(False) for card in cards
            ], MoveDestinationPlayer(player.profile.id, destPosition)))
        player.hand.insert(cards, destPosition)

    def moveCardsToMeld(self, cards: list[ServerCard], originalStack: Stack, meldNumber: int, destPosition: int):
        originalStack.remove(cards)
        meldNumber = min(max(meldNumber, 0), len(self.melds))
        if (meldNumber > len(self.melds) - 1):
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
                assert card is not None
                self.moveCardsToHand(
                    [card], self.deck, player, player.getDestinationHandPosition(card, self.settings))
            for player in self.aiPlayers:
                card = self.deck.top()
                assert card is not None
                self.moveCardsToAIHand(
                    [card], self.deck, player, player.getDestinationHandPosition(card, self.settings))
        discard = self.deck.top()
        assert discard is not None
        self.moveCardsToDiscard([discard], self.deck)

    def notifyPlayersOfTurnState(self):
        if (self.turn_player < len(self.players)):
            # it's a human player's turn
            for client in self.players:
                client.connection.sendEvent(TurnEvent(
                    self.players[self.turn_player].connection.id, "play" if self.turn_has_drawn else "draw"))
        else:
            # it's an AI player's turn
            for client in self.players:
                client.connection.sendEvent(TurnEvent(
                    self.aiPlayers[self.turn_player - len(self.players)].profile.id, "play" if self.turn_has_drawn else "draw"))

    def start(self):
        for client in self.players:
            # send a start event notifying all players that the game is starting
            client.connection.sendEvent(StartEvent([
                player.makeForClient(client is player) for player in self.players
            ] + [
                player.makeForClient() for player in self.aiPlayers
            ], client.connection.id, [card.id for card in self.deck.cards], self.lobby, self.settings))

        # deal out the cards
        self.deal()
        # kick off the first turn
        self.notifyPlayersOfTurnState()

    def redeck(self):
        if self.settings.deck_exhaust == "end_round" or len(self.discard.cards) == 0:
            self.end(None)
            # returning False here is how the caller (nextTurn()) knows that the game is over
            return False
        elif self.settings.deck_exhaust == "flip_discard":

            # take the discard pile, reverse it ("flipping it"), and set it as the new deck
            self.deck.cards = self.discard.cards
            self.deck.cards.reverse()
            self.discard.cards = []

            # reassign new IDs to the cards in the deck, to obscure the order of the cards
            for card in self.deck.cards:
                card.id = uuid4().hex

            # send the new card IDs to the client
            for client in self.players:
                client.connection.sendEvent(RedeckEvent(
                    [card.id for card in self.deck.cards]))

            # flip the top card to start the discard pile
            discard = self.deck.top()
            assert discard is not None
            self.moveCardsToDiscard([discard], self.deck)

            return True
        elif self.settings.deck_exhaust == "shuffle_discard":

            # take the discard pile, shuffle it, and set it as the new deck
            self.deck.cards = self.discard.cards
            shuffle(self.deck.cards)
            self.discard.cards = []

            # reassign new IDs to the cards in the deck, to obscure the order of the cards
            for card in self.deck.cards:
                card.id = uuid4().hex

            # send the new card IDs to the client
            for client in self.players:
                client.connection.sendEvent(RedeckEvent(
                    [card.id for card in self.deck.cards]))

            # flip the top card to start the discard pile
            discard = self.deck.top()
            assert discard is not None
            self.moveCardsToDiscard([discard], self.deck)

            return True

    def end(self, winnerID: Optional[str]):
        # TODO: if settings.lay_at_end is enabled, automatically all possible cards to minimize hand scores
        event = EndEvent(winnerID, {
            player.connection.id: sum(funlib.scoreValue(card, self.settings) for card in player.hand.cards) for player in self.players
        } | {
            player.profile.id: sum(funlib.scoreValue(card, self.settings) for card in player.hand.cards) for player in self.aiPlayers
        })
        for client in self.players:
            client.connection.sendEvent(event)

        # deleting the games entry stops player actions from being processed as game actions
        del games[self.lobby]

        # sending a lobby event updates clients on what players are still in the lobby for the next round
        if self.lobby in lobby.lobbies:
            lobby.lobbies[self.lobby].informPlayersOfLobby()

    def checkGameOver(self):
        winner = None
        for player in self.players:
            if len(player.hand.cards) == 0:
                winner = player
                break
        if winner is not None:
            self.end(winner.connection.id)
            return True
        for player in self.aiPlayers:
            if len(player.hand.cards) == 0:
                winner = player
                break
        if winner is not None:
            self.end(winner.profile.id)
            return True
        return False

    def nextTurn(self):

        # count how many human players are still connected
        connectedPlayers = 0
        for player in self.players:
            if player.connection.id in lobby.connections:
                connectedPlayers += 1

        # if there are no human players left, or if there are less than two active (connected or AI) players, end the round
        if connectedPlayers == 0 or connectedPlayers + len(self.aiPlayers) < 2:
            self.end(None)
            return

        # if the deck is exhausted, flip or resuffle the deck according to the game settings
        if len(self.deck.cards) == 0:
            if not self.redeck():
                return

        # increment the turn counter, wrapping around at the end (once we've gone through all AI and human players)
        self.turn_player = (self.turn_player +
                            1) % (len(self.players) + len(self.aiPlayers))

        # set game state to the beginning of a turn
        self.turn_has_drawn = False
        self.non_discardable_card = None

        # send a message to all clients notifying them of the current turn state
        self.notifyPlayersOfTurnState()

        # turns start with players, then AI, so low self.turn_player indicates a player turn
        if (self.turn_player < len(self.players)):
            # a human player needs to take a turn
            if not self.players[self.turn_player].connection.id in lobby.connections:
                # skip this player if they have disconnected
                self.players[self.turn_player].skipTurn(self)
        else:
            # an AI player needs to take a turn
            self.aiPlayers[self.turn_player - len(self.players)].takeTurn(self)

    def removePlayer(self, playerID: str):
        # the player is still in the game, but no longer in the lobby (disconnected)
        # if they were currently playing a turn, skip to the next player
        if (self.turn_player < len(self.players)):
            if (self.players[self.turn_player].connection.id == playerID):
                self.players[self.turn_player].skipTurn(self)

    def assertCurrentTurn(self, connection: 'lobby.Connection'):
        assert self.turn_player < len(
            self.players) and self.players[self.turn_player].connection is connection
