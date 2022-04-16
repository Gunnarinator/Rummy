//@ts-check
import * as connection from "./connection.js"
import * as controls from "./controls.js"

/**
 * @typedef {{type: "loading", lobby?: never, board?: never, ui?: never} |
 * 		{type: "lobby", lobby: Lobby, board?: never, ui?: never} |
 * 		{type: "game", board: Board, ui: GameUIState, lobby?: never}
 * } State
 */

/** @type {State} */
export let state = { type: "loading" }

/**
 * @param {State} s
*/
export function setState(s) {
	state = s
}

/** @type {(id: string) => HTMLDivElement | null} */
export const id = document.getElementById.bind(document)

function init() {
	controls.init()
	connection.init()
}

if (document.readyState === "complete") {
	init()
} else {
	document.addEventListener("DOMContentLoaded", init)
}
