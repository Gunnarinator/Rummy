from random import shuffle
from uuid import uuid4

import classes
from protocol import CardFace, CardRank, GameSettings

# this just returns one or more decks, shuffled.


def sortStack(cards: list['classes.ServerCard'], settings: GameSettings):
    cards.sort(key=lambda card: card.face.suit)
    cards.sort(key=lambda card: rankValue(card, settings))
    return cards


def newDeck(decks: int = 1, jokers: int = 0):
    retval: list['classes.ServerCard'] = []
    ranks: list[CardRank] = ["A", "2", "3", "4",
                             "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    for deck in range(decks):
        for s in range(4):
            if(s == 1):
                suit = "clubs"
            elif(s == 2):
                suit = "hearts"
            elif(s == 3):
                suit = "diamonds"
            else:
                suit = "spades"
            for n in range(13):
                rank: CardRank = ranks[n]
                retval.append(classes.ServerCard(CardFace(suit, rank)))
        id = deck*54 + 52
    for n in range(jokers):
        retval.append(classes.ServerCard(CardFace("joker", "W")))
    shuffle(retval)
    return retval


# this checks to see if a meld is legal
# the array of cards must be at least 3 long
# The array of cards must be a set or a run
# Sets are 3+ of the same card, in different suits
# Runs are 3+ in a row of the same suit, i.e. 3, 4, 5 of hearts or 10, J, Q of spades.
# Aces are high or low, according to the settings.
def checkLegal(cards: list['classes.ServerCard'], settings: GameSettings):
    # Check for length real quick
    if len(cards) < 3:
        return False
    if settings.limit_meld_size is not None and len(cards) > settings.limit_meld_size:
        return False

    return checkSet(cards, settings) or checkRun(cards, settings)


# checkSet(cards)
# cards is an array of cards that is hopefully a set.
# returns a bool for if cards is a set.
#
# look through all the cards. If any of them are different numbers or the same suit, return false.
# unless the offending card is a joker.
def checkSet(cards: list['classes.ServerCard'], settings: GameSettings):
    rank = None
    suits = []

    # for each card, if it's a different number, return false
    for i in range(len(cards)):
        # we do need to know which number the set is tho
        if (cards[i].face.rank != "W"):
            if rank is None:
                rank = cards[i].face.rank
            elif rank != cards[i].face.rank:
                return False

    # for each card, if it's suit has been represented already, return false.
    for i in range(len(cards)):
        # if that suit has been done already, return false.
        if(cards[i].face.suit in suits and not cards[i].face.suit == "joker"):
            return False
        else:
            suits.append(cards[i].face.suit)

    # if we get this far, it's a set.
    return True


def rankValue(card: 'classes.ServerCard', settings: GameSettings):
    if card.face.rank == "W":
        return -1
    elif card.face.rank == "J":
        return 11
    elif card.face.rank == "Q":
        return 12
    elif card.face.rank == "K":
        return 13
    elif card.face.rank == "A":
        if settings.ace_rank == "low":
            return 1
        else:
            return 14
    else:
        return int(card.face.rank)


def scoreValue(card: 'classes.ServerCard', settings: GameSettings):
    if card.face.rank == "W":
        return 15
    elif card.face.rank == "J":
        return 10
    elif card.face.rank == "Q":
        return 10
    elif card.face.rank == "K":
        return 10
    elif card.face.rank == "A":
        if settings.ace_rank == "low":
            return 1
        else:
            return 11
    else:
        return int(card.face.rank)

# checkSet but for runs.
# cards is an array
# returns a bool for whether cards is a valid run or not.


def checkRun(cards: list['classes.ServerCard'], settings: GameSettings):
    # filter out non-wild cards and sort by rank
    rankedCards = [card for card in cards if card.face.rank != "W"]
    rankedCards.sort(key=lambda card: rankValue(card, settings))
    if len(rankedCards) == 0:
        return True
    wilds = len(cards) - len(rankedCards)
    if not settings.allow_run_mixed_suit:
        # find out what suit the run is
        suit = rankedCards[0].face.suit
        # make sure all cards are the same suit.
        if any(card.face.suit != suit for card in rankedCards):
            return False
    # find out what the first rank is
    rank = rankValue(rankedCards[0], settings) - 1
    # check each card
    for card in rankedCards:
        nextRank = rankValue(card, settings)
        if nextRank - rank - 1 > wilds or nextRank <= rank:
            return False
        wilds -= nextRank - rank - 1
        rank = nextRank
    return True
