from random import shuffle
from uuid import uuid4

import classes
from protocol import CardFace, CardRank

# this just returns one or more decks, shuffled.


def newDeck(decks: int = 1, jokers: int = 0):
    retval: list[classes.ServerCard] = []
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
# Aces are high or low, but not both. i.e. A, 2, 3 is legal, and Q, K, A is legal, but K, A, 2 is not.
def checkLegal(cards, meld=[]):
    # Check for length real quick
    if len(meld) < 3:
        return "Error: destination meld not long enough"
    if len(cards) + len(meld) < 3:
        return "Error: melds must be at least 3 cards long"

    # we're gonna use testmeld as a var when testing for sets/runs.
    testmeld = []
    for i in range(len(cards)):
        testmeld.append(cards[i])
    for i in range(len(meld)):
        testmeld.append(meld[i])

    set = checkSet(testmeld)
    run = checkRun(testmeld)


# checkSet(cards)
# cards is an array of cards that is hopefully a set.
# returns a bool for if cards is a set.
#
# look through all the cards. If any of them are different numbers or the same suit, return false.
# unless the offending card is a joker.
def checkSet(cards):
    num = ''
    suits = []

    # for each card, if it's a different number, return false
    for i in range(len(cards)):
        # we do need to know which number the set is tho
        if(num == '' and not cards[i].isjoker()):
            num = cards[i].num

        # if it's a different number, return false unless joker
        if(num != '' and cards[i].num != num):
            if(not cards[i].isjoker()):
                return "Error: All cards in a set must be the same number."

    # for each card, if it's suit has been represented already, return false.
    for i in range(len(cards)):
        # if that suit has been done already, return false.
        if(cards[i].suit in suits and not cards[i].isjoker()):
            return "Error: Each suit can only appear in a set once."
        else:
            suits.append(cards[i].suit)

        # if we get this far, it's a set.
        return "set"


# checkSet but for runs.
# cards is an array
# returns a bool for whether cards is a valid run or not.
def checkRun(cards):
    suit = ""
    nums = []

    # make sure all cards are the same suit.
    for i in range(len(cards)):
        # find out what suit the run is
        if(suit == "" and not cards[i].isjoker()):
            suit = cards[i].suit
        # if the card isn't the same suit (or a joker), kick it out.
        if(suit != "" and cards[i].suit != suit):
            if(not cards[i].isjoker()):
                return "Error: All cards in a run must be the same set."

    # now that we know the cards are all the same suit, we can make sure they're a run.
    # testcards is a copy of cards for us to remove stuff from
    # prevnum is the num of the card last removed from testcards.
    testcards = []
    for i in range(len(cards)):
        testcards.append(cards[i].val)
    prevcard = classes.Card()

    for i in range(len(cards)):
        nextcard = findMin(testcards)
        if(prevnum == 0):
            prevcard = removeMin(testcards)
        else:
            if(nextcard.val == prevnum.val + 1 or (prevnum.num == 'A' and nextcard.num == '2')):
                prevnum = nextcard
                removeMin(testcards)
            elif():
                removeJoker(testcards)
                prevnum.val += 1
                prevnum.num = nextNum(prevnum)
            else:
                return "Error: Each card in a run must be 1 greater than the last."

    return "run"


# removeMin removes the card in the array with the lowest value
def removeMin(cards):
    mincard = findMin(cards)
    cards.remove(mincard)
    return mincard


# remove joker removes the first joker from cards, then returns true.
# if there's no joker, it returns false.
def removeJoker(cards):
    for i in range(len(cards)):
        if(cards[i].num == 'W'):
            cards.remove(cards[i])
            return True
    return False

# findMin returns the card with the lowest value unless there's an ace.
# if there's an ace, it returns the ace if there


def findMin(cards):
    min = 20
    mindex = 0
    acepresent = False
    kingpresent = False
    twopresent = False
    acelow = False
    acedex = 0
    for i in range(len(cards)):
        val = cards[i].tonum
        if(val < min):
            mindex = i
            min = cards[i].val
        if(val == 2):
            twopresent = True
        if(val == 1):
            acepresent = True
            acedex = i
        if(val == 13):
            kingpresent = True
        if(twopresent and acepresent):
            acelow = True
    if(acelow):
        return cards[acedex]
    else:
        return cards[mindex]


# helper function for when runs have jokers.
# takes a card and returns the next num, i.e. 10->J, A->2, etc
def nextNum(card):
    # if it's 9-A, return the next thing
    if(card.num == '9'):
        return '0'
    elif(card.num == '0'):
        return 'J'
    elif(card.num == 'J'):
        return 'Q'
    elif(card.num == 'Q'):
        return 'K'
    elif(card.num == 'K'):
        return '2'
    elif(card.num == 'A'):
        return '2'
    # 2-8 are cool because the next number is also one digit so we have other functions for that.
    elif(card.num.isdigit()):
        return str(int(card.num)+1)
