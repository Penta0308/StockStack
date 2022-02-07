import asyncio
import os
from typing import Optional

import psycopg
import websockets

from stockstack.network.connection import WSConnection

# noinspection PyUnresolvedReferences
from stockstack.network.packets import internalerror, marketadmin, marketview
from stockstack.settings import Settings


class Gateway:
    def __init__(self, dbinfo, socket):
        self.__runfuture = None
        self.__socket = socket
        self.__wsserver = None
        self.__dbinfo = dbinfo
        self.__dbconn: Optional[psycopg.AsyncConnection] = None

    def run(self):
        Settings.logger.debug(f"Gateway Starting")
        asyncio.run(self._run())

    def cursor(self, name: str = "") -> psycopg.AsyncCursor | psycopg.AsyncServerCursor:
        return self.__dbconn.cursor(name)

    async def _run(self):
        self.__dbconn = await psycopg.AsyncConnection.connect(
            **self.__dbinfo, autocommit=True
        )
        async with websockets.unix_serve(self.handler_receive, self.__socket):
            Settings.logger.info(f"Gateway Listening at {self.__socket}")
            os.chmod(self.__socket, 0o660)
            await asyncio.Future()

        self.__wsserver.close()
        await self.__wsserver.wait_closed()

        Settings.logger.info(f"Gateway Stopped")

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await WSConnection(self, websocket).run()
