/**
 * The state of the Game UI that isn't reflected in the board state itself.
 */
declare interface GameUIState {
    /**
     * The cards in the player's hand that are currently selected to perform an action.
     */
    selectedCardIDs: Set<string>
    primaryAction?: "discard" | "meld" | "lay" | "cancel" | "none"
    nonDiscardableCard?: string
    selectingMeldToLay?: boolean
    lastDrawnCard?: string
}
/**
 * A specifier for the position of a particular card. This is translated into CSS classes and variables.
 */
declare type UICardPosition = {
    type: "own-hand"
    index: number
    stack_size: number
    selected: boolean
} | {
    type: "opponent-hand"
    position: "top" | "right" | "left"
    index: number
    stack_size: number
} | {
    type: "deck" | "discard"
    index: number
    stack_size: number
} | {
    type: "meld"
    index: number
    stack_size: number
    meld_column: number
    meld_column_count: number
    meld_row: number
    meld_row_count: number
    eligible: boolean
}
/**
 * A Card instance is created for each card in the game, regardless of whether it has been dealt.
 *
 * The game generally starts off with 52 face-down cards in the deck.
 */
declare interface Card {
    /**
     * A randomized string identifying the card. Does not give away anything about the card's value or suit.
     */
    id: string
    /**
     * The face of the card. "null" indicates that the card is face down.
     */
    face?: {
        suit: "hearts" | "diamonds" | "spades" | "clubs"
        rank: "A" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "10" | "J" | "Q" | "K"
    } | {suit: "joker", "rank": "W"}
}
/**
 * A stack or row of cards. A stack of cards is ordered from top to bottom, while a row is ordered from left to right.
 */
declare type Stack = Card[]
declare interface Player {
    /** The name of the player. */
    name: string
    /** A randomized string uniquely identifying the player. */
    id: string
    /** The stack of cards the player has. */
    hand: Stack
    /** Whether the player is human. */
    human: boolean
}
/** A lobby of players. */
declare interface Lobby {
    /** A list of players currently in the game. */
    players: Pick<Player, "name" | "id" | "human">[]
    /** The player ID string of the current user. */
    current_player_id: string
    /** The code to join the current game. */
    code: string
    /** The game settings. */
    settings: GameSettings
}
declare type Meld = Stack
declare interface Board {
    /** An array of 1-4 players currently in the game. */
    players: Player[]
    /** The player ID string of the current user. */
    current_player_id: string
    /** Indicates which players turn it is. A null value means the game has not started yet or has ended, so it is no one's turn. */
    turn?: {
        /** The player ID who's turn it currently is. */
        player_id: string
        /**
         * The step the player must take.
         *
         * `"draw"`: The player must draw a card either from the discard pile or the deck.
         * `"play"`: The player can try to create or lay on melds as they see fit, and then they must discard a card.
         */
        state: "draw" | "play"
    }
    /**
     * An array of the melds currently on the table. At the beginning of the game, this is an empty array.
     */
    melds: Meld[]
    /**
     * The stack of face-down cards that have yet to be drawn. The next card to be drawn is the first item in the array.
     */
    deck: Stack
    /**
     * The stack of face-up cards that have been discarded. The last card to be discarded is the first item in the array.
     */
    discard: Stack
    /**
     * A code that other players may use to join the game before it starts.
     */
    game_code: string
    /**
     * The game settings.
     */
    settings: GameSettings
}

/**
 * A message recieved from the server.
 *
 * `"ping"`: A ping recieved from the server. Client should immediately respond with a pong action.
 * `"lobby"`: Update the state of the lobby.
 * `"start"`: Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.
 * `"turn"`: Update the current turn state of the game.
 * `"move"`: Indicates that a card has been moved, either by the current player or by someone else. `card.face` being present indicates that the card is face-up.
 * `"redeck"`: Indicates that the deck has been replenished from the discard pile.
 * `"end"`: Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping.
 */
declare type GameEvent = PingEvent | LobbyEvent | StartEvent | TurnEvent | MoveEvent | RedeckEvent | EndEvent

/**
 * A ping recieved from the server. Client should immediately respond with a pong action.
 */
declare interface PingEvent {
    type: "ping"
}
/**
 * A message received from the server that updates the state of the lobby.
 */
declare interface LobbyEvent {
    type: "lobby"
    /** The lobby state. */
    lobby: Lobby
}
/**
 * Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.
 */
declare interface StartEvent {
    type: "start"
    /** The IDs and names of all of the players in the game (assumed to have empty hands). */
    players: Omit<Player, "hand">[]
    /** The player ID string of the current user. */
    current_player_id: string
    /** A list of face-down card IDs to include in the deck. The order matches the shuffled state of the deck. */
    card_ids: string[]
    /** A code that other players may use to join the game before it starts. */
    game_code: string
    /** The current game settings. */
    settings: GameSettings
}
/**
 * Updates the current turn state of the game.
 */
declare interface TurnEvent {
    type: "turn"
    /** The player ID who's turn it currently is. */
    player_id: string
    /**
     * The step the player must take.
     *
     * `"draw"`: The player must draw a card either from the discard pile or the deck.
     * `"play"`: The player can try to create or lay on melds as they see fit, and then they must discard a card.
     */
    state: "draw" | "play"
}
/**
 * Indicates that a card has been moved, either by the current player or by someone else. `card.face` being present indicates that the card is face-up.
 */
declare interface MoveEvent {
    type: "move"
    /** The cards that are moved. `face` being present indicates that this card is face up (and should be revealed if necessary). */
    cards: Card[]
    /** The final destination of the cards. The client will animate the cards moving from their current position to the new position. */
    destination: {
        type: "player"
        player_id: string
        /** The position in the player's hand to move the cards to. `0` represents the card all the way to the left in the hand. */
        position: number
    } | {
        type: "meld"
        /** Identifies which meld to put the cards in, where `0` is the first meld that was laid down. This will create a new meld if necessary. */
        meld_number: number
        position: number
    } | {
        type: "discard"
    }
}
/**
 * Indicates that the deck has been replenished from the discard pile.
 *
 * All cards in the discard pile are considered to be destroyed, and the deck is replaced with new cards.
 */
declare interface RedeckEvent {
    type: "redeck",
    /** The server should generate a new list of card IDs to use for the new deck. */
    new_card_ids: string[]
}
/**
 * Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping. The client keeps track of score.
 */
declare interface EndEvent {
    type: "end"
    /** The player ID of the winner. */
    winner_id: string | null
    /** A map (keyed by player ID) showing the hand values of the losing players. These point values will be added to the winner's score. "Rummy" should already be accounted for. */
    hand_values: Record<string, number>
}

/**
 * A message sent to the server. Indicates an action that the client wishes to perform.
 *
 * The client does not assume any side-effects of these actions. The server must send events back to the client to indicate the result of the action.
 *
 * `"pong"`: A pong recieved from the client. Indicates that the connection is still active.
 * `"name"`: Sets the name of the current player.
 * `"ai"`: Add or remove an AI player.
 * `"join"`: Joins a game.
 * `"start"`: Starts a game.
 * `"draw"`: Draws a card from the deck or the discard pile.
 * `"meld"`: Lay down some cards to create a meld.
 * `"lay"`: Lay down a card to add to an existing meld.
 * `"discard"`: Discard a card.
 * `"settings"`: Changes the current game settings.
 *
 * The server should verify the legality of every action taken by the client, including whether it is the player's turn, and that the player's turn state is appropriate.
 */
declare type Action = PongAction | NameAction | AIAction | JoinAction | StartAction | DrawAction | MeldAction | LayAction | DiscardAction | SettingsAction

/**
 * A pong recieved from the client. Indicates that the connection is still active.
 */
declare interface PongAction {
    type: "pong"
}
/**
 * Sets the name of the current player.
 *
 * The server should verify that the name is valid (not too long, not already in use, must contain a letter or number).
 */
declare interface NameAction {
    type: "name"
    name: string
}
/**
 * Add or remove an AI player.
 *
 * If adding a player, the server should verify that there's room in the lobby and that the game has not started.
 * If removing a player, the server should verify that there is an AI player in the lobby to remove, and the game has not started.
 */
declare interface AIAction {
    type: "ai"
    action: "add" | "remove"
}
/**
 * Joins a game. A game is left when the websocket connection is closed.
 *
 * The server should verify that the game is not already running, and that thare are less than 4 players in the game.
 */
declare interface JoinAction {
    type: "join"
    code: string
}
/**
 * Starts the current game.
 *
 * The server should verify that at least two players are in the game.
 */
declare interface StartAction {
    type: "start"
}
/**
 * Draws a card from the deck or the discard pile.
 *
 * The server should verify that the card ID is at the top of the discard pile or the deck.
 */
declare interface DrawAction {
    type: "draw"
    /** The ID of the card to draw. This can be the top card of the deck or the top card of the discard pile. */
    card_id: string
}
/**
 * Lay down some cards to create a meld.
 *
 * The server should verify that (A) all cards are in the player's hand, and (B) that the cards form a valid meld.
 */
declare interface MeldAction {
    type: "meld"
    /** A list of card IDs to lay down. */
    card_ids: string[]
}
/**
 * Lay down a card to add to an existing meld.
 *
 * The server should verify that the card is in the player's hand, and that the card forms a valid meld.
 */
declare interface LayAction {
    type: "lay"
    /** The IDs of the cards to lay. */
    card_ids: string[]
    /** The index of the meld to add the card to. */
    meld_number: number
}
/**
 * Discard a card. This ends the player's turn.
 *
 * The server should verify that the card is in the player's hand.
 */
declare interface DiscardAction {
    type: "discard"
    /** The ID of the card to discard. */
    card_id: string
}
/**
 * Changes the current game settings.
 *
 * The server should verify that the settings are valid and that the game has not started.
 */
declare interface SettingsAction {
    type: "settings"
    settings: GameSettings
}

declare interface GameSettings {
    deck_count: number
    enable_jokers: boolean
    hand_size: number
    first_turn: "next_player" | "prev_winner" | "random"
    allow_draw_choice: boolean
    allow_run_mixed_suit: boolean
    limit_meld_size: 3 | 4 | null
    ace_rank: "low" | "high"
    deck_exhaust: "flip_discard" | "shuffle_discard" | "end_round"
    require_end_discard: boolean
    lay_at_end: boolean
}

