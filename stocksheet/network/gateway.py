import asyncio
import os
import signal

import psycopg
import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import ClientConnection
# noinspection PyUnresolvedReferences
from stocksheet.network.packets import globaladmin, hello, internalerror, marketadmin
from stocksheet.settings import Settings


class Gateway:
    def __init__(self, name, dbinfo, socket):
        self.__runfuture = None
        self.__socket = socket
        self.__wsserver = None
        self.auth = None
        self.name = name
        self.schema = f"m{self.name}"
        self.dbinfo = dbinfo

    def run(self):
        Settings.logger.debug(f'Gateway {self.name} Starting')
        asyncio.run(self._run())

    async def _run(self):
        async with await psycopg.AsyncConnection.connect(**self.dbinfo, autocommit=False) as dbconn:
            async with dbconn.cursor() as cur:
                template = Settings.templateenv.get_template("schema_init.sql")
                await cur.execute(template.render(schemaname=self.schema))

        self.dbinfo['options'] = f"-c search_path={self.schema}"

        self.auth = Auth(self.dbinfo)
        await self.auth.start()

        async with websockets.unix_serve(self.handler_receive, self.__socket):
            Settings.logger.info(f'Gateway {self.name} Listening at {self.__socket}')
            os.chmod(self.__socket, 0o660)
            await asyncio.Future()

        self.__wsserver.close()
        await self.__wsserver.wait_closed()

        await self.auth.stop()
        Settings.logger.info(f'Gateway {self.name} Stopped')

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await ClientConnection(self, websocket).run()
