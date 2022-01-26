import asyncio
import json
import ssl
import typing
from typing import TYPE_CHECKING

import websockets

from stocksheet.network.auth import Auth
from stocksheet.network.packet import PACKET_OPCODE, PacketR, PacketT
from stocksheet.network.packets import cmdlet, internalerror

if TYPE_CHECKING:
    from stocksheet.worker import WorkerProcess


class Gateway:
    def __init__(self, auth: Auth, host='127.0.0.1', port=5000, sslcert=None):
        self.__host = host
        self.__port = port
        self.workerlut = dict()
        self.__eventloop = None
        self.__wsserver = None
        self.__auth = auth
        if sslcert is not None:
            # noinspection PyTypeChecker
            self.__ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__ssl_context.load_cert_chain(certfile=sslcert["cert"], keyfile=sslcert["key"])
        else:
            self.__ssl_context = None

    def workers_register(self, marketident: typing.Hashable, workerprocess: 'WorkerProcess'):
        self.workerlut[marketident] = workerprocess

    def start(self):
        self.__eventloop = asyncio.get_event_loop()
        self.__wsserver = self.__eventloop.run_until_complete(
            websockets.serve(self.handler_receive, self.__host, self.__port, ssl=self.__ssl_context))
        self.__eventloop.run_forever()

    def stop(self):
        self.__eventloop.stop()

    async def handler_receive(self, websocket: websockets.WebSocketServerProtocol):
        token = await websocket.recv()

        print(token)

        uid = self.__auth.apikey_check(token)

        if uid is None:
            await websocket.close(1011, "Authentication Failed")

        async for message in websocket:
            try:
                jo = json.loads(message)
                pclass = PACKET_OPCODE(jo['op'])
                if self.__auth.privilege_check(uid, pclass.REQUIRE_PRIVILEGE):
                    await pclass.receive(websocket, jo['d'])
                else:
                    raise PermissionError()
            except Exception as e:
                await internalerror.InternalErrorResp.send(websocket, e)
