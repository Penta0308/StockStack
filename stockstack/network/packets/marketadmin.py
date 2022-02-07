from typing import TYPE_CHECKING

from stockstack.entity.trader import Trader
from stockstack.network.packets import PACKETS, PacketR, PacketT
from stockstack.world.market import Market
from stockstack.world.stock import Stock

if TYPE_CHECKING:
    from stockstack.network.connection import WSConnection


@PACKETS.register(8)
class MarketConfAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        k = self._d["k"]
        v = self._d["v"]

        await Market.config_write(self._connection.gateway.cursor, k, v)

        d = {"k": k, "v": v}

        await MarketConfResp(self._connection, self._t, d).process()


@PACKETS.register(9)
class MarketConfResp(PacketT):
    pass


@PACKETS.register(10)
class StockCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        t = self._d["t"]
        n = self._d["n"]
        p = self._d["p"]
        r = self._d["r"]

        await Stock.create(self._connection.gateway.cursor, t, n, p, r)

        d = {"t": t, "n": n}

        await StockCreateResp(self._connection, self._t, d).process()


@PACKETS.register(11)
class StockCreateResp(PacketT):
    pass


@PACKETS.register(12)
class TraderCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        t = self._d["t"]
        n = self._d["n"]

        await Trader.create(self._connection.gateway.cursor, t, n)

        d = {"t": t, "n": n}

        await TraderCreateResp(self._connection, self._t, d).process()


@PACKETS.register(13)
class TraderCreateResp(PacketT):
    pass
