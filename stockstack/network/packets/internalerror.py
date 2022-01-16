import websockets

from stockstack.network.packet import PacketT


class InternalErrorResp(PacketT):
    @staticmethod
    async def send(websocket: websockets.WebSocketServerProtocol, d: Exception):
        str(d)
        await websocket.send(d)
        print(d)
        return
