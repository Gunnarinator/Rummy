import random
from traceback import print_exc
from uuid import uuid4

from flask_sock import Server
from names import generateName

import events
from protocol import *

connections: dict[str, 'Connection'] = {}


class Connection:
    def __init__(self, sock: Server):
        self.sock = sock
        self.id = uuid4().hex
        self.name = generateName()
        self.lobby = Lobby()
        connections[self.id] = self
        self.lobby.addPlayer(self)

    def sendEvent(self, event: Event):
        if not self.id in connections:
            return
        try:
            self.sock.send(event.encodeString())
        except Exception:
            print_exc()
            removeConnection(self.id)
            try:
                self.lobby.removePlayer(self)
            except Exception:
                pass


class AILobbyPlayer:
    def __init__(self):
        self.name = generateName()
        self.id = uuid4().hex


class Lobby:
    def __init__(self):
        self.connections: list[str] = []
        self.aiPlayers: list[AILobbyPlayer] = []
        self.code = str(random.randint(0, 999999)).rjust(6, "0")
        self.settings = GameSettings()
        lobbies[self.code] = self

    def addPlayer(self, player: Connection):
        player.lobby.removePlayer(player)
        player.lobby = self
        self.connections.append(player.id)
        self.informPlayersOfLobby()

    def removePlayer(self, player: Connection):
        try:
            g = events.games.get(player.lobby.code)
            if g is not None:
                g.removePlayer(player.id)
            self.connections.remove(player.id)
            if len(self.connections) == 0:
                lobbies.pop(self.code)
            if g is None:
                self.informPlayersOfLobby()
        except:
            pass

    def informPlayersOfLobby(self):
        for player in map(lambda x: connections[x], self.connections):
            player.sendEvent(LobbyEvent(
                lobby=ClientLobby(
                    code=self.code,
                    current_player_id=player.id,
                    players=[LobbyPlayer(
                        id=p.id,
                        human=True,
                        name=p.name
                    ) for p in map(lambda x: connections[x], self.connections)] +
                    [LobbyPlayer(
                        id=p.id,
                        human=False,
                        name=p.name
                    ) for p in self.aiPlayers],
                    settings=self.settings
                )
            ))

    def addAIPlayer(self):
        if len(self.connections) + len(self.aiPlayers) >= 4:
            return
        self.aiPlayers.append(AILobbyPlayer())
        self.informPlayersOfLobby()

    def removeAIPlayer(self):
        if len(self.aiPlayers) == 0:
            return
        self.aiPlayers.pop()
        self.informPlayersOfLobby()


lobbies: dict[str, Lobby] = {}


def addConnection(sock: Server):
    try:
        connection = Connection(sock)
        try:
            while True:
                data: Union[str, bytes, None] = sock.receive(10)
                if data is None:
                    connection.sendEvent(PingEvent())
                    data: Union[str, bytes, None] = sock.receive(10)
                    if data is None:
                        raise RuntimeError("Connection timed out")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                action = parseAction(data)
                try:
                    events.handleAction(action, connection)
                except Exception:
                    print_exc()
        except Exception:
            print_exc()
            removeConnection(connection.id)
            try:
                connection.lobby.removePlayer(connection)
            except Exception:
                pass
    except:
        pass
    try:
        sock.close()
    except Exception:
        print_exc()


def removeConnection(id: str):
    try:
        connections[id].sock.close()
    except Exception:
        pass
    try:
        del connections[id]
    except Exception:
        pass


def parseAction(action: str) -> Action:
    o = json.loads(action)
    assert isinstance(o, dict)
    assert "type" in o
    assert o["type"] in actionTypeMap
    return actionTypeMap[o["type"]].decodeObject(o)
