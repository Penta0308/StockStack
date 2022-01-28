"""
Packet CmdLet
:parameter  e: str, command to exec
:returns    r: str, stdout
"""
import logging
from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stocksheet.network.connection import ClientConnection


@PACKETS.register(4)
@Privilege.require(Privilege.GLOBALADMINISTRATION)
class CmdLetAct(PacketR):
    def __init__(self, connection: 'ClientConnection', t, d):
        super().__init__(connection, t, d)

    async def process(self):
        e = self._d['e']
        logging.info(f"Execution UID: {self._connection.uid} CMD: {e}")
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
        logging.info(f"MarketStart UID: {self._connection.uid}")
        # TODO: MARKET START

        s = {}

        trans = MarketStartResp(self._connection, self._t, s)
        await trans.process()


@PACKETS.register(7)
class MarketStartResp(PacketT):
    pass
