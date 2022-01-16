import abc
import json

import websockets

from stockstack.network.auth import Privilege


PACKET_OPCODE_DICT = {
    0: 'AliveQuery',
    1: 'AliveResp',
    2: 'CmdLetAct',
    3: 'CmdLetResp'
}


class PacketR:
    REQUIRE_PRIVILEGE = Privilege(1 << 64 - 1)  # ALL PRIVILEGE

    @staticmethod
    @abc.abstractmethod
    async def receive(websocket: websockets.WebSocketServerProtocol, d):
        pass


class PacketT:
    @staticmethod
    async def send(websocket: websockets.WebSocketServerProtocol, d):
        await websocket.send(json.dumps(d))
