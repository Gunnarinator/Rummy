//@ts-check

/** @type {{type: "loading"} | {type: "lobby", lobby: Lobby} | {type: "game", board: Board, ui: GameUIState}} */
let state = { type: "loading" }

/** @type {(id: string) => HTMLDivElement | null} */
let id = document.getElementById.bind(document)

/**
 * @param {StartEvent} event
 */
function resetBoard(event) {
	state = {
		type: "game",
		board: {
			current_player_id: event.current_player_id,
			deck: event.card_ids.map(id => ({ id })),
			discard: [],
			game_code: event.game_code,
			melds: [],
			players: event.players.map(player => ({
				...player,
				hand: []
			}))
		},
		ui: {
			selectedCardIDs: new Set()
		}
	}
	let boardElement = id("board")
	if (boardElement.classList.contains("hidden")) boardElement.classList.remove("hidden")
	if (!id("lobby").classList.contains("hidden")) id("lobby").classList.add("hidden")
	boardElement.innerHTML = ""
	for (let cardID of event.card_ids) {
		let card = document.createElement("div")
		card.classList.add("card")
		card.id = `card-${cardID}`
		card.addEventListener("click", () => handleCardClick(cardID))
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
 * @param {string} cardID
 */
function handleCardClick(cardID) {
	if (state.type != "game") return
	if (state.board.turn?.player_id == state.board.current_player_id) {
		if (state.board.turn?.state == "draw") {
			if (state.board.deck[state.board.deck.length - 1]?.id == cardID || state.board.discard[state.board.discard.length - 1]?.id == cardID) {
				if (state.board.discard[state.board.discard.length - 1]?.id == cardID)
					state.ui.nonDiscardableCard = cardID
				sendAction({
					type: "draw",
					card_id: cardID
				})
			}
		}
	}
	//@ts-ignore
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

function performPrimaryAction() {
	if (state.type != "game" || !state.ui.primaryAction) return
	switch (state.ui.primaryAction) {
		case "discard":
			if (state.ui.selectedCardIDs.size != 1) return
			let cardID = [...state.ui.selectedCardIDs][0]
			sendAction({
				type: "discard",
				card_id: cardID
			})
			break
		case "meld":
			if (state.ui.selectedCardIDs.size == 0) return
			let cardIDs = [...state.ui.selectedCardIDs]
			sendAction({
				type: "meld",
				card_ids: cardIDs
			})
			break
		case "lay":
			break
	}
}

/**
 * @param {Card} card
 * @param {UICardPosition} position
 * @param {Board["turn"]["state"] | null | undefined} turnState
 */
function updateCard(card, position, turnState) {
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
			classString += " face-up spread hand hover-up"
			if (position.selected) classString += " selected"
			attributeMap.pin = "bottom"
			break
		case "opponent-hand":
			classString += " face-down spread hand"
			attributeMap.pin = position.position
			break
		case "deck":
			classString += " face-down deck"
			if (turnState == "draw" && position.index == position.stack_size - 1) classString += " hover-down"
			break
		case "discard":
			classString += " face-up discard"
			if (turnState == "draw" && position.index == position.stack_size - 1) classString += " hover-down"
			break
		case "meld":
			classString += " face-up spread meld"
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
function updatePlayerAccessories(player, position) {
	let playerPrimaryElement = id(`player-${player.id}-primary`)
	let playerSecondaryElement = id(`player-${player.id}-secondary`)
	let primaryStyle = `--stack-size:${player.hand.length}`
	let secondaryStyle = `--stack-size:${player.hand.length}`
	if (playerPrimaryElement.getAttribute("style") !== primaryStyle) playerPrimaryElement.setAttribute("style", primaryStyle)
	if (playerSecondaryElement.getAttribute("style") !== secondaryStyle) playerSecondaryElement.setAttribute("style", secondaryStyle)
	if (playerPrimaryElement.getAttribute("data-pin") !== position) playerPrimaryElement.setAttribute("data-pin", position)
	if (playerSecondaryElement.getAttribute("data-pin") !== position) playerSecondaryElement.setAttribute("data-pin", position)
	if (playerPrimaryElement.innerText != player.name) playerPrimaryElement.innerText = player.name
	if (playerSecondaryElement.innerText != `0 points`) playerSecondaryElement.innerText = `0 points`
}

/**
 * Updates the position and state of all cards in the board,
 */
function updateBoardState() {
	if (state.type !== "game") return
	let turnState = state.board.turn?.player_id == state.board.current_player_id ? state.board.turn.state : null
	for (let [i, card] of state.board.deck.entries()) {
		updateCard(card, {
			type: "deck",
			index: i,
			stack_size: state.board.deck.length
		}, turnState)
	}
	for (let [i, card] of state.board.discard.entries()) {
		updateCard(card, {
			type: "discard",
			index: i,
			stack_size: state.board.discard.length
		}, turnState)
	}
	for (let [i, meld] of state.board.melds.entries()) {
		let columnCount = state.board.melds.length > 1 ? 2 : 1
		let rowCount = Math.ceil(state.board.melds.length / columnCount)
		let column = i % columnCount
		let row = Math.floor(i / columnCount)
		for (let [j, card] of meld.entries()) {
			updateCard(card, {
				type: "meld",
				index: j,
				stack_size: meld.length,
				meld_row: row,
				meld_row_count: rowCount,
				meld_column: column,
				meld_column_count: columnCount
			}, turnState)
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
			}, turnState)
		}
		if (player.id === state.board.current_player_id) {
			for (let card of state.ui.selectedCardIDs) {
				if (!player.hand.some(({ id }) => id == card)) {
					state.ui.selectedCardIDs.delete(card)
				}
			}
		}
		updatePlayerAccessories(player, /**@type {any}*/(playerPosition))
		updateControlsState()
	}
}

function updateLobbyState() {
	if (state.type !== "lobby") return
	updateControlsState()
	if (id("lobby").classList.contains("hidden")) id("lobby").classList.remove("hidden")
	if (!id("board").classList.contains("hidden")) id("board").classList.add("hidden")
	let lobby = state.lobby
	document.querySelector(".lobby-code").textContent = lobby.code.replace(/.../, "$& ")
	document.querySelector(".lobby-players").innerHTML = ""
	if (lobby.players.length > 1) {
		for (let player of lobby.players) {
			let li = document.createElement("li")
			let name = player.name
			if (player.id == lobby.current_player_id)
				name += " (you)"
			li.textContent = name
			document.querySelector(".lobby-players").appendChild(li)
		}
	}
	(/** @type {HTMLButtonElement}*/ (document.querySelector("#remove-ai-button"))).disabled = !lobby.players.some(player => !player.human)
	document.querySelector("#lobby-primary").textContent = lobby.players.length > 1 ? "Start Game" : "Join Game"
}

/**
 * @param {string} cardID
 * @return {Card | null}
 */
function removeAndReturnCard(cardID) {
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
function moveCard(card, destination) {
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

/**
 * @param {GameEvent} event
 */
function handleEvent(event) {
	console.log(`Incoming ${event.type} event`, event)
	switch (event.type) {
		case "move":
			for (let card of event.cards.reverse()) {
				moveCard(card, event.destination)
			}
			break
		case "start":
			resetBoard(event)
			break
		case "turn":
			if (state.type !== "game") return
			state.board.turn = {
				player_id: event.player_id,
				state: event.state
			}
			updateBoardState()
			break
		case "lobby":
			state.type = "lobby"
			//@ts-ignore
			state.lobby = event.lobby
			updateLobbyState()
			break
	}
}

function updateControlsState() {
	let button = id("main-action-button")
	if (state.type !== "game")
		button.dataset.action = "none"
	else if (state.board.turn?.player_id != state.board.current_player_id || state.board.turn?.state != "play")
		button.dataset.action = state.ui.primaryAction = "none"
	else if (state.ui.selectedCardIDs.size == 1)
		// TODO: use "lay" if the selected card can be laid down
		if ([...state.ui.selectedCardIDs][0] != state.ui.nonDiscardableCard)
			button.dataset.action = state.ui.primaryAction = "discard"
		else
			button.dataset.action = state.ui.primaryAction = "none"
	else if (state.ui.selectedCardIDs.size > 1)
		button.dataset.action = state.ui.primaryAction = "meld"
	else
		button.dataset.action = state.ui.primaryAction = "none"
}

/** @type {GameEvent[]} */
let eventQueue = []

/** @type {ReturnType<typeof setTimeout> | null} */
let eventQueueTimer = null

/** @type {Partial<Record<GameEvent["type"], number>>}*/
const eventDelays = {
	start: 1000,
	move: 200
}
function handleNextEvent() {
	eventQueueTimer = null
	if (eventQueue.length === 0) return
	let event = eventQueue.shift()
	handleEvent(event)
	eventQueueTimer = setTimeout(handleNextEvent, eventDelays[event.type] || 0)
}

/**
 * @param {GameEvent} event
 */
function queueEvent(event) {
	eventQueue.push(event)
	if (eventQueueTimer == null) {
		handleNextEvent()
	}
}

/** @type {WebSocket} */
let ws = null

function init() {
	document.querySelector("#add-ai-button").addEventListener("click", () => {
		sendAction({
			type: "ai",
			action: "add"
		})
	})
	document.querySelector("#remove-ai-button").addEventListener("click", () => {
		sendAction({
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
			sendAction({
				type: "join",
				code: code.replace(/\D/g, "")
			})
		} else {
			sendAction({
				type: "start"
			})
		}
	})
	document.querySelector("#main-action-button").addEventListener("click", performPrimaryAction)
	ws = new WebSocket(`${location.protocol.replace("http", "ws")}//${location.host}/stream`)
	ws.onmessage = d => queueEvent(JSON.parse(d.data))
	ws.onclose = () => ws = null
	ws.onerror = console.error
}

if (document.readyState === "complete") {
	init()
} else {
	document.addEventListener("DOMContentLoaded", init)
}

/**
 * @param {Action} action
 */
function sendAction(action) {
	console.log(`Sending ${action.type} action`, action)
	if (ws) ws.send(JSON.stringify(action))
}

window.sendAction = sendAction
