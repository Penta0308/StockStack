import json
from typing import TYPE_CHECKING

import websockets
from websockets.exceptions import ConnectionClosedError

from stocksheet.network.packets import PACKETS, PacketR
from stocksheet.network.packets import internalerror

if TYPE_CHECKING:
    from stocksheet.network.gateway import Gateway


class ClientConnection:
    def __init__(self, gateway: 'Gateway', websocket: websockets.WebSocketServerProtocol):
        self.gateway = gateway
        self.websocket = websocket
        self.uid = None

    async def send(self, p):
        return await self.websocket.send(p)

    async def run(self):
        try:
            async for message in self.websocket:
                try:
                    jo = json.loads(message)
                    pclass = PACKETS.packet_lookup(int(jo['op']))
                    if issubclass(pclass, PacketR):
                        if await self.gateway.auth.privilege_check(self.uid, pclass.REQUIRE_PRIVILEGE):
                            recvpacket = pclass(self, jo.get('t'), jo['d'])
                            await recvpacket.process()
                        else:
                            raise PermissionError
                    else:
                        raise AttributeError("Not an input packet")
                except Exception as e:
                    await internalerror.InternalErrorResp(self, e).process()
        except ConnectionClosedError:
            return
