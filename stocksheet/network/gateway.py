import asyncio
import os

import psycopg
import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import ClientConnection
# noinspection PyUnresolvedReferences
from stocksheet.network.packets import globaladmin, hello, internalerror, marketadmin
from stocksheet.settings import Settings


class Gateway:
    def __init__(self, name, dbinfo, socket):
        self.__socket = socket
        self.__eventloop = None
        self.__wsserver = None
        self.auth = None
        self.name = name
        self.schema = f"m{self.name}"
        self.dbinfo = dbinfo

    def start(self):
        with psycopg.connect(**self.dbinfo, autocommit=False) as dbconn:
            with dbconn.cursor() as cur:
                template = Settings.templateenv.get_template("schema_init.sql")
                cur.execute(template.render(schemaname=self.schema))

        self.dbinfo['options'] = f"-c search_path={self.schema}"

        self.auth = Auth(self.dbinfo)

        self.__eventloop = asyncio.get_event_loop()
        self.__wsserver = self.__eventloop.run_until_complete(
            websockets.unix_serve(self.handler_receive, self.__socket))
        os.chmod(self.__socket, 0o660)
        self.__eventloop.run_forever()

    def stop(self):
        self.__eventloop.stop()

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await ClientConnection(self, websocket).run()
