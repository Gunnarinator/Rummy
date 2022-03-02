# Communications Protocol for Super Rummy

## Websockets

Super Rummy uses a [WebSocket](https://www.html5rocks.com/en/tutorials/websockets/basics/) based API for communication between the server and the client. There are four main motivations for designing this protocol:

1. It should be fast with low latency. This generally means maintaining a persistent connection.
2. Information should be provided on a need-to-know basis. For example, the client should only know what a card is once it's face up.
3. It should be easy to understand and use in Python and in JavaScript. A JSON-based API helps with this.
4. Cards should be realistic. The card you see moving in or out of a player's hand in-game matters just like in real life gameplay.

## Events and Actions

The API is centered around **events** and **actions**. All messages sent from the server to the client are **events**. These are events in the game, such as a card moving from point A to point B. All messages sent from the client are **actions**. These represent the intentions of the player, such as wanting to discard a 5 of hearts.

All messages in this API are formatted using JSON. The documentation here uses an adaptation of TypeScript. Everything should be self-explanatory. Keep in mind that optional properties are denoted with a `?` and they can be either missing or `null` (`None` in Python). `numbers` are generally going to be `Ints` from Python.

In both events and actions, the specific type of event or action taking place is denoted using the `type` parameter.

## Game and Lobby Setup

As soon as the client connects, the server sends a `lobby` event:

```typescript
/**
 * A message received from the server that updates the state of the lobby.
 */
declare interface LobbyEvent {
    type: "lobby"
    /** The lobby state. */
    lobby: {
		/** A list of players currently in the game. */
		players: {
			/** The name of the player. */
			name: string
			/** A randomized string uniquely identifying the player. */
			id: string
			/** Whether the player is human. */
			human: boolean
		}[]
		/** The player ID string of the current user. */
		current_player_id: string
		/** The code to join the current game. */
		code: string
	}
}
```

Usually the lobby is empty at first, so the `players` array will just contain one player, the player ID.

A player may decide to leave their empty lobby and join a different one, with the `join` action:

```typescript
/**
 * Joins a game. A game is left when the websocket connection is closed.
 *
 * The server should verify that the game is not already running, and that thare are less than 4 players in the game.
 */
declare interface JoinAction {
    type: "join"
    code: string
}
```

This action implicitly leaves the lobby the player was in. A lobby is closed/deleted when all players have left. Note that when a client disconnects (the websocket errors or closes), they should be treated as if they left the lobby.

If a player leaves during a game (for example if they get disconnected), they should be left in the game, but their turn should be skipped.

There are other actions that allow the player to set their username, or to add/remove AI players from the lobby:

```typescript
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
```

> Throughout all of these changes (any time a player leaves, joins, changes their name, or if an AI player is created or removed), the sever should send new `lobby` events to _all_ clients in the lobby in order to notify them of the changes.

Finally, once everyone is ready, a player may start the game with the `start` event:

```typescript
/**
 * Starts the current game.
 *
 * The server should verify that at least two players are in the game.
 */
declare interface StartAction {
    type: "start"
}
```

## Gameplay

### Starting the game

At the beginning of each round, the server should shuffle a new deck of cards, and then randomly assign an ID to each card. The IDs will be sent to the client immediately, but the faces of the cards associated with those IDs won't be revealed until the player can see the card. Using IDs like this ensures visual accuracy without giving away unnecessary information.

Once the game is started the server needs to send a `start` event.

```typescript
/**
 * Resets the game to a default state where all players have empty hands, there is no meld, and the deck is shuffled.
 */
declare interface StartEvent {
    type: "start"
    /** The IDs and names of all of the players in the game (assumed to have empty hands). */
    players: {
		/** The name of the player. */
		name: string
		/** A randomized string uniquely identifying the player. */
		id: string
		/** Whether the player is human. */
		human: boolean
	}[]
    /** The player ID string of the current user. */
    current_player_id: string
    /** A list of face-down card IDs to include in the deck. The order matches the shuffled state of the deck. */
    card_ids: string[]
    /** A code that other players may use to join the game before it starts. */
    game_code: string
}
```

Note that all "stacks" of cards (and card IDs) are ordered from the _bottom up_. This means that the first card to be drawn is at the _end_ of the `card_ids` array.

### Dealing and Moving Cards

_After_ setting this state, the server can then start to deal out the deck. In order to move a card from one place to another, the `move` event is used.

> Most of the time when using this event, `cards` will only contain one item; the card to move. The one exception to this is when a new meld is formed, or multiple cards are added to it at the same time. In this case, `cards` will contain the 3-4 cards that form the new meld.

```typescript
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
```

This is by far the most used event. Since clients already know where each card ID is, we just need to tell them where the card is going. It's important here that `face` is only provided when the client is supposed to be able to see the card.

In dealing, the server simply sends out `move` events in a round-robin fashion (as if the server is a player dealing cards). Once all of the players hands are full, a last `move` event is sent for the card going into the discard pile.

> `move` events are used for everything from melds to discards.

Here are some more examples of potential `move` events that you might see:

This example adds a new card to a meld. If the meld already exists, this would place the card on the left end of the meld (position `0`). Otherwise, a new meld would be created.

```json
{
	"type": "move",
	"card": {
		"id": "<random>",
		"face": {
			"suit": "hearts",
			"rank": "5"
		}
	},
	"destination": {
		"type": "meld",
		"meld_number": 0,
		"position": 0
	}
}
```

This is what an opponent drawing a card might look like:

```json
{
	"type": "move",
	"card": {
		"id": "<random>",
		"face": null
	},
	"destination": {
		"type": "player",
		"player_id": "<some ID>",
		"position": 3
	}
}
```

### Turns

As players take actions, it's the server's responsibility to keep track of whose turn it is, and ensure that no player can take actions out-of-turn. To inform clients of this turn state, a `turn` event is sent:

```typescript
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
```

The server should send everyone a new `turn` event any time either of these variables (`player_id` or `state`) changes.

### Ending the Round

Once a player runs out of cards, the server will send an `end` event. This event identifies the round winner, and sends a map of scores indicating how many points each player grants to the winner.

```typescript
/**
 * Indicates that the game has ended. The values of the remaining hands are tallied for scorekeeping. The client keeps track of score.
 **/
declare interface EndEvent {
    type: "end"
    /** The player ID of the winner. */
    winner_id: string
    /** A map (keyed by player ID) showing the hand values of the losing players. These point values will be added to the winner's score. "Rummy" should already be accounted for. */
    hand_values: Record<string, number>
}
```

For example, in a 3-player game, where player 2 wins, this might be the result:

```json
{
	type: "end",
	winner_id: "P2",
	hand_values: {
		"P1": 23,
		"P3": 41
	}
}
```

In this case, player 2 would gain 64 points, while the other player's scores would remain unchanged. The client can keep track of score.

### Gameplay Actions

There are various actions that the user can take throughout the game; and it's up to the server to ensure that these actions are legal.

```typescript
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
    /** The ID of the card to lay. */
    card_id: string
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
```

For example, any time a server recieves this JSON message in a websocket channel...

```json
{
	"type": "discard",
	"card_id": "123"
}
```

this indicates that the client is attempting to discard a card with ID `123`. Any time an action is successful, the server should respond by sending corresponding `move` events to all players, _including the player performing the action_. The client won't assume an action is successful until it recieves events from the server. The server also needs to send `turn` events as appropriate.

### Turn Example

Here's a sample of what a complete turn might look like in the websocket channel. The player draws a card, uses it to lay down a meld, then discards a different card, and the turn moves to the next player.

```json
// server to clients
// It's now the player's turn
{
	"type": "turn",
	"player_id": "<random string>",
	"state": "draw"
}

// client to server
// Draw a card
{
	"type": "draw",
	"card_id": "<card ID at the top [end] of either the deck or discard pile>"
}

// server to clients (face is null for other players)
// Card moves to player's hand, and the turn state changes
{
	"type": "move",
	"card": {
		"id": "<id from above>",
		"face": {
			"suit": "hearts",
			"rank": 3
		}
	},
	"destination": {
		"type": "hand",
		"player_id": "<random string>",
		"position": 2
	}
}
{
	"type": "turn",
	"player_id": "<same player ID>",
	"state": "play"
}

// client to server
// Player lays down a meld
{
	"type": "meld",
	"card_ids": ["<card 1>", "<card 2>", "<card 3>"]
}

// server to clients (face is revealed to all)
// Meld is valid, so cards move into the meld.
{
	"type": "move",
	"cards":[
		{
			"id": "<card 1>",
			"face": {
				"suit": "hearts",
				"rank": "A"
			}
		},
		{
			"id": "<card 2>",
			"face": {
				"suit": "hearts",
				"rank": "2"
			}
		},
		{
			"id": "<card 3>",
			"face": {
				"suit": "hearts",
				"rank": "3"
			}
		}
	]
	"destination": {
		"type": "meld",
		"meld_number": 0,
		"position": 0
	}
}

// client to server
// Player discards another card
{
	"type": "discard",
	"card_id": "<some other card ID>"
}

// server to clients
// Card moves to the top of the discard pile, and turn moves to the next player
{
	"type": "move",
	"card": {
		"id": "<another card>",
		"face": {
			"suit": "spades",
			"rank": "8"
		}
	},
	"destination": {
		"type": "discard"
	}
}
{
	"type": "turn",
	"player_id": "<next player>",
	"state": "draw"
}
```

### Exhausted Decks

When the deck is exhausted, the server will send an event to the client that replaces the deck.

```typescript
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
```

Whether or not the server shuffles the discard pile, it should generate a new card ID for each card.

It also needs to send a new `move` event to move the top card from the deck back to the discard pile.
