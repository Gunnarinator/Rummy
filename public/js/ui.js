import * as controls from "./controls.js"
import { id, setState, state } from "./index.js"
import * as rules from "./rules.js"
import * as settings from "./settings.js"

/**
 * @param {StartEvent} event
 */
export function resetBoard(event) {
    setState({
        type: "game",
        scores: state.scores ?? {},
        board: {
            current_player_id: event.current_player_id,
            deck: event.card_ids.map(id => ({ id })),
            discard: [],
            game_code: event.game_code,
            melds: [],
            players: event.players.map(player => ({
                ...player,
                hand: []
            })),
            settings: event.settings
        },
        ui: {
            selectedCardIDs: new Set()
        }
    })
    let boardElement = id("board")
    if (boardElement.classList.contains("hidden")) boardElement.classList.remove("hidden")
    if (!id("lobby").classList.contains("hidden")) id("lobby").classList.add("hidden")
    boardElement.innerHTML = ""
    for (let cardID of event.card_ids) { //modifies board html to display the cards
        let card = document.createElement("div")
        card.classList.add("card") //this can be where I add different colors
        //card.classList.add("Red")
        card.id = `card-${cardID}`
        card.dataset.id = cardID
        card.addEventListener("click", function () { controls.handleCardClick(this.dataset.id) }) //will probably look something like this
        boardElement.appendChild(card)
    }
    for (let player of event.players) {
        let playerPrimaryElement = document.createElement("div")
        playerPrimaryElement.classList.add("accessory-primary")
        playerPrimaryElement.id = `player-${player.id}-primary`
        boardElement.appendChild(playerPrimaryElement)
        let playerSecondaryElement = document.createElement("div")
        playerSecondaryElement.classList.add("accessory-secondary")
        playerSecondaryElement.id = `player-${player.id}-secondary`
        boardElement.appendChild(playerSecondaryElement)
    }
    updateBoardState()
}



/**
 * @param {Card} card
 * @param {UICardPosition} position
 * @param {Board["turn"]["state"] | null | undefined} turnState
 * @param {boolean} laySelection
 */
export function updateCard(card, position, turnState, laySelection) {
    let cardElement = id(`card-${card.id}`)
    let classString = "card"
    let styleString = `--stack-index:${position.index};--stack-size:${position.stack_size};`
    /** @type {Record<string, string>} */
    let attributeMap = card.face ? {
        suit: card.face.suit,
        rank: card.face.rank
    } : {}
    switch (position.type) {
        case "own-hand":
            classString += " face-up spread hand"
            if (!laySelection && turnState == "play") classString += " turn hover-up"
            if (position.selected) classString += " selected"
            if (laySelection && !position.selected) classString += " faded"
            attributeMap.pin = "bottom"
            break
        case "opponent-hand":
            classString += " face-down spread hand" // here I can change color?
            if (turnState) classString += " turn"
            attributeMap.pin = position.position
            break
        case "deck":
            classString += " face-down deck"
            if (turnState == "draw" && position.index == position.stack_size - 1) classString += " hover-down"
            break
        case "discard":
            classString += " face-up discard"
            if (turnState == "draw" && position.index == position.stack_size - 1) classString += " hover-down"
            if (laySelection) classString += " faded"
            break
        case "meld":
            classString += " face-up spread meld"
            if (laySelection && !position.eligible) classString += " faded"
            styleString += `--meld-row:${position.meld_row};--meld-row-count:${position.meld_row_count};--meld-column:${position.meld_column};--meld-column-count:${position.meld_column_count};`
            break
    }
    if (cardElement.getAttribute("class") !== classString) cardElement.setAttribute("class", classString)
    if (cardElement.getAttribute("style") !== styleString) cardElement.setAttribute("style", styleString)
    for (let [key, value] of Object.entries(attributeMap)) {
        if (cardElement.getAttribute(`data-${key}`) !== value) cardElement.setAttribute(`data-${key}`, value)
    }
}

/**
 * @param {Player} player
 * @param {"top" | "bottom" | "left" | "right"} position
 */
export function updatePlayerAccessories(player, position) {
    let playerPrimaryElement = id(`player-${player.id}-primary`)
    let playerSecondaryElement = id(`player-${player.id}-secondary`)
    let primaryStyle = `--stack-size:${player.hand.length}`
    let secondaryStyle = `--stack-size:${player.hand.length}`
    let score = `${state.scores[player.id] ?? 0} points`
    if (playerPrimaryElement.getAttribute("style") !== primaryStyle) playerPrimaryElement.setAttribute("style", primaryStyle)
    if (playerSecondaryElement.getAttribute("style") !== secondaryStyle) playerSecondaryElement.setAttribute("style", secondaryStyle)
    if (playerPrimaryElement.getAttribute("data-pin") !== position) playerPrimaryElement.setAttribute("data-pin", position)
    if (playerSecondaryElement.getAttribute("data-pin") !== position) playerSecondaryElement.setAttribute("data-pin", position)
    if (playerPrimaryElement.innerText != player.name) playerPrimaryElement.innerText = player.name
    if (playerSecondaryElement.innerText != score) playerSecondaryElement.innerText = score
}

/**
 * Updates the position and state of all cards in the board,
 */
export function updateBoardState() {
    if (state.type !== "game") return
    let turnState = state.board.turn?.player_id == state.board.current_player_id ? state.board.turn.state : null
    for (let [i, card] of state.board.deck.entries()) {
        updateCard(card, {
            type: "deck",
            index: i,
            stack_size: state.board.deck.length
        }, turnState, state.ui.selectingMeldToLay)
    }
    for (let [i, card] of state.board.discard.entries()) {
        updateCard(card, {
            type: "discard",
            index: i,
            stack_size: state.board.discard.length
        }, turnState, state.ui.selectingMeldToLay)
    }
    for (let [i, meld] of state.board.melds.entries()) {
        let columnCount = state.board.melds.length > 1 ? 2 : 1
        let rowCount = Math.ceil(state.board.melds.length / columnCount)
        let column = i % columnCount
        let row = Math.floor(i / columnCount)
        let eligibleMelds = rules.getMeldsForLay()
        for (let [j, card] of meld.entries()) {
            updateCard(card, {
                type: "meld",
                index: j,
                stack_size: meld.length,
                meld_row: row,
                meld_row_count: rowCount,
                meld_column: column,
                meld_column_count: columnCount,
                eligible: eligibleMelds.includes(i)
            }, turnState, state.ui.selectingMeldToLay)
        }
    }
    let rotatedPlayers = [...state.board.players]
    if (rotatedPlayers.length > 2) {
        while (rotatedPlayers.length < 4) rotatedPlayers.push(null)
    }
    while (rotatedPlayers[0].id !== state.board.current_player_id) rotatedPlayers.push(rotatedPlayers.shift())
    for (let [i, player] of rotatedPlayers.entries()) {
        if (!player) continue
        let playerPosition = (state.board.players.length > 2 ? ["bottom", "left", "top", "right"] : ["bottom", "top"])[i]
        for (let [j, card] of player.hand.entries()) {
            updateCard(card, player.id === state.board.current_player_id ? {
                type: "own-hand",
                index: j,
                stack_size: player.hand.length,
                selected: state.ui.selectedCardIDs.has(card.id)
            } : {
                type: "opponent-hand",
                position: /**@type {any}*/(playerPosition),
                index: j,
                stack_size: player.hand.length
            }, state.board.turn?.player_id == player.id ? state.board.turn.state : null, state.ui.selectingMeldToLay)
        }
        if (player.id === state.board.current_player_id) {
            for (let card of state.ui.selectedCardIDs) {
                if (turnState != "play" || !player.hand.some(({ id }) => id == card)) {
                    state.ui.selectedCardIDs.delete(card)
                }
            }
        }
        updatePlayerAccessories(player, /**@type {any}*/(playerPosition))
        controls.updateControlsState()
    }
}

/**
 * @param {boolean} updateName
 */
export function updateLobbyState(updateName) {
    if (state.type !== "lobby") return
    controls.updateControlsState()
    settings.updateSettingsState(updateName)
    if (id("lobby").classList.contains("hidden")) id("lobby").classList.remove("hidden")
    if (!id("board").classList.contains("hidden")) id("board").classList.add("hidden")
    let lobby = state.lobby
    document.querySelector(".lobby-code").textContent = lobby.code.replace(/.../, "$& ")
    document.querySelector(".lobby-players").innerHTML = ""
    let showScores = lobby.players.some(({ id }) => id in state.scores)
    if (lobby.players.length > 1) {
        for (let player of lobby.players) {
            let tr = document.createElement("tr")
            let nameBox = document.createElement("td")
            let name = player.name
            if (player.id == lobby.current_player_id)
                name += " (you)"
            nameBox.textContent = name
            tr.appendChild(nameBox)
            if (showScores) {
                let scoreBox = document.createElement("td")
                scoreBox.textContent = `${state.scores[player.id] || 0} points`
                tr.appendChild(scoreBox)
            }
            document.querySelector(".lobby-players").appendChild(tr)
        }
    }
    (/** @type {HTMLButtonElement}*/ (document.querySelector("#remove-ai-button"))).disabled = !lobby.players.some(player => !player.human)
    document.querySelector("#lobby-primary").textContent = lobby.players.length > 1 ? "Start Game" : "Join Game"
}

/**
 * @param {string} cardID
 * @return {Card | null}
 */
export function removeAndReturnCard(cardID) {
    if (state.type !== "game") return null
    let card = state.board.deck.find(({ id }) => cardID === id)
    if (card) {
        state.board.deck.splice(state.board.deck.indexOf(card), 1)
    } else {
        card = state.board.discard.find(({ id }) => cardID === id)
        if (card) {
            state.board.discard.splice(state.board.discard.indexOf(card), 1)
        } else {
            card = state.board.melds.flatMap(meld => meld.filter(({ id }) => cardID === id))[0]
            if (card) {
                let meld = state.board.melds.find(meld => meld.includes(card))
                meld.splice(meld.indexOf(card), 1)
            } else {
                card = state.board.players.flatMap(player => player.hand.filter(({ id }) => cardID === id))[0]
                if (card) {
                    let player = state.board.players.find(player => player.hand.includes(card))
                    player.hand.splice(player.hand.indexOf(card), 1)
                }
            }
        }
    }
    return card || null
}

/**
 *
 * @param {Card} card
 * @param {MoveEvent["destination"]} destination
 * @returns
 */
export function moveCard(card, destination) {
    if (state.type !== "game") return
    let id = card.id
    let oldCard = removeAndReturnCard(id)
    let newCard = {
        id: id,
        face: card.face || oldCard?.face
    }
    switch (destination.type) {
        case "discard":
            state.board.discard.push(newCard)
            break
        case "meld":
            let meld = state.board.melds[destination.meld_number]
            if (meld) {
                meld.splice(destination.position, 0, newCard)
            } else {
                state.board.melds.push([newCard])
            }
            break
        case "player":
            // @ts-ignore
            let player = state.board.players.find(({ id }) => id === destination.player_id)
            player.hand.splice(destination.position, 0, newCard)
            break
    }
    updateBoardState()
}
