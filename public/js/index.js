//@ts-check
import * as connection from "./connection.js"
import * as controls from "./controls.js"

/** @type {{type: "loading"} | {type: "lobby", lobby: Lobby} | {type: "game", board: Board, ui: GameUIState}} */
export let state = { type: "loading" }

/**
 * @template {{type: "loading"} | {type: "lobby", lobby: Lobby} | {type: "game", board: Board, ui: GameUIState}} S
 * @param {S} s
 * @return {asserts state is S}
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
