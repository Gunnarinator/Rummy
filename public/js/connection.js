import { id, setState, state } from "./index.js"
import * as ui from "./ui.js"

/**
 * @param {GameEvent} event
 */
export function handleEvent(event) {
    console.log(`Incoming ${event.type} event`, event)
    switch (event.type) {
        case "ping":
            sendAction({ type: "pong" })
            break
        case "move":
            for (let card of event.cards.reverse()) {
                ui.moveCard(card, event.destination)
            }
            break
        case "start":
            ui.resetBoard(event)
            break
        case "turn":
            if (state.type !== "game") return
            state.board.turn = {
                player_id: event.player_id,
                state: event.state
            }
            state.ui.selectingMeldToLay = false
            if (event.state == "draw")
                state.ui.lastDrawnCard = null
            ui.updateBoardState()
            break
        case "lobby":
            state.type = "lobby"
            //@ts-ignore
            state.lobby = event.lobby
            ui.updateLobbyState()
            break
        case "redeck":
            if (state.type !== "game") return
            if (event.new_card_ids.length != state.board.discard.length) throw Error("Invalid number of cards")
            state.board.deck = event.new_card_ids.map(id => ({ id }))
            for (let oldCard of state.board.discard) {
                let newID = event.new_card_ids.shift()
                let cardElement = id(`card-${oldCard.id}`)
                cardElement.id = `card-${newID}`
                cardElement.dataset.id = newID
            }
            state.board.discard = []
            ui.updateBoardState()
            break
        case "end":
            if (state.type !== "game") return
            if (event.winner_id) {
                for (let score of Object.values(event.hand_values)) {
                    state.scores[event.winner_id] = (state.scores[event.winner_id] ?? 0) + score
                }
            }
            break
        default:
            console.error("Unrecognized event", event)
    }
}


/** @type {GameEvent[]} */
let eventQueue = []

/** @type {ReturnType<typeof setTimeout> | null} */
let eventQueueTimer = null

/** @type {Partial<Record<GameEvent["type"], number>>}*/
const eventDelays = {
    start: 1000,
    redeck: 600,
    move: 600,
    end: 1000
}
function handleNextEvent() {
    eventQueueTimer = null
    if (eventQueue.length === 0) return
    let event = eventQueue.shift()
    handleEvent(event)
    if (event.type == "move" && state.type == "game" && !state.board.turn) {
        // use a shorter delay for dealing
        eventQueueTimer = setTimeout(handleNextEvent, 600 / state.board.players.length)
    } else {
        eventQueueTimer = setTimeout(handleNextEvent, eventDelays[event.type] || 0)
    }
}

/**
 * @param {GameEvent} event
 */
function queueEvent(event) {
    if (event.type === "ping") {
        // ping events are handled immediately
        handleEvent(event)
        return
    }
    eventQueue.push(event)
    if (eventQueueTimer == null) {
        handleNextEvent()
    }
}

/** @type {WebSocket} */
let ws = null

export function init() {
    ws = new WebSocket(`${location.protocol.replace("http", "ws")}//${location.host}/stream`)
    ws.onmessage = d => queueEvent(JSON.parse(d.data))
    ws.onclose = () => {
        ws = null
        setState({
            type: "loading",
            scores: {}
        })
        id("board").classList.add("hidden")
        id("lobby").classList.add("hidden")
        setTimeout(() => location = location, 1000)
    }
    ws.onerror = console.error
}

/**
 * @param {Action} action
 */
export function sendAction(action) {
    console.log(`Sending ${action.type} action`, action)
    if (ws) ws.send(JSON.stringify(action))
}
