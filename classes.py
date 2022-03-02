import funlib

# This file should contain all classes created by Super Rummy.


# Board
# The Board class will cover the state of the game.
# self.Players = a list of players, each of which contains point values and hand.
# self.deck = a stack of cards in the deck.
# self.discard = a stack of cards in the discard pile.
# self.melds = a 2d array of cards: melds[meld number][card-in-meld]
# self.settings = a thing just so that we don't have to ask what the rules are every 5 seconds,
#   if that ends up being inconvinient.

class Board():
    def __init__(self, players):
        self.players = players
        self.settings = Settings()
        self.deck = Deck(self.settings.decknum)
        self.discard = Deck(self.settings.decknum, True)
        self.melds = []

    # this just runs the entire game.

    def game(self):
        while(not self.gameOver()):
            self.startRound()

            while(not self.roundOver()):
                for i in range(len(self.players)):
                    self.takeTurn(self.players[i])

            self.endRound()
        return True

    # start game will shuffle the deck(s), deal them out, then put a card on the discard pile.

    def startRound(self):
        # reset / shuffle the deck
        self.deck = Deck(self.settings.decknum)
        self.deck = self.deck.shuffle()

        # reset hands / deal the cards
        for i in range(len(self.players)):
            self.players[i].hand = []
            for j in range(self.settings.handsize):
                self.players[i].hand.append(self.deck.pop())

        # reset / put the top card in discard
        self.discard.deck = Deck(self.settings.decknum, True)
        self.discard.push(self.deck.pop())

    # roundOver returns true if someone's hand is empty, otherwise return false.
    def roundOver(self):
        for i in range(len(self.players)):
            if(len(self.players[i].hand) == 0):
                return True
        return False

    # add everyone's score to their score count.
    def endRound(self):
        for i in range(len(self.players)):
            for j in range(len(self.players[i].hand)):
                self.players[i].score += self.players.hand[j].val

    # checks to see whether anyone has enough points to win.
    def gameOver(self):
        for i in range(len(self.players)):
            if(self.players[i].score >= self.settings.endscore):
                return True
        return False

    # this is the main "player taking their turn" function.
    def takeTurn(self, player):
        # Draw a card from the deck or discard pile

        # spend as long as you want selecting / deselecting cards

        # play any potential melds

        # discard a card

        return True


class Deck():

    # self.deck is an array of cards.
    # self.top is the index of the top card in the stack.
    # self.empty is whether or not it's empty
    # discard is just used at the start to determine whether it's the discard pile or the deck.
    def __init__(self, decks, discard=False):
        if discard:
            self.deck = [None] * 54 * decks
            self.top = 54 * decks - 1
            self.empty = True
        else:
            self.deck = funlib.newDeck(decks)
            self.top = 0
            self.empty = False

    def pop(self):
        if(not self.empty):
            retval = self.deck[self.top]
            if(self.top == len(self.deck)-1):
                self.empty = True
            else:
                self.top += 1
        else:
            retval = "Empty"
        return retval

    def shuffle(self):
        retval = self.deck
        # make retval a randomly organized version of self.deck
        return retval

    # just a get function, because self.top is an index, but deck.top() will be top card.
    def top(self):
        return self.deck[self.top]

    # adds card to the top of the deck. this should only happen to discard piles.
    def push(self, card):
        if(self.top == 0):
            return "Full?"
        else:
            self.top -= 1
            self.deck[self.top] = card


# Player
# self.hand = an array of cards in that player's hand.
# self.selected = an array of which cards that player has selected.
# self.score = that player's score so far in the game. Only updated at the end of each round.

class Player():
    def __init__(self):
        self.hand = []
        self.selected = []
        self.score = 0

# Cards
# This class will contain each card's information.
# self.id = an integer to keep track of it, somewhere between 0 and (number of decks * 52) -1
# self.num = a char to determine what should show up. A for ace, 2-9, 0 for 10,
#   J, Q, K, for face cards, W for joker / wild card.
# self.suit = a string to determine suit.
#   the "four" suits are spades, clubs, hearts, diamonds, and jokers.
# val = the point value of the card. numbers are worth that many points, J, Q, K are all 10
#   A is either 1 or 11. I've seen it both ways. W is 20.


class Card():
    def __init__(self, id=0, num='A', suit="spades", val=11):
        self.id = id
        self.num = num
        self.suit = suit
        self.val = val

    # True if this card is a joker.
    def isJoker(self):
        return self.suit == "joker"

    # Returns a number from 1 to 13 (A to K). Joker returns 0
    def toNum(self):
        if(self.num == 'A'):
            return 1
        if(self.num == '0'):
            return 10
        if(self.num == 'J'):
            return 11
        if(self.num == 'Q'):
            return 12
        if(self.num == 'K'):
            return 13
        if(self.num == 'W'):
            return 0
        else:
            return int(self.num)


# really this is just a placeholder for the actual implementation of the settings that we do.
class Settings():
    def __init__(self) -> None:
        self.endscore = 200
        self.decknum = 2
        self.handsize = 14
