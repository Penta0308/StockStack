import json
from typing import TYPE_CHECKING, Union

import websockets
from websockets.exceptions import ConnectionClosedError

from stocksheet.network.packets import PACKETS, PacketR
from stocksheet.network.packets import internalerror
from stocksheet.settings import Settings

if TYPE_CHECKING:
    from stocksheet.network.gateway import Gateway


class WSConnection:
    websocket: websockets.WebSocketServerProtocol

    def __init__(
            self, gateway: Union[None, "Gateway"], websocket: websockets.WebSocketCommonProtocol,
            bypassauth: bool = False
    ):
        self.gateway = gateway
        self.websocket = websocket
        self.uid: None | int = None
        self.bypassauth: bool = bypassauth

    async def send(self, p: str) -> None:
        await self.websocket.send(p)

    async def run(self) -> None:
        try:
            while True:
                message = await self.websocket.recv()
                try:
                    jo = json.loads(message)
                    pclass = PACKETS.packet_lookup(int(jo["op"]))
                    if issubclass(pclass, PacketR):
                        if self.bypassauth or await self.gateway.auth.privilege_check(
                                self.uid, pclass.REQUIRE_PRIVILEGE
                        ):
                            recvpacket = pclass(self, jo.get("t"), jo["d"])
                            await recvpacket.process()
                        else:
                            raise PermissionError
                    else:
                        raise AttributeError("Not an input packet")
                except Exception as e:
                    Settings.logger.debug(e, exc_info=True)
                    await internalerror.InternalErrorResp(self, e).process()
        except ConnectionClosedError:
            return
