//@ts-check
import * as connection from "./connection.js"
import * as controls from "./controls.js"
import * as settings from "./settings.js"

/**
 * @typedef {{type: "loading", lobby?: never, board?: never, ui?: never, scores: Partial<Record<string, number>>} |
 * 		{type: "lobby", scores: Partial<Record<string, number>>, lobby: Lobby, board?: never, ui?: never} |
 * 		{type: "game", scores: Partial<Record<string, number>>, board: Board, ui: GameUIState, lobby?: never}
 * } State
 */

/** @type {State} */
export let state = { type: "loading", scores: {} }

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
	settings.init()
}

if (document.readyState === "complete") {
	init()
} else {
	document.addEventListener("DOMContentLoaded", init)
}
