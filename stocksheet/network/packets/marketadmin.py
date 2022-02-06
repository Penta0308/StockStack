from typing import TYPE_CHECKING

from stocksheet.entity.trader import Trader
from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT
from stocksheet.world.stock import Stock

if TYPE_CHECKING:
    from stocksheet.network.connection import WSConnection


@PACKETS.register(6)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class MarketStateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):

        ts = self._d["s"]

        if ts == "open":
            await self._connection.gateway.market.open()

            d = {"s": "open"}

            await MarketStateResp(self._connection, self._t, d).process()
        elif ts == "close":
            await self._connection.gateway.market.close()

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
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        k = self._d["k"]
        v = self._d["v"]

        await self._connection.gateway.market.config_write(k, v)

        d = {"k": k, "v": v}

        await MarketConfResp(self._connection, self._t, d).process()


@PACKETS.register(9)
class MarketConfResp(PacketT):
    pass


@PACKETS.register(10)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class StockCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        t = self._d["t"]
        n = self._d["n"]
        p = self._d["p"]
        r = self._d["r"]

        await Stock.create(self._connection.gateway.market, t, n, p, r)

        await self._connection.gateway.market.stock_load(t)

        d = {"t": t, "n": n}

        await StockCreateResp(self._connection, self._t, d).process()


@PACKETS.register(11)
class StockCreateResp(PacketT):
    pass


@PACKETS.register(12)
@Privilege.require(Privilege.MARKETADMINISTRATION)
class TraderCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        t = self._d["t"]
        n = self._d["n"]

        await Trader.create(self._connection.gateway.market, t, n)

        await self._connection.gateway.market.trader_load(t)

        d = {"t": t, "n": n}

        await TraderCreateResp(self._connection, self._t, d).process()


@PACKETS.register(13)
class TraderCreateResp(PacketT):
    pass
