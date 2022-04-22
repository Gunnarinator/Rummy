import * as connection from "./connection.js"
import { id, state } from "./index.js"


/** @type {{[K in keyof GameSettings]?: {name: string, options: {label: string, value: GameSettings[K], element?: HTMLButtonElement}[]}}} */
const gameSettings = {
    deck_count: {
        name: "Number of decks",
        options: [
            {
                label: "1",
                value: 1
            },
            {
                label: "2",
                value: 2
            },
            {
                label: "4",
                value: 4
            }
        ]
    },
    enable_jokers: {
        name: "Jokers",
        options: [
            {
                label: "No",
                value: false
            },
            {
                label: "Yes",
                value: true
            }
        ]
    },
    hand_size: {
        name: "Hand size",
        options: [
            {
                label: "7",
                value: 7
            },
            {
                label: "8",
                value: 8
            },
            {
                label: "9",
                value: 9
            },
            {
                label: "10",
                value: 10
            },
            {
                label: "11",
                value: 11
            },
            {
                label: "12",
                value: 12
            }
        ]
    },
    // first_turn: {
    //     name: "First turn",
    //     options: [
    //         {
    //             label: "Next player",
    //             value: "next_player"
    //         },
    //         {
    //             label: "Previous winner",
    //             value: "prev_winner"
    //         },
    //         {
    //             label: "Random",
    //             value: "random"
    //         }
    //     ]
    // },
    // allow_draw_choice: {
    //     name: "Draw choice",
    //     options: [
    //         {
    //             label: "No",
    //             value: false
    //         },
    //         {
    //             label: "Yes",
    //             value: true
    //         }
    //     ]
    // },
    allow_run_mixed_suit: {
        name: "Allow mixed suits in a run",
        options: [
            {
                label: "No",
                value: false
            },
            {
                label: "Yes",
                value: true
            }
        ]
    },
    allow_set_duplicate_suit: {
        name: "Allow duplicate suits in a set",
        options: [
            {
                label: "No",
                value: false
            },
            {
                label: "Yes",
                value: true
            }
        ]
    },
    limit_meld_size: {
        name: "Maximum meld size",
        options: [
            {
                label: "Any",
                value: null
            },
            {
                label: "3",
                value: 3
            },
            {
                label: "4",
                value: 4
            }
        ]
    },
    ace_rank: {
        name: "Ace rank",
        options: [
            {
                label: "Low",
                value: "low"
            },
            {
                label: "High",
                value: "high"
            }
        ]
    },
    deck_exhaust: {
        name: "When the deck is exhausted",
        options: [
            {
                label: "Flip discard pile",
                value: "flip_discard"
            },
            {
                label: "Shuffle discard pile",
                value: "shuffle_discard"
            },
            {
                label: "End round",
                value: "end_round"
            }
        ]
    },
    require_end_discard: {
        name: "Require discard to end the round",
        options: [
            {
                label: "No",
                value: false
            },
            {
                label: "Yes",
                value: true
            }
        ]
    },
    // lay_at_end: {
    //     name: "Lay at end",
    //     options: [
    //         {
    //             label: "No",
    //             value: false
    //         },
    //         {
    //             label: "Yes",
    //             value: true
    //         }
    //     ]
    // }
}

export function init() {
    const settingsElement = id("game-settings")
    for (let [settingID, setting] of Object.entries(gameSettings)) {
        const settingElement = document.createElement("div")
        settingElement.classList.add("setting")
        const settingNameElement = document.createElement("p")
        settingNameElement.classList.add("setting-name")
        settingNameElement.textContent = setting.name + ":"
        settingElement.appendChild(settingNameElement)
        const settingOptionsElement = document.createElement("div")
        settingOptionsElement.classList.add("setting-options")
        for (let option of setting.options) {
            const optionElement = document.createElement("button")
            optionElement.classList.add("setting-option")
            optionElement.textContent = option.label
            optionElement.addEventListener("click", () => {
                if (state.type !== "lobby") return
                const s = {
                    ...state.lobby.settings,
                    [settingID]: option.value
                }
                connection.sendAction({
                    type: "settings",
                    settings: s
                })
            })
            option.element = optionElement
            settingOptionsElement.appendChild(optionElement)
        }
        settingElement.appendChild(settingOptionsElement)
        settingsElement.appendChild(settingElement)
    }
}

export function updateSettingsState() {
    if (state.type !== "lobby" && state.type !== "game") return
    document.querySelectorAll("#game-settings .setting-option.selected").forEach(e => e.classList.remove("selected"))
    for (let [settingID, setting] of Object.entries(gameSettings)) {
        for (let option of setting.options) {
            if (option.value === state.lobby.settings[settingID]) {
                option.element.classList.add("selected")
            }
        }
    }
}
