import * as connection from "./connection.js"
import { id, state } from "./index.js"
import * as rules from "./rules.js"
/**
 * @param {string} cardID
 */
export function handleCardClick(cardID) {
    if (state.type != "game") return
    if (state.board.turn?.player_id == state.board.current_player_id) {
        if (state.board.turn.state == "draw") {
            if (state.board.deck[state.board.deck.length - 1]?.id == cardID || state.board.discard[state.board.discard.length - 1]?.id == cardID) {
                if (state.board.discard[state.board.discard.length - 1]?.id == cardID)
                    state.ui.nonDiscardableCard = cardID
                else
                    state.ui.nonDiscardableCard = null
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
            break
    }
}

export function updateControlsState() {
    let button = id("main-action-button")
    if (state.type !== "game")
        button.dataset.action = "none"
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
