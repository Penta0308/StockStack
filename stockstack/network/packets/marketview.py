from typing import TYPE_CHECKING

from stockstack.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stockstack.network.connection import WSConnection


@PACKETS.register(14)
class StockViewAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        k = self._d["k"]
        v = self._d["v"]

        await Stock.searchall()

        await Market.config_write(self._connection.gateway.cursor, k, v)

        d = {"k": k, "v": v}

        await StockViewResp(self._connection, self._t, d).process()


@PACKETS.register(15)
class StockViewResp(PacketT):
    pass
