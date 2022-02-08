from typing import TYPE_CHECKING

from stockstack.entity.trader import Trader
from stockstack.network.packets import PACKETS, PacketR, PacketT
from stockstack.world.company import Company
from stockstack.world.stock import Stock

if TYPE_CHECKING:
    from stockstack.network.connection import WSConnection


@PACKETS.register(14)
class StockViewAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        ticker = self._d["ticker"]

        r = await Stock.getinfo(self._connection.gateway.cursor, ticker)

        d = r

        await StockViewResp(self._connection, self._t, d).process()


@PACKETS.register(15)
class StockViewResp(PacketT):
    pass


@PACKETS.register(16)
class StockListAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        r = await Stock.searchall(self._connection.gateway.cursor)

        d = r

        await StockListResp(self._connection, self._t, d).process()


@PACKETS.register(17)
class StockListResp(PacketT):
    pass


@PACKETS.register(18)
class TraderViewAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        tid = self._d["tid"]

        r = await Trader.getinfo(self._connection.gateway.cursor, tid)

        d = r

        await TraderViewResp(self._connection, self._t, d).process()


@PACKETS.register(19)
class TraderViewResp(PacketT):
    pass


@PACKETS.register(20)
class TraderListAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        r = await Trader.searchall(self._connection.gateway.cursor)

        d = r

        await TraderListResp(self._connection, self._t, d).process()


@PACKETS.register(21)
class TraderListResp(PacketT):
    pass


@PACKETS.register(22)
class CompanyViewAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        cid = self._d["cid"]

        r = await Company.getinfo(self._connection.gateway.cursor, cid)

        d = r

        await CompanyViewResp(self._connection, self._t, d).process()


@PACKETS.register(23)
class CompanyViewResp(PacketT):
    pass


@PACKETS.register(24)
class CompanyListAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        r = await Company.searchall(self._connection.gateway.cursor)

        d = r

        await CompanyListResp(self._connection, self._t, d).process()


@PACKETS.register(25)
class CompanyListResp(PacketT):
    pass
