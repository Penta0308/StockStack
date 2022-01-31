from typing import TYPE_CHECKING

from stocksheet.settings import Settings
from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection


@PACKETS.register(6)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class MarketStateAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):

        ts = self._d['s']

        if ts == "open":
            # TODO: MARKET OPEN

            d = {"s": "open"}

            await MarketStateResp(self._connection, self._t, d).process()
        elif ts == "close":
            # TODO: MARKET OPEN

            d = {"s": "close"}

            await MarketStateResp(self._connection, self._t, d).process()
        else:
            raise AttributeError


@PACKETS.register(7)
class MarketStateResp(PacketT):
    pass


@PACKETS.register(8)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class MarketConfAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):

        k = self._d['k']
        v = self._d['v']

        # TODO: CONFIG UPDATER

        d = {"k": k, "v": v}

        await MarketConfResp(self._connection, self._t, d).process()


@PACKETS.register(9)
class MarketConfResp(PacketT):
    pass
