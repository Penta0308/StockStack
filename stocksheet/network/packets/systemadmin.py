"""
Packet CmdLet
:parameter  e: str, command to exec
:returns    r: str, stdout
"""
from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

from stocksheet.settings import Settings
from stocksheet.network.auth import Privilege
from stocksheet.network.packets import PACKETS, PacketR, PacketT

if TYPE_CHECKING:
    from stocksheet.network.connection import WSConnection


@PACKETS.register(4)
@Privilege.require(Privilege.SYSTEMADMINISTRATION)
class CmdLetAct(PacketR):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        e = self._d["e"]
        Settings.logger.warning(f"Execution UID: {self._connection.uid} CMD: {e}")
        f = StringIO()
        with redirect_stdout(f):
            exec(e, Settings.maincontext)
        s = f.getvalue()
        trans = CmdLetResp(self._connection, self._t, str(s))
        await trans.process()


@PACKETS.register(5)
class CmdLetResp(PacketT):
    def __init__(self, connection: "WSConnection", t, d):
        super().__init__(connection, t, d)

    async def process(self):
        self._d = {"r": self._d}
        await super().process()
