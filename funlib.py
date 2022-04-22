from copy import copy
from functools import reduce
from random import shuffle
from uuid import uuid4

import classes
from protocol import CardFace, CardRank, GameSettings

# this just returns one or more decks, shuffled.


def sortStack(cards: list['classes.ServerCard'], settings: GameSettings):
    cards.sort(key=lambda card: card.face.suit)
    cards.sort(key=lambda card: rankValue(card, settings))
    return cards


def printCards(cards: list['classes.ServerCard']):
    print(" - " + " ".join([{
        "joker": "\x1b[1;34m",
        "hearts": "\x1b[1;31m",
        "diamonds": "\x1b[1;31m",
        "spades": "\x1b[1m",
        "clubs": "\x1b[1m",
    }[card.face.suit] + card.face.rank + {
        "joker": "✦",
        "hearts": "♥",
        "diamonds": "♦",
        "spades": "♠",
        "clubs": "♣",
    }[card.face.suit] + "\x1b[0m" for card in cards]))


def findRuns(cards: list['classes.ServerCard'], settings: GameSettings):
    nonWilds = [card for card in cards if card.face.rank != "W"]
    wilds = [card for card in cards if card.face.rank == "W"]
    buckets = {}
    for card in nonWilds:
        suit = "*" if settings.allow_run_mixed_suit else card.face.suit
        if suit not in buckets:
            buckets[suit] = []
        buckets[suit].append(card)
    runs: list[list['classes.ServerCard']] = []
    for suit in buckets:
        bucket = buckets[suit]
        bucket.sort(key=lambda card: rankValue(card, settings))
        if len(bucket) >= 3:
            for i in range(len(bucket)):
                run = [bucket[i]]
                availableWilds = len(wilds)
                for j in range(i + 1, len(bucket)):
                    if rankValue(bucket[j], settings) == rankValue(run[-1], settings):
                        continue
                    if rankValue(bucket[j], settings) > rankValue(run[-1], settings) and \
                            rankValue(bucket[j], settings) - rankValue(run[-1], settings) - 1 <= availableWilds:
                        for k in range(rankValue(bucket[j], settings) - rankValue(run[-1], settings) - 1):
                            run.append(wilds[-availableWilds])
                            availableWilds -= 1
                        run.append(bucket[j])
                    else:
                        break
                if len(run) + availableWilds >= 3:
                    for j in range(3 - len(run)):
                        run.append(wilds[-availableWilds])
                        availableWilds -= 1
                    runs.append(sortStack(run, settings))
    return runs


def findSets(cards: list['classes.ServerCard'], settings: GameSettings):
    nonWilds = [card for card in cards if card.face.rank != "W"]
    wilds = [card for card in cards if card.face.rank == "W"]
    buckets = {}
    for card in nonWilds:
        if card.face.rank not in buckets:
            buckets[card.face.rank] = []
        buckets[card.face.rank].append(card)
    sets: list[list['classes.ServerCard']] = []
    availableWilds = len(wilds)
    for rank in buckets:
        bucket = sortStack(buckets[rank], settings)
        if len(bucket) >= 3:
            sets.append(bucket)
        # only add wilds to sets of 2 or more, since a lone card will be caught by findRun as a run of 3 with two wilds
        # this isn't strictly necessary, but it prevents duplicate melds being found
        if availableWilds > 0 and len(bucket) >= 2 and len(bucket) + availableWilds >= 3:
            if len(bucket) < 3 and len(bucket) + availableWilds > 3:
                sets.append(
                    sortStack(bucket + wilds[:3 - len(bucket)], settings))
            sets.append(sortStack(bucket + wilds, settings))
    if availableWilds >= 3:
        sets.append(wilds)
    return sets


def findLays(card: 'classes.ServerCard', melds: list['classes.Stack'], settings: GameSettings, runsOnly: bool):
    indexes: list[int] = []
    for i in range(len(melds)):
        meld = melds[i]
        if card.face.rank == "W":
            indexes.append(i)
            continue
        if checkLegal(meld.cards + [card], settings) and (not runsOnly or checkRun(meld.cards + [card], settings)):
            indexes.append(i)
            continue
    return indexes


def findNextPreferredLay(cards: list['classes.ServerCard'], melds: list['classes.Stack'], settings: GameSettings):
    if len(melds) == 0:
        return None, None

    # first look for runs that don't involve jokers
    for i in range(len(cards)):
        if cards[i].face.suit == "joker":
            continue
        lays = findLays(cards[i], melds, settings, True)
        if len(lays) > 0:
            return i, lays[0]

    # if there are no runs, find sets that don't involve jokers
    for i in range(len(cards)):
        if cards[i].face.suit == "joker":
            continue
        lays = findLays(cards[i], melds, settings, False)
        if len(lays) > 0:
            return i, lays[0]

    # if there are no sets or runs without jokers, find runs that involve jokers
    for i in range(len(cards)):
        if cards[i].face.suit != "joker":
            continue
        lays = findLays(cards[i], melds, settings, True)
        if len(lays) > 0:
            return i, lays[0]

    # finally, find sets that involve jokers
    for i in range(len(cards)):
        if cards[i].face.suit != "joker":
            continue
        lays = findLays(cards[i], melds, settings, False)
        if len(lays) > 0:
            return i, lays[0]

    return None, None


def nonWildCards(cards: list['classes.ServerCard']):
    return len([card for card in cards if card.face.rank != "W"])


def canWinWith(meld: list['classes.ServerCard'], totalCards: int, settings: GameSettings):
    winLength = totalCards - 1
    return len(meld) >= winLength and (not settings.require_end_discard or len(meld) > 3 or winLength == 3)


def findMelds(cards: list['classes.ServerCard'], settings: GameSettings):
    maxLength = len(cards) - 1 if settings.require_end_discard else len(cards)
    melds = findRuns(cards, settings) + findSets(cards, settings)
    melds = [*filter(lambda meld: (nonWildCards(meld) >= 2 or canWinWith(meld,
                     len(cards), settings)) and len(meld) <= maxLength, melds)]

    # least important, sort by least number of wild cards
    melds.sort(key=lambda meld: len(meld) - nonWildCards(meld))
    # most important, sort by highest number of non-wild cards
    melds.sort(key=lambda meld: -nonWildCards(meld))
    # naturally, the least important of all will be to sort runs before sets (since they're assigned that way)
    return melds


def findNextMeld(cards: list['classes.ServerCard'], settings: GameSettings):
    melds = findMelds(cards, settings)
    print("Current melds:")
    for meld in melds:
        printCards(meld)
    if len(melds) == 0:
        return None
    return melds[0]


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
