import json
from typing import TYPE_CHECKING, Optional

import websockets

from stockstack.network.packets import PACKETS, PacketR
from stockstack.settings import Settings

# noinspection PyUnresolvedReferences
from stockstack.network.packets import hello, internalerror, globaladmin, marketadmin

if TYPE_CHECKING:
    from stockstack.network.gateway import Gateway
    from stockstack.worker import WorkerProcess


class ClientConnection:
    def __init__(self, gateway: 'Gateway', websocket: websockets.WebSocketServerProtocol):
        self.gateway = gateway
        self.websocket = websocket
        self.uid, self._marketident = None, None
        self.workerp: Optional['WorkerProcess'] = None
        self.logger = Settings.get_logger()

    def set_market(self, marketident):
        m = self.gateway.workermanager.workers_get(marketident)
        if m is None:
            raise AttributeError('Undefined market')
        self.workerp = m
        self._marketident = marketident
        return self._marketident

    def get_market(self):
        return self.workerp

    async def send(self, p):
        self.logger.debug(f"WebSocket Outbound > {p}")
        return await self.websocket.send(p)

    async def run(self):
        async for message in self.websocket:
            try:
                self.logger.debug(f"WebSocket Inbound  < {message}")
                jo = json.loads(message)
                pclass = PACKETS.packet_lookup(int(jo['op']))
                if issubclass(pclass, PacketR):
                    if self.gateway.auth.privilege_check(self.uid, pclass.REQUIRE_PRIVILEGE):
                        recvpacket = pclass(self, jo.get('t'), jo['d'])
                        await recvpacket.process()
                    else:
                        raise PermissionError
                else:
                    raise AttributeError("Not an input packet")
            except Exception as e:
                await internalerror.InternalErrorResp(self, e).process()
