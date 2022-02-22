# Rummy Game Rules

## Dealing

The game starts with a single 52-card shuffled deck.

> **Variable:** Players can elect to use 1 (default), 2 or 3 decks.
>
> Name (technical): Number of decks (`deck_count`)  
> Values [default]: [`1`], `2`, `3`

Cards are delt by the server in a round-robin fashion. With only 2 players, 10 cards are delt to each player. For 3-4 player games, 7 cards are delt per player. 5-6 player games are dealt with 6 cards per player.

> **Variable:** For games with multiple decks, players can increase the number of cards to up to 12 cards for 2 players, 10 cards for 3-4 players, or 8 cards for 5-6 players.
>
> Name (technical): Card count (`hand_size`)  
> Description: Number of cards delt to each player at the start of a round.  
> Values: 6-12

## Playing

Players take turns going to the left. In the first round, the first player to join the lobby has the first turn. In subsequent rounds, the player with the first turn is passed off to the left.

> **Variable:** Players can choose instead to start each round with the winner from the previous round. In a round where there is no "winner," the same starting person starts again the next round.
>
> Name (technical): Start the round with... (`first_turn`)  
> Values [default]: [`"next_player"`], `"prev_winner"`

The first move in a turn must be to draw a card. This can either be the top card of the discard pile, or the top card of the deck.

> **Variable:** Players can choose to allow drawing multiple cards from the discard pile. In this case, the top 5 cards of the discard pile are shown, and the players may choose to draw one of them. *However,* they must also take all of the cards above the one they choose.
>
> For example, if the discard contains a 1, a 2, and a 3 (with the 3 on top), a player can choose to take just the 3, both the 2 and the 3, or all 3 cards.
>
> Name (technical): Open discard pile (`allow_draw_choice`)  
> Description: Show more of the discard pile and allow players to choose how many cards to draw.  
> Values [default]: `true`, [`false`]

After drawing a card, the player can take one of 3 actions:

 1. **Create a meld**

    A meld consists of 3 or more cards. These can form a **run**, where cards of the same suit can be layed in a sequence, or a **set** consisting of a set of cards of the same rank. By default, aces are low, denoting a rank of 1.

    > **Variable:** Players can elect to allow runs to contain cards of different suits.
    >
    > Name (technical): Allow runs with mixed suits (`allow_run_mixed_suit`)  
    > Values [default]: `true`, [`false`]
    >
    > **Variable:** Players can elect to restrict melds to only 3 or 4 cards (so that runs or sets from multiple decks can't exceed this size).
    >
    > Name (technical): Limit meld size to 4 cards (`limit_meld_size`)  
    > Values [default]: `4`, [`null`]
    >
    > **Variable:** Players can choose whether aces are high (rank 14) or low (rank 1).
    >
    > Name (technical): Ace rank (`ace_rank`)  
    > Values [default]: [`low`], `high`

2. **Lay onto a meld**

    If a player has a card which can be added to a meld on the table to form a new, valid meld, they may add their card to the meld. It does not matter who created the original meld. But if there is a size restriction (see variable above), they cannot add cards to exceed this restriction.

3. **Discard a card**

    At the end of a turn, players must choose a card in their hand to add to the discard pile. If they started the turn by drawing from the discard pile, they must discard a different card.

Players can optionally complete steps 1 and 2 as many times as they wish, but they must complete step 3 to end the turn.

## Exhausting the Deck

When the face-down deck is exhausted of cards, the next player has two choices to start the turn. They can draw the top card from the discard pile as normal, or they can turn over the discard pile (without shuffling, by default), and the top card of the new face-down deck is flipped to form the new discard pile. After flipping the deck, the player can choose to draw either from the deck, or to take the card from the discard pile as normal.

> **Variable:** Players can choose to have the server shuffle the deck when the discard pile is flipped.
> **Variable:** Players may elect instead to simply end the round when the deck is exhausted. In this case, the values of each player's hand (see scoring below) is _subtracted_ from their score, though the score cannot drop below zero. The same hand-laying process described below takes place in as well, where all players will lay down their current cards as possible to minimize their hand's value.
>
> Name (technical): When the deck is exhausted... (`deck_exhaust`)  
> Values [default]: [`flip_discard`], `shuffle_discard`, `end_round`

## Going Out

A player wins a round by getting rid of all cards in their hand. This can be done either by laying cards down onto a meld, or discarding the last card.

> **Variable:** Players can choose to require ending the round on a discard. This means that a player cannot lay down a meld using all of their cards; they must discard a card to end their turn.
>
> Name (technical): Require a discard to go out... (`require_end_discard`)  
> Description: Requires players to discard at the end of the winning turn.  
> Values [default]: `true`, [`false`]

After a player goes out, other players have the opportunity to lay down cards before the round ends. In Super Rummy, this is automatically done by the server to minimize the ending hand value. This takes place in the normal turn order, going once around the table.

> **Variable:** Players automatically laying down cards at the end can be disabled.
>
> Name (technical): All players lay down eligible cards at the end of a round (`lay_at_end`)  
> Values [default]: [`true`], `false`

Players must wait until at least their second turn to go out.

## Rummy

A player may call "rummy" if, after starting a turn and drawing a card, they can immediately lay down all of their cards to create a new meld. This also implies that they "go out."

> If the rule requiring discards is enabled, a player must also discard a card when declaring "rummy," so this requires them to lay down all cards but one.

## Scoring

At the end of a round, all players that still have cards will have their values added up. Numbers are scored as-is. Face cards are given a value of 10. Aces are 1 when low, or 11 when high.

The losing players' values are added to the winner's score.

If the winner declared "rummy," hand values are doubled.
