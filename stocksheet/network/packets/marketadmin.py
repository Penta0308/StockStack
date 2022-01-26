"""
Packet CmdLet
:parameter  e: str, command to exec
:returns    r: str, stdout
"""

from typing import TYPE_CHECKING

from stocksheet.network.packets import PACKETS, PacketR, PacketT
from stocksheet.network.auth import Privilege
from stocksheet.settings import Settings

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection

"""
@PACKETS.register(10)
@Privilege.require(Privilege.GLOBALADMINISTRATION)  # TODO: Creative Action
class MarketCreateAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        self._connection.logger.info(f"MarketCreate UID: {self._connection.uid} Name: {a}")

        s = {'a': a}

        trans = MarketCreateResp(self._connection, self._t, s)
        await trans.process()


@PACKETS.register(11)
class MarketCreateResp(PacketT):
    pass
"""
