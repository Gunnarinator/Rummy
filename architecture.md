# Architecture

A **client-server** architecture is used.

## Server

The server listens for incoming [WebSocket](https://www.html5rocks.com/en/tutorials/websockets/basics/) connections from the client. Once established, WebSockets act as a computer's form of a chat thread; either side (the client or the server) can send messages to each other. This connection is maintained throughout the player's session.

### JSON

However, WebSockets are limited to sending strings (or binary data, which we don't bother with). In order to send more complex data like arrays and objects, we need to use [JSON](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON). JSON is a standard format for converting these complex data types to a string so it can be saved to a file or sent over a network. Here's a sample (taken from the MDN article linked):

```json
{
  "squadName": "Super hero squad",
  "homeTown": "Metro City",
  "formed": 2016,
  "secretBase": "Super tower",
  "active": true,
  "members": [
    {
      "name": "Molecule Man",
      "age": 29,
      "secretIdentity": "Dan Jukes",
      "powers": [
        "Radiation resistance",
        "Turning tiny",
        "Radiation blast"
      ]
    }
  ]
}
```

In this example, JSON is specifying a dictionary (denoted by `{}`) with the keys of `squadName`, `homeTown`, `formed`, etc. Within that dictionary, `members` is an array (or list, denoted by `[]`) of other objects. In this case, it just contains one additional dictionary, which lists the name, age, identity, and powers of the member.

The great thing about JSON is that both the client and the server can understand it.

### Rummy Protocol

JSON defines _how_ we're going to send the data, but we haven't specified exactly _what_. This is where we define a protocol. Check out the [protocol document](protocol.md) for details.

The protocol defines how we communicate to the client that certain things happened, or how the client will communicate to the server that it wants to perform an action.

#### Actions

Actions are messages sent from the client to the server. They represent something that the client wants to do.

For example, the JSON message that a client would send to join another lobby would be:

```json
{
	"type": "join",
	"code": "123456"
}
```

`type` specifies the type of the action that the clinet wants (for example `join` to join a lobby, or `discard` to discard a card).

Other properties are specific to the type of action, and provide additional details. In this case, `code` specifies which lobby the client would like to join.

The [protocol document](protocol.md) details what types of actions are available.

#### Events

Events are messages sent from the server to the client. They notify clients of something that changed (either as a result of their own action, or something that another player did).

For example, an event that tells a client that a certain card was moved to the discard pile would look like this:

```json
{
	"type": "move",
	"card": {
		"id": "<a random string>",
		"face": {
			"suit": "spades",
			"rank": "8"
		}
	},
	"destination": {
		"type": "discard"
	}
}
```

In this case, the `type` of the event is `move`. The `card` property contains information about the card itself, including the `face` which is now revealed to all players. There is also `destination` that specifies that the card will move to the discard pile.

All changes in board state are communicated to clients using these events. The [protocol document](protocol.md) defines what events are available.

Information is only sent to the client on a need-to-know basis. This mitigates the possibility of cheating with a modified client. Specifically, faces are only sent to the client once the player is supposed to see the card. The `face` property is left `null` for face-down cards. Additionally, when the deck is reshuffled, an entirely new set of card IDs are selected for the reshuffled cards.

#### Rules

Rules are enforced on the server. Player actions will only have side-effects if the rules allow that action to take place. Illegal moves are ignored.

The [rules document](rules.md) details the rules enforced by the server, as well as the options that players may have in customizing the game rules.

## Client

The client consists of a standard webpage design featuring components of HTML, CSS, and JavaScript.

HTML defines the structure of the page. It specifies which things exist on the page and (roughly) where.

CSS defines the appearance of the page. Visual details such as colors, shadows, dimensions, and layouts are specified here.

JavaScript describes the dynamic functionality of the page. It handles user interaction, communication with the server, and ensures that the page is updated to indicate the correct game state.

### Rendering

The most complicated part of the UI is rendering the Rummy board itself.

There are three main ways to perform this kind of layout; each denoted by the language (HTML, CSS, or JavaScript) that does the heavy lifting:

#### HTML-Heavy

Doing everything in an HTML-heavy manner is most likely the easiest. This involves defining containers for different areas of the board, and then placing each card in a different container.

An example of how this could be done is as follows:

```html
<div class="board">
	<div class="center">
		<div class="deck">
			<div class="card"></div>
			<div class="card"></div>
			<div class="card"></div>
			<!-- more cards -->
		</div>
		<div class="discard">
			<div class="card"></div>
			<!-- more cards -->
		</div>
	</div>
	<div class="edge-bottom">
		<div class="player-hand spread">
			<div class="card"></div>
			<!-- more cards -->
		</div>
	</div>
	<!-- and so on -->
</div>
```

The issue with this approach is that the only way to move a card from one place to another is to remove it from its prior location in HTML, and then add it again to the new location. This means that HTML cannot animate smoothy between two containers; it simply doesn't have that capability.

So, unless we want our game to look more like a powerpoint than an interactive game, we can't rely on HTML to move cards around.

#### JavaScript-Heavy

Using JavaScript is probably the next easiest, although it's much more difficult. Here, we simply stick all of the cards into a pile on the board:

```html
<div class="board">
	<div class="card" id="card-1">
	<div class="card" id="card-2">
	<div class="card" id="card-3">
	<!-- and so on -->
</div>
```

We then calculate the position of each card within JavaScript, using a custom layout. For example, laying out the discard pile might look like this:

```javascript
// cardWidth and cardHeight are defined elsewhere

// Offset from the top of the window
let discardTop = cardHeight + 10
// Offset from the left side of the window
let discardLeft = window.innerWidth / 2 + 5

// Apply these offsets to the card to get it into position
let card = document.getElementByID(theCardWeNeed)
card.style.top = discardTop + "px"
card.style.left = discardLeft + "px"
```

However, the issue with this approach is that it involves a lot more juggling of HTML elements. For example, every time a player draws or places a card, all of the cards in their hand have to move to fill the gap. And when the window is resized, every card has to be moved to accomodate. Animations can also get complicated here.

#### CSS-Heavy

With Super Rummy, we went with a **CSS-heavy** implementation. The elements are thrown into the board in HTML just like with the JavaScript example, but this time CSS actually does the hard work.

JavaScript is responsible for defining a few [CSS variables](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties), and then CSS uses those variables to calculate the layout. For example, let's look at some cherry-picked styles relevant to a card in the current player's hand (at the bottom of the screen).

```css
.card {
	/* allows --position-offset-x and --position-offset-y variables to control the card's position */
	transform: translateX(var(--position-offset-x)) translateY(var(--position-offset-y));
	/* Animate any changes in position */
	transition: transform 0.5s ease-in-out;

	/* These variables are modified by JavaScript, specifying the size of the stack, and where the card is within */
	--stack-size: 1;
	/* Cards are stacked bottom to top, so index 0 is the bottom of the stack */
	/* Except for opponent's hands, the order here is reversed because you see it from the other direction */
	--stack-index: 0;
}

/* JavaScript will add .face-up and .spread classes to indicate that the card is in a stack that's spread out and face up */
.card.face-up.spread {
	/* Calculate the offset (from the center of the spread-out stack) to place the card, using the stack variables above */
	--stack-offset: calc(var(--card-spread-distance) * ((var(--stack-size) - 1) / -2 + var(--stack-index)));
}

/* .hand means the card is in a player's hand, and the pin indicates it should be at the bottom of the screen */
.card.hand[data-pin="bottom"] {
	/* Put the stack in the middle of the screen, but follow the --stack-offset to spread out the cards */
	--position-offset-x: var(--stack-offset);

	/* Pin this to the bottom of the screen */
	--position-offset-y: var(--edge-bottom);
}
```

This results in very smooth animations generated directly from the browser.

However, this does complicate the CSS code quite a bit. A potential future direction is to switch to JavaScript and see if there is a significant trade-off there; but that can be explored at a future date.
