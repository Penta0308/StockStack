"""
Packet CmdLet
:parameter  e: str, command to exec
:returns    r: str, stdout
"""

from io import StringIO
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

from stocksheet.network.packets import PACKETS, PacketR, PacketT
from stocksheet.network.auth import Privilege
from stocksheet.settings import Settings

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection


@PACKETS.register(4)
@Privilege.require(Privilege.GLOBALADMINISTRATION)
class CmdLetAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        e = self._d['e']
        self._connection.logger.info(f"Execution UID: {self._connection.uid} CMD: {e}")
        from stocksheet.settings import Settings
        f = StringIO()
        with redirect_stdout(f):
            exec(e, Settings.maincontext_get())
        s = f.getvalue()
        trans = CmdLetResp(self._connection, self._t, str(s))
        await trans.process()


@PACKETS.register(5)
class CmdLetResp(PacketT):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        self._d = {"r": self._d}
        await super().process()


@PACKETS.register(6)
@Privilege.require(Privilege.GLOBALADMINISTRATION)
class MarketStartAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        a = self._d['a']
        if not Settings.check_name(a):
            raise AttributeError

        self._connection.logger.info(f"MarketStart UID: {self._connection.uid} Name: {a}")
        self._connection.gateway.workermanager.workers_create(a)

        s = {'a': a}

        trans = MarketStartResp(self._connection, self._t, s)
        await trans.process()


@PACKETS.register(7)
class MarketStartResp(PacketT):
    pass


@PACKETS.register(8)
@Privilege.require(Privilege.GLOBALADMINISTRATION)
class ConnSetMarketAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        marketident = self._d['a']

        self._connection.logger.info(f"ConnSetMarket UID: {self._connection.uid} Name: {marketident}")

        mkts = self._connection.set_market(marketident)

        s = {'a': mkts}

        trans = ConnSetMarketResp(self._connection, self._t, s)
        await trans.process()


@PACKETS.register(9)
class ConnSetMarketResp(PacketT):
    pass
