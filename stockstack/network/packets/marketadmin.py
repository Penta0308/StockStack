from typing import TYPE_CHECKING

from stockstack.entity.trader import Trader
from stockstack.network.packets import PACKETS, PacketR, PacketT
from stockstack.world.company import Company
from stockstack.world.market import Market
from stockstack.world.marketconfig import MarketConfig

if TYPE_CHECKING:
    from stockstack.network.connection import WSConnection


@PACKETS.register(8)
class MarketConfAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        key = self._d["key"]
        value = self._d["value"]

        await MarketConfig.write(self._connection.gateway.cursor, key, value)

        d = {"kkey": key, "value": value}

        await MarketConfResp(self._connection, self._t, d).process()


@PACKETS.register(9)
class MarketConfResp(PacketT):
    pass


@PACKETS.register(10)
class CompanyCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        name = self._d["name"]
        worktype = self._d["worktype"]

        cid = await Company.create(self._connection.gateway.cursor, name, worktype)

        d = {"cid": cid}

        await CompanyCreateResp(self._connection, self._t, d).process()


@PACKETS.register(11)
class CompanyCreateResp(PacketT):
    pass


@PACKETS.register(12)
class TraderCreateAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        tid = self._d["tid"]
        name = self._d["name"]

        await Trader.create(self._connection.gateway.cursor, tid, name)

        d = {"tid": tid}

        await TraderCreateResp(self._connection, self._t, d).process()


@PACKETS.register(13)
class TraderCreateResp(PacketT):
    pass
