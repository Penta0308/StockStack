from typing import TYPE_CHECKING

from stocksheet.settings import Settings
from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection


@PACKETS.register(6)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class MarketStartAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        Settings.logger.debug(f"MarketStart UID: {self._connection.uid}")
        # TODO: MARKET START

        s = {}

        trans = MarketStartResp(self._connection, self._t, s)
        await trans.process()


@PACKETS.register(7)
class MarketStartResp(PacketT):
    pass
