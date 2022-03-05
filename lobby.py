import random
from uuid import uuid4

from flask_sock import Server

from protocol import *


class Connection:
    def __init__(self, sock: Server):
        self.sock = sock
        self.id = uuid4().hex
        self.name = "Player"
        self.lobby = Lobby()
        connections[self.id] = self
        self.lobby.addPlayer(self)

    def sendEvent(self, event: Event):
        try:
            self.sock.send(event.encodeString())
        except Exception as e:
            print(e)
            try:
                self.lobby.removePlayer(self)
            except: pass
            try:
                self.sock.close()
            except: pass
            try:
                del connections[self.id]
            except: pass

connections: dict[str, Connection] = {}

class Lobby:
    def __init__(self):
        self.connections: list[str] = []
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
        except: pass

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
                    ) for p in map(lambda x: connections[x], self.connections)]
                )
            ))

lobbies: dict[str, Lobby] = {}

def addConnection(sock: Server):
    try:
        connection = Connection(sock)
        connections[connection.id] = connection
        try:
            while True:
                data: Union[str, bytes, None] = sock.receive(60 * 30) # Time out the user after 30min of inactivity
                if data is None:
                    raise RuntimeError("Connection timed out")
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                action = parseAction(data)
                try:
                    handleAction(action, connection)
                except Exception as e:
                    print(e)
                    raise RuntimeError("Error handling action {}".format(action))
        except Exception as e:
            print(e)
            try:
                connection.lobby.removePlayer(connection)
            except: pass
            try:
                removeConnection(connection.id)
            except: pass
    except: pass
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
from game import handleAction
