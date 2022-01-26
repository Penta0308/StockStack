import asyncio
import json

import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.connection import ClientConnection
from stocksheet.network.packets import PACKETS

# noinspection PyUnresolvedReferences
from stocksheet.network.packets import globaladmin, hello, internalerror, marketadmin

class Gateway:
    def __init__(self, auth: Auth, port, host='127.0.0.1'):
        self.__host = host
        self.__port = port
        self.__eventloop = None
        self.__wsserver = None
        self.auth = auth

    def start(self):
        self.__eventloop = asyncio.get_event_loop()
        self.__wsserver = self.__eventloop.run_until_complete(
            websockets.serve(self.handler_receive, self.__host, self.__port))
        self.__eventloop.run_forever()

    def stop(self):
        self.__eventloop.stop()

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        await ClientConnection(self, websocket).run()
