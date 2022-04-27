import net
from classes import *
from protocol import *


def handleAction(action: Action, connection: 'net.Connection'):
    print("Player " + connection.id +
          " (" + connection.name + "): " + str(action) + " action")
    lobby = connection.lobby
    # If the game hasn't started yet, this will be None
    game = games.get(lobby.code, None)

    if isinstance(action, PongAction):

        # A pong recieved from the client. Indicates that the connection is still active.
        pass

    elif isinstance(action, NameAction):

        # Sets the name of the current player.
        # The server should verify that the name is valid (not too long, not already in use, must contain a letter or number).
        #  - name (str): The name of the player.
        assert game is None
        n = action.name.strip()
        assert len(n) <= 20
        assert any(c.isalnum() for c in n)
        connection.name = n
        connection.lobby.informPlayersOfLobby()

    elif isinstance(action, AIAction):

        # Add or remove an AI player.
        # If adding a player, the server should verify that there's room in the lobby and that the game has not started.
        # If removing a player, the server should verify that there is an AI player in the lobby to remove, and the game has not started.
        #  - action (Literal["add", "remove"]): The action to perform.
        assert game is None
        if action.action == "add":
            connection.lobby.addAIPlayer()
        elif action.action == "remove":
            connection.lobby.removeAIPlayer()

    elif isinstance(action, JoinAction):

        # Joins a game. A game is left when the websocket connection is closed.
        # The server should verify that the game is not already running, and that thare are less than 4 players in the game.
        #  - code (str): The game code to join.
        assert game is None
        if action.code in net.lobbies and not action.code in games and len(net.lobbies[action.code].connections) + len(net.lobbies[action.code].aiPlayers) < 4:
            net.lobbies[action.code].addPlayer(connection)

    elif isinstance(action, StartAction):

        # Starts the current game.
        # The server should verify that at least two players are in the game.
        assert game is None
        assert len(lobby.connections) + len(lobby.aiPlayers) >= 2
        game = Game(lobby)
        game.start()

    elif isinstance(action, DrawAction):

        # Draws a card from the deck or the discard pile.
        # The server should verify that the card ID is at the top of the discard pile or the deck.
        #  - card_id (str): The ID of the card to draw. This can be the top card of the deck or the top card of the discard pile.
        assert game is not None
        player: Optional[BoardPlayer] = None
        for p in game.players:
            if p.connection is connection:
                player = p
                break
        assert player is not None
        game.assertCurrentTurn(connection)
        assert game.turn_has_drawn is False
        deckCard = game.deck.top()
        discardCard = game.discard.top()
        if deckCard is not None and deckCard.id == action.card_id:
            game.moveCardsToHand([deckCard], game.deck, player, player.getDestinationHandPosition(
                deckCard, game.settings))
            game.turn_has_drawn = True
            game.notifyPlayersOfTurnState()
        elif discardCard is not None and discardCard.id == action.card_id:
            game.moveCardsToHand([discardCard], game.discard, player, player.getDestinationHandPosition(
                discardCard, game.settings))
            game.turn_has_drawn = True
            game.non_discardable_card = discardCard
            game.notifyPlayersOfTurnState()
        else:
            raise RuntimeError("Invalid card ID")

    elif isinstance(action, MeldAction):

        # TODO: "Rummy"
        # TODO: A player can't go out until at least their second turn

        # Lay down some cards to create a meld.
        # The server should verify that (A) all cards are in the player's hand, and (B) that the cards form a valid meld.
        #  - card_ids (list[str]): A list of card IDs to lay down.
        assert game is not None
        player: Optional[BoardPlayer] = None
        for p in game.players:
            if p.connection is connection:
                player = p
                break
        assert player is not None
        game.assertCurrentTurn(connection)
        assert game.turn_has_drawn is True
        if game.settings.require_end_discard:
            # only allow a meld or lay if there's at least a card left over to discard
            assert len(action.card_ids) < len(player.hand.cards)
        assert all(any(c == h.id for h in player.hand.cards)
                   for c in action.card_ids)
        cards = [c for c in player.hand.cards if c.id in action.card_ids]
        assert funlib.checkLegal(cards, game.settings)
        funlib.sortStack(cards, game.settings)
        game.moveCardsToMeld(cards, player.hand, len(game.melds), 0)
        game.checkGameOver()

    elif isinstance(action, LayAction):

        # TODO: A player can't go out until at least their second turn

        # Lay down a card to add to an existing meld.
        # The server should verify that the card is in the player's hand, and that the card forms a valid meld.
        #  - card_ids (list[str]): The ID of the card to lay.
        #  - meld_number (int): The index of the meld to add the card to.
        assert game is not None
        player: Optional[BoardPlayer] = None
        for p in game.players:
            if p.connection is connection:
                player = p
                break
        assert player is not None
        game.assertCurrentTurn(connection)
        assert game.turn_has_drawn is True
        if game.settings.require_end_discard:
            # only allow a meld or lay if there's at least a card left over to discard
            assert len(action.card_ids) < len(player.hand.cards)
        assert len(game.melds) > action.meld_number
        assert all(any(c == h.id for h in player.hand.cards)
                   for c in action.card_ids)
        cards = game.melds[action.meld_number].cards + \
            [c for c in player.hand.cards if c.id in action.card_ids]
        assert funlib.checkLegal(cards, game.settings)
        funlib.sortStack(cards, game.settings)
        game.moveCardsToMeld(cards, player.hand, action.meld_number, 0)
        game.checkGameOver()

    elif isinstance(action, DiscardAction):

        # Discard a card. This ends the player's turn.
        # The server should verify that the card is in the player's hand.
        #  - card_id (str): The ID of the card to discard.
        assert game is not None
        player: Optional[BoardPlayer] = None
        for p in game.players:
            if p.connection is connection:
                player = p
                break
        assert player is not None
        game.assertCurrentTurn(connection)
        assert game.turn_has_drawn is True
        card: Optional[ServerCard] = None
        for c in player.hand.cards:
            if c.id == action.card_id:
                card = c
                break
        assert card is not None
        assert card is not game.non_discardable_card
        game.moveCardsToDiscard([card], player.hand)
        if not game.checkGameOver():
            game.nextTurn()

    elif isinstance(action, SettingsAction):

        # Changes the current game settings.
        # The server should verify that the settings are valid and that the game has not started.
        #  - settings (GameSettings): The new settings.
        assert game is None
        lobby.settings = action.settings
        lobby.informPlayersOfLobby()

    else:
        raise RuntimeError("Unknown action type")
