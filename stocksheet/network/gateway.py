import asyncio
import os

import psycopg
from psycopg import sql
import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import ClientConnection
# noinspection PyUnresolvedReferences
from stocksheet.network.packets import hello, internalerror, systemadmin, marketadmin
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
                await cur.execute(sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schemaname}""").format(schemaname=sql.Identifier(self.schema)))
                await cur.execute("""SELECT set_config('search_path', %s, false)""", (self.schema,))
                await cur.execute(
                    """CREATE TABLE IF NOT EXISTS apiusers (uid SERIAL PRIMARY KEY, trader TEXT DEFAULT NULL, privilege BIT(64) DEFAULT 0::BIT(64) NOT NULL);
                    CREATE TABLE IF NOT EXISTS apikeys (uid INT REFERENCES apiusers (uid), apikey CHAR(86) PRIMARY KEY, ratelimit INT DEFAULT -1 NOT NULL);
                    CREATE TABLE IF NOT EXISTS stocks (ticker TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, totalamount INT DEFAULT 0 NOT NULL, parvalue INT DEFAULT 5000, closingprice INT DEFAULT 5000);
                    CREATE TABLE IF NOT EXISTS traders (tid SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL);
                    CREATE TABLE IF NOT EXISTS stockowns (tid INT REFERENCES traders (tid), ticker TEXT REFERENCES stocks (ticker), amount INT DEFAULT 0 NOT NULL)""")

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
