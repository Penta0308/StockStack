import asyncio
import os

import aiofiles as aiofiles
import psycopg
from psycopg import sql
import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import WSConnection

# noinspection PyUnresolvedReferences
from stocksheet.network.packets import login, internalerror, systemadmin, marketadmin
from stocksheet.settings import Settings
from stocksheet.world.market import Market


class Gateway:
    def __init__(self, name, dbinfo, socket):
        self.__runfuture = None
        self.__socket = socket
        self.__wsserver = None
        self.auth = None
        self.name = name
        self.schema = f"m{self.name}"
        self.dbinfo = dbinfo
        self.market = None

    def run(self):
        Settings.logger.debug(f"Gateway {self.name} Starting")
        asyncio.run(self._run())

    async def _run(self):
        async with await psycopg.AsyncConnection.connect(
                **self.dbinfo, autocommit=False
        ) as dbconn:
            async with dbconn.cursor() as cur:
                await cur.execute(
                    sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schemaname}""").format(
                        schemaname=sql.Identifier(self.schema)
                    ),
                    prepare=False,
                )
                await cur.execute(
                    """SELECT set_config('search_path', %s, false)""",
                    (self.schema,),
                    prepare=False,
                )

                async with aiofiles.open(
                        "stocksheet/schema_init.sql", encoding="UTF-8"
                ) as f:
                    await cur.execute(await f.read(), prepare=False)

        self.dbinfo["options"] = f"-c search_path={self.schema}"

        self.auth = Auth(self.dbinfo)
        await self.auth.start()

        self.market = Market(self.dbinfo)
        await self.market.init()

        async with websockets.unix_serve(self.handler_receive, self.__socket):
            Settings.logger.info(f"Gateway Listening at {self.__socket}")
            os.chmod(self.__socket, 0o660)
            await asyncio.Future()

        self.__wsserver.close()
        await self.__wsserver.wait_closed()

        await self.auth.stop()
        Settings.logger.info(f"Gateway Stopped")

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await WSConnection(self, websocket).run()
