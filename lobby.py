import random
from traceback import print_exc
from uuid import uuid4

from flask_sock import Server

import game
from names import generateName
from protocol import *


class Connection:
    def __init__(self, sock: Server):
        self.sock = sock
        self.id = uuid4().hex
        self.name = generateName()
        self.lobby = Lobby()
        connections[self.id] = self
        self.lobby.addPlayer(self)

    def sendEvent(self, event: Event):
        try:
            self.sock.send(event.encodeString())
        except Exception:
            print_exc()
            try:
                self.lobby.removePlayer(self)
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
            try:
                del connections[self.id]
            except:
                pass


connections: dict[str, Connection] = {}


class AILobbyPlayer:
    def __init__(self):
        self.name = generateName()
        self.id = uuid4().hex


class Lobby:
    def __init__(self):
        self.connections: list[str] = []
        self.aiPlayers: list[AILobbyPlayer] = []
        self.code = str(random.randint(0, 999999)).rjust(6, "0")
        lobbies[self.code] = self

    def addPlayer(self, player: Connection):
        player.lobby.removePlayer(player)
        player.lobby = self
        self.connections.append(player.id)
        self.informPlayersOfLobby()

    def removePlayer(self, player: Connection):
        try:
            self.connections.remove(player.id)
            if len(self.connections) == 0:
                lobbies.pop(self.code)
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
                    ) for p in self.aiPlayers]
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
        connections[connection.id] = connection
        try:
            while True:
                data: Union[str, bytes, None] = sock.receive()
                if data is None:
                    raise RuntimeError("Connection timed out")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                action = parseAction(data)
                try:
                    game.handleAction(action, connection)
                except Exception:
                    print_exc()
                    raise RuntimeError(
                        "Error handling action {}".format(action))
        except Exception as e:
            print_exc()
            try:
                connection.lobby.removePlayer(connection)
            except:
                pass
            try:
                removeConnection(connection.id)
            except:
                pass
    except:
        pass
    try:
        sock.close()
    except Exception as e:
        print(e)


def removeConnection(id: str):
    try:
        connections[id].sock.close()
    finally:
        del connections[id]


def parseAction(action: str) -> Action:
    o = json.loads(action)
    assert isinstance(o, dict)
    assert "type" in o
    assert o["type"] in actionTypeMap
    return actionTypeMap[o["type"]].decodeObject(o)


# import last so that Lobby and Connection easily available to game
