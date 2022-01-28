import asyncio
import os

import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import ClientConnection
# noinspection PyUnresolvedReferences
from stocksheet.network.packets import globaladmin, hello, internalerror, marketadmin


class Gateway:
    def __init__(self, auth: Auth, socket):
        self.__socket = socket
        self.__eventloop = None
        self.__wsserver = None
        self.auth = auth

    def start(self):
        self.__eventloop = asyncio.get_event_loop()
        self.__wsserver = self.__eventloop.run_until_complete(
            websockets.unix_serve(self.handler_receive, self.__socket))
        os.chmod(self.__socket, 0o660)
        self.__eventloop.run_forever()

    def stop(self):
        self.__eventloop.stop()

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await ClientConnection(self, websocket).run()
