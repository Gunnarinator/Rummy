import { state } from "./index.js"

/**
 * @return {Card[]}
 */
function getSelectedCards() {
    if (state.type !== "game") return []
    return state.board.players
        .find(({ id }) => id === state.board.current_player_id).hand
        .filter(({ id }) => state.ui.selectedCardIDs.has(id))
}

/**
 * @return {boolean}
 */
export function canMeldSelectedCards() {
    if (state.type !== "game" || state.ui.selectedCardIDs.size == 0) return false
    if (state.board.settings.require_end_discard &&
        state.ui.selectedCardIDs.size == state.board.players
            .find(({ id }) => id === state.board.current_player_id).hand.length) return false
    let selectedCards = getSelectedCards()
    return isValidMeld(selectedCards)
}

/**
 * @return {number[]}
 */
export function getMeldsForLay() {
    if (state.type !== "game" || state.ui.selectedCardIDs.size == 0) return []
    if (state.board.settings.require_end_discard &&
        state.ui.selectedCardIDs.size == state.board.players
            .find(({ id }) => id === state.board.current_player_id).hand.length) return []
    let selectedCards = getSelectedCards()
    return [...state.board.melds.entries()]
        .filter(([, meld]) => isValidMeld(meld.concat(selectedCards)))
        .map(([index]) => index)
}

/**
 * @param {Card[]} cards
 * @return {boolean}
 */
function isValidMeld(cards) {
    if (state.type !== "game") return false
    let settings = state.board.settings
    if (settings.limit_meld_size && cards.length > settings.limit_meld_size) return false
    return isValidSet(cards) || isValidRun(cards)
}

/**
 * @param {Card} card
 * @param {GameSettings} settings
 * @return {number}
 */
function rankValue(card, settings) {
    return card.face.rank == "W" ? -1 :
        card.face.rank === "J" ? 11 :
            card.face.rank === "Q" ? 12 :
                card.face.rank === "K" ? 13 :
                    card.face.rank === "A" ? (settings.ace_rank === "low" ? 1 : 14) :
                        parseInt(card.face.rank)
}

/**
 * @param {Card[]} cards
 * @return {boolean}
 */
function isValidSet(cards) {
    if (state.type !== "game") return false
    if (cards.length < 3) return false
    let suits = new Set()
    let rank = cards.find(card => card.face.rank !== "W")?.face.rank ?? "W"
    return (state.board.settings.allow_set_duplicate_suit || cards.length <= 4)
        && cards.every(card => card.face.rank === "W" ||
            (card.face.rank === rank && (!suits.has(card.face.suit) || state.board.settings.allow_set_duplicate_suit) && suits.add(card.face.suit)))
}

/**
 * @param {Card[]} cards
 * @return {boolean}
 */
function isValidRun(cards) {
    if (state.type !== "game") return false
    if (cards.length < 3 || cards.length > 13) return false
    let rankedCards = cards // filter out non-wild cards and sort by rank
        .filter(card => card.face.rank != "W")
        .sort((a, b) => rankValue(a, state.board.settings) - rankValue(b, state.board.settings))
    if (rankedCards.length === 0) return true // all wilds is a run
    let wilds = cards.length - rankedCards.length
    if (!state.board.settings.allow_run_mixed_suit) {
        let suit = rankedCards[0].face.suit
        if (rankedCards.some(card => card.face.suit !== suit)) {
            return false
        }
    }
    let rank = rankValue(rankedCards[0], state.board.settings) - 1
    for (let card of rankedCards) {
        let nextRank = rankValue(card, state.board.settings)
        if (nextRank - rank - 1 > wilds || nextRank <= rank) return false
        wilds -= nextRank - rank - 1
        rank = nextRank
    }
    return true
}

