import * as connection from "./connection.js"
import { id, state } from "./index.js"
import * as rules from "./rules.js"
import * as ui from "./ui.js"
/**
 * @param {string} cardID
 */
export function handleCardClick(cardID) {
    if (state.type != "game") return
    if (state.board.turn?.player_id == state.board.current_player_id) {
        if (state.ui.selectingMeldToLay) {
            let [index, meld] = [...state.board.melds.entries()].find(([, meld]) => meld.some(card => card.id == cardID)) ?? []
            if (meld && rules.getMeldsForLay().includes(index)) {
                connection.sendAction({
                    type: "lay",
                    meld_number: index,
                    card_ids: [...state.ui.selectedCardIDs]
                })
                state.ui.selectingMeldToLay = false
            }
        } if (state.board.turn.state == "draw") {
            if (state.board.deck[state.board.deck.length - 1]?.id == cardID || state.board.discard[state.board.discard.length - 1]?.id == cardID) {
                if (state.board.discard[state.board.discard.length - 1]?.id == cardID)
                    state.ui.nonDiscardableCard = cardID
                else
                    state.ui.nonDiscardableCard = null
                state.ui.lastDrawnCard = cardID
                connection.sendAction({
                    type: "draw",
                    card_id: cardID
                })
            }
        } else {
            if (state.board.players.find(player => player.id == state.board.current_player_id)?.hand.some(({ id }) => id == cardID)) {
                if (state.ui.selectedCardIDs.has(cardID)) {
                    state.ui.selectedCardIDs.delete(cardID)
                    id("card-" + cardID).classList.remove("selected")
                } else {
                    state.ui.selectedCardIDs.add(cardID)
                    id("card-" + cardID).classList.add("selected")
                }
                updateControlsState()
            }
        }
    }
}

export function performPrimaryAction() {
    if (state.type != "game" || !state.ui.primaryAction) return
    switch (state.ui.primaryAction) {
        case "discard":
            if (state.ui.selectedCardIDs.size != 1) return
            let cardID = [...state.ui.selectedCardIDs][0]
            connection.sendAction({
                type: "discard",
                card_id: cardID
            })
            break
        case "meld":
            if (state.ui.selectedCardIDs.size == 0) return
            let cardIDs = [...state.ui.selectedCardIDs]
            connection.sendAction({
                type: "meld",
                card_ids: cardIDs
            })
            break
        case "lay":
            state.ui.selectingMeldToLay = true
            updateControlsState()
            ui.updateBoardState()
            break
        case "cancel":
            state.ui.selectingMeldToLay = false
            updateControlsState()
            ui.updateBoardState()
            break
    }
}

export function updateControlsState() {
    let button = id("main-action-button")
    if (state.type !== "game")
        button.dataset.action = "none"
    else if (state.ui.selectingMeldToLay)
        button.dataset.action = state.ui.primaryAction = "cancel"
    else if (state.board.turn?.player_id != state.board.current_player_id || state.board.turn?.state != "play")
        button.dataset.action = state.ui.primaryAction = "none"
    else if (state.ui.selectedCardIDs.size == 1)
        if (rules.getMeldsForLay().length > 0)
            button.dataset.action = state.ui.primaryAction = "lay"
        else if ([...state.ui.selectedCardIDs][0] != state.ui.nonDiscardableCard)
            button.dataset.action = state.ui.primaryAction = "discard"
        else
            button.dataset.action = state.ui.primaryAction = "none"
    else if (state.ui.selectedCardIDs.size > 1)
        if (rules.canMeldSelectedCards())
            button.dataset.action = state.ui.primaryAction = "meld"
        else if (rules.getMeldsForLay().length > 0)
            button.dataset.action = state.ui.primaryAction = "lay"
        else
            button.dataset.action = state.ui.primaryAction = "none"
    else
        button.dataset.action = state.ui.primaryAction = "none"
}

export function init() {
    document.querySelector("#add-ai-button").addEventListener("click", () => {
        connection.sendAction({
            type: "ai",
            action: "add"
        })
    })
    document.querySelector("#remove-ai-button").addEventListener("click", () => {
        connection.sendAction({
            type: "ai",
            action: "remove"
        })
    })
    document.querySelector("#lobby-primary").addEventListener("click", () => {
        if (state.type !== "lobby") return
        let lobby = state.lobby
        if (lobby.players.length === 1) {
            let code = ""
            while (code.replace(/\D/g, "").length != 6) {
                code = prompt("Enter a 6-digit lobby code:", code)
            }
            connection.sendAction({
                type: "join",
                code: code.replace(/\D/g, "")
            })
        } else {
            connection.sendAction({
                type: "start"
            })
        }
    })
    document.querySelector("#main-action-button").addEventListener("click", performPrimaryAction)
}

// prevent the browser from doing it's own behavior when the user presses certain keys in-game
window.addEventListener("keydown", e => {
    if (state.type !== "game") return
    if (e.key == "Enter" || e.key == " " || e.key == "Tab" || e.key.includes("Arrow")) e.preventDefault()
})

window.addEventListener("keyup", e => {
    if (state.type !== "game") return
    if (e.key == "Enter" || e.key == " " || e.key == "Tab" || e.key.includes("Arrow")) e.preventDefault()
    if (state.board.turn?.player_id != state.board.current_player_id) return
    if (state.board.turn.state == "draw") {
        // waiting to draw a card
        switch (e.key) {

            // draw from the deck
            case "`":
            case "1":
            case "q":
            case ",":
            case " ":
                if (state.board.deck.length == 0) break
                handleCardClick(state.board.deck[state.board.deck.length - 1].id)
                e.preventDefault()
                break

            // draw from the discard pile
            case "0":
            case "-":
            case "=":
            case "e":
            case ".":
            case "Tab":
                if (state.board.discard.length == 0) break
                handleCardClick(state.board.discard[state.board.discard.length - 1].id)
                e.preventDefault()
                break
        }
    } else {
        // time to make a play
        switch (e.key) {

            // lay down selected cards
            case "Enter":
            case " ":
                if (state.ui.primaryAction === "lay" || state.ui.primaryAction === "meld") {
                    performPrimaryAction()
                    e.preventDefault()
                }
                break

            // cancel the option to select a meld to lay onto
            // or deselect all cards
            case "Escape":
                if (state.ui.primaryAction != "cancel") {
                    state.ui.selectedCardIDs.forEach(handleCardClick)
                    break
                }

            // discard the selected card
            // or cancel the option to select a meld to lay onto
            case "Backspace":
            case "Delete":
                if (state.ui.primaryAction === "discard" || state.ui.primaryAction === "cancel") {
                    performPrimaryAction()
                    e.preventDefault()
                }
                break

            // deselect all cards
            case "`":
                state.ui.selectedCardIDs.forEach(handleCardClick)
                break

            // select the card that was just drawn
            case "=":
            case "-":
                if (state.ui.lastDrawnCard)
                    handleCardClick(state.ui.lastDrawnCard)
                break

            // select a card according to the number pressed (0 is 10)
            // hold shift to add 10 to the index (so shift-2 selects card 12)
            // also works for selecting which meld to lay onto (only counts eligible melds)
            default:
                if ("1234567890".includes(e.key)) {
                    let index = "1234567890".indexOf(e.key)
                    if (e.shiftKey) index += 10
                    if (state.ui.selectingMeldToLay) {
                        let availableMelds = rules.getMeldsForLay()
                        if (index >= availableMelds.length) break
                        let meld = state.board.melds[availableMelds[index]]
                        handleCardClick(meld[0].id)
                        e.preventDefault()
                    } else {
                        let playerHand = state.board.players.find(p => p.id == state.board.current_player_id).hand
                        if (index >= playerHand.length) break
                        handleCardClick(playerHand[index].id)
                        e.preventDefault()
                    }
                }
                break
        }
    }
})
