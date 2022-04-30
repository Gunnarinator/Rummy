import sys
sys.path.append("../")
sys.path.append("./")
import app

from funlib import *
from classes import *
import unittest
import logging
from typing import Literal

logger = logging.getLogger()
logger.level = logging.DEBUG
stream_handler = logging.StreamHandler(sys.stdout)


def enableLogging():
    logger.addHandler(stream_handler)


def disableLogging():
    logger.removeHandler(stream_handler)


def c(cards: list[Literal[
    "AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS",
    "AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH",
    "AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD",
    "AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC",
    "WJ"
]]):
    return [ServerCard(CardFace({
        "S": "spades",
        "H": "hearts",
        "D": "diamonds",
        "C": "clubs",
        "J": "joker"
    }[card[-1]], card[:-1])) for card in cards]  # type: ignore


def legal(cards: list[Literal[
    "AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS", "QS", "KS",
    "AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH", "QH", "KH",
    "AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD", "QD", "KD",
    "AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC", "QC", "KC",
    "WJ"
]], settings: GameSettings):
    return checkLegal(c(cards), settings)


class TestRules(unittest.TestCase):

    normalRules = GameSettings(
        ace_rank="low", allow_set_duplicate_suit=False, limit_meld_size=None, allow_run_mixed_suit=False)
    aceHighRules = GameSettings(
        ace_rank="high"
    )
    dupSetRules = GameSettings(
        allow_set_duplicate_suit=True, limit_meld_size=None)
    mixedRunRules = GameSettings(
        allow_run_mixed_suit=True, limit_meld_size=None)
    limit3Rules = GameSettings(
        allow_set_duplicate_suit=False, limit_meld_size=3)
    limit4Rules = GameSettings(
        allow_set_duplicate_suit=True, limit_meld_size=4)

    def test_legal_normalSet(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "AD"], self.normalRules))

    def test_legal_middleSet(self: 'TestRules'):
        self.assertTrue(legal(["8S", "8H", "8D"], self.normalRules))

    def test_legal_wildSet(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "WJ"], self.normalRules))

    def test_legal_3Wilds(self: 'TestRules'):
        self.assertTrue(legal(["WJ", "WJ", "WJ"], self.normalRules))

    def test_illegal_mixed3(self: 'TestRules'):
        self.assertFalse(legal(["AS", "2H", "5D"], self.normalRules))

    def test_illegal_smallSet(self: 'TestRules'):
        self.assertFalse(legal(["AH", "AS"], self.normalRules))

    def test_illegal_1Card1Wild(self: 'TestRules'):
        self.assertFalse(legal(["AH", "WJ"], self.normalRules))

    def test_illegal_2Wilds(self: 'TestRules'):
        self.assertFalse(legal(["WJ", "WJ"], self.normalRules))

    def test_illegal_4SetAndWild(self: 'TestRules'):
        self.assertFalse(
            legal(["AS", "AH", "AD", "AC", "WJ"], self.normalRules))

    def test_legal_4Set(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "AD", "AC"], self.normalRules))

    def test_legal_3Set2(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "AD"], self.dupSetRules))

    def test_legal_4Set2(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "AD", "AC"], self.dupSetRules))

    def test_illegal_dupSet(self: 'TestRules'):
        self.assertFalse(legal(["AS", "AD", "AD"], self.normalRules))

    def test_legal_limitSet3(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AH", "AD"], self.limit3Rules))

    def test_illegal_setOverLimit(self: 'TestRules'):
        self.assertFalse(legal(["AS", "AD", "AD", "AC"], self.limit3Rules))

    def test_legal_limitSet4(self: 'TestRules'):
        self.assertTrue(legal(["AS", "AD", "AD", "AC"], self.limit4Rules))

    def test_illegal_setOverLimit4(self: 'TestRules'):
        self.assertFalse(
            legal(["AS", "AD", "AD", "AC", "AC"], self.limit4Rules))

    def test_legal_normalRun(self: 'TestRules'):
        self.assertTrue(legal(["5S", "6S", "7S"], self.normalRules))
        self.assertTrue(legal(["5H", "6H", "7H"], self.normalRules))
        self.assertTrue(legal(["5D", "6D", "7D"], self.normalRules))
        self.assertTrue(legal(["5C", "6C", "7C"], self.normalRules))

    def test_legal_aceLowRun(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2S", "3S"], self.normalRules))

    def test_legal_aceHighRun(self: 'TestRules'):
        self.assertTrue(legal(["QS", "KS", "AS"], self.aceHighRules))

    def test_legal_shuffledSet(self: 'TestRules'):
        self.assertTrue(legal(["AS", "3S", "2S"], self.normalRules))

    def test_legal_mixedRun(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2D", "3H"], self.mixedRunRules))

    def test_legal_mixedRun2(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2D", "3S"], self.mixedRunRules))

    def test_legal_wildRun(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2S", "WJ"], self.normalRules))

    def test_illegal_smallRun(self: 'TestRules'):
        self.assertFalse(legal(["2S", "3S"], self.normalRules))

    def test_legal_run2Wilds(self: 'TestRules'):
        self.assertTrue(legal(["8S", "WJ", "WJ"], self.normalRules))

    def test_legal_maxRun(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2S", "3S", "4S", "5S", "6S", "7S",
                        "8S", "9S", "10S", "JS", "QS", "KS"], self.normalRules))

    def test_illegal_overflowRunWild(self: 'TestRules'):
        self.assertFalse(legal(["AS", "2S", "3S", "4S", "5S", "6S", "7S",
                         "8S", "9S", "10S", "JS", "QS", "KS", "WJ"], self.normalRules))

    def test_legal_maxRunWild(self: 'TestRules'):
        self.assertTrue(legal(["AS", "2S", "3S", "4S", "5S", "7S", "8S",
                        "9S", "10S", "JS", "QS", "KS", "WJ"], self.normalRules))

    def test_legal_limit3Run(self: 'TestRules'):
        self.assertTrue(legal(["4S", "5S", "6S"], self.limit3Rules))

    def test_legal_limit4Run(self: 'TestRules'):
        self.assertTrue(legal(["4S", "5S", "6S", "7S"], self.limit4Rules))

    def test_illegal_overflowRun(self: 'TestRules'):
        self.assertFalse(
            legal(["4S", "5S", "6S", "7S", "8S"], self.limit4Rules))


def compare(cards: list[ServerCard], target: list[ServerCard], silent: bool = False):
    sortStack(cards, GameSettings())
    sortStack(target, GameSettings())
    ok = True
    if len(cards) != len(target):
        ok = False
    else:
        for i in range(len(cards)):
            if cards[i].face.rank != target[i].face.rank:
                ok = False
            elif cards[i].face.suit != target[i].face.suit:
                ok = False
    if not ok:
        if not silent:
            enableLogging()
            print("\nActual:")
            printCards(cards)
            print("Expected:")
            printCards(target)
            disableLogging()
        raise AssertionError("Cards don't match")


def compareAll(stacks: list[list[ServerCard]], target: list[list[ServerCard]]):
    matched: set[int] = set()
    if len(stacks) != len(target):
        enableLogging()
        print("\nActual:")
        if len(stacks) > 0:
            for s in stacks:
                printCards(s)
        else:
            print("(none)")
        print("Expected:")
        if len(target) > 0:
            for s in target:
                printCards(s)
        else:
            print("(none)")
        disableLogging()
        raise AssertionError("Cards don't match")
    for stack in stacks:
        ok = False
        for t in range(len(target)):
            if t in matched:
                continue
            try:
                compare(stack, target[t], True)
                matched.add(t)
                ok = True
            except AssertionError:
                pass
        if not ok:
            enableLogging()
            print("\nActual:")
            if len(stacks) > 0:
                for s in stacks:
                    printCards(s)
            else:
                print("(none)")
            print("Expected:")
            if len(target) > 0:
                for s in target:
                    printCards(s)
            else:
                print("(none)")
            disableLogging()
            raise AssertionError("Cards don't match")


class TestAILogic(unittest.TestCase):
    rules = GameSettings(
        allow_run_mixed_suit=False, allow_set_duplicate_suit=False, limit_meld_size=None, require_end_discard=False)
    discardReqiredRules = GameSettings(
        allow_run_mixed_suit=False, allow_set_duplicate_suit=False, limit_meld_size=None, require_end_discard=True)
    limitedRules = GameSettings(
        allow_run_mixed_suit=False, allow_set_duplicate_suit=False, limit_meld_size=4, require_end_discard=False)

    def test_canWin(self: 'TestAILogic'):
        self.assertTrue(canWinWith(c(["AH", "AD", "AC", "AS"]), 4, self.rules))

    def test_cannotWin_discardRequired(self: 'TestAILogic'):
        self.assertFalse(canWinWith(
            c(["AH", "AD", "AC", "AS"]), 4, self.discardReqiredRules))

    def test_cannotWin(self: 'TestAILogic'):
        self.assertFalse(canWinWith(c(["AH", "AD", "AC"]), 5, self.rules))

    def test_canWin_discardRequired(self: 'TestAILogic'):
        self.assertTrue(canWinWith(
            c(["AH", "AD", "AC"]), 4, self.discardReqiredRules))

    def test_findMelds(self: 'TestAILogic'):
        compareAll(findMelds(c(["AH", "AD", "AC", "AS", "9D", "3S", "4S", "5S", "WJ"]), self.rules, None), [
            c(["AH", "AD", "AC", "AS"]),
            c(["AH", "AD", "AC", "AS", "WJ"]),
            c(["AS", "WJ", "3S", "4S", "5S"]),
            c(["3S", "4S", "5S"]),
            c(["4S", "5S", "WJ"])
        ])

    def test_findMelds_wild(self: 'TestAILogic'):
        compareAll(findMelds(c(["AH", "WJ", "WJ", "WJ"]), self.rules, None), [
            c(["AH", "WJ", "WJ"]),
            c(["WJ", "WJ", "WJ"])
        ])

    def test_findMelds_allWild(self: 'TestAILogic'):
        compareAll(findMelds(c(["WJ", "WJ", "WJ", "WJ"]), self.rules, None), [
            c(["WJ", "WJ", "WJ"]),
            c(["WJ", "WJ", "WJ", "WJ"])
        ])

    def test_findLay_run(self: 'TestAILogic'):
        cards = c(["2C", "8H", "3H", "4S"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["AS", "2S", "3S"]))
                                    ], self.rules, None)
        self.assertIsNotNone(i)
        compare([cards[i]], c(["4S"]))  # type: ignore

    def test_findLay_set(self: 'TestAILogic'):
        cards = c(["2C", "8H", "3H", "4S"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, None)
        self.assertIsNotNone(i)
        compare([cards[i]], c(["4S"]))  # type: ignore

    def test_findLay_ignoreWild(self: 'TestAILogic'):
        cards = c(["2C", "8H", "3H", "WJ"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, None)
        self.assertIsNone(i)

    def test_findLay_wild_win(self: 'TestAILogic'):
        cards = c(["3H", "WJ"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, cards[1])
        self.assertIsNotNone(i)
        compare([cards[i]], c(["WJ"]))  # type: ignore

    def test_findLay_wild_only(self: 'TestAILogic'):
        cards = c(["WJ"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, None)
        self.assertIsNotNone(i)
        compare([cards[i]], c(["WJ"]))  # type: ignore

    def test_findLay_discardTrap(self: 'TestAILogic'):
        cards = c(["3H", "4S"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, cards[0])
        self.assertIsNone(i)

    def test_findLay_discardTrap_wild(self: 'TestAILogic'):
        cards = c(["3H", "WJ"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.rules, cards[0])
        self.assertIsNone(i)

    def test_findLay_winTrap(self: 'TestAILogic'):
        cards = c(["4S"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.discardReqiredRules, None)
        self.assertIsNone(i)

    def test_findLay_winTrap_wild(self: 'TestAILogic'):
        cards = c(["WJ"])
        i, _ = findNextPreferredLay(cards,
                                    [
                                        Stack.of(c(["4C", "4H", "4D"]))
                                    ], self.discardReqiredRules, None)
        self.assertIsNone(i)


if __name__ == '__main__':
    unittest.main(verbosity=2)
