"""
Packet Hello
:parameter  akey: str, apikey
:returns    uid: None or int, uid
:returns    mkt: None or str, market name
"""
from typing import TYPE_CHECKING

from stocksheet.settings import Settings
from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection


@PACKETS.register(1)
@Privilege.require(Privilege.NONE)
class HelloAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        apikey = self._d['akey']
        uid = self._connection.gateway.auth.apikey_check(apikey)
        Settings.logger.info(f"Authentication UID: {str(uid)} Key: {apikey}")
        self._connection.uid = uid
        trans = HelloResp(self._connection, self._t,
                          {'uid': self._connection.uid})
        await trans.process()


@PACKETS.register(2)
class HelloResp(PacketT):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)
