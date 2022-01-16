from io import StringIO
from contextlib import redirect_stdout

import websockets

from stockstack.network.packet import PacketR, PacketT
from stockstack.network.auth import Privilege


class CmdLetAct(PacketR):
    REQUIRE_PRIVILEGE = Privilege.ADMINISTRATION

    @staticmethod
    async def receive(websocket: websockets.WebSocketServerProtocol, d):
        from stockstack.settings import Settings
        f = StringIO()
        with redirect_stdout(f):
            exec(d, Settings.maincontext_get())
        s = f.getvalue()
        await CmdLetResp.send(websocket, str(s))


class CmdLetResp(PacketT):
    pass
