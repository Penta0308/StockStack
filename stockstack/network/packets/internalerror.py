"""
Packet InternalError
:returns    en: str, error name
:returns    ed: str, error state (can be an empty string)
"""

from typing import TYPE_CHECKING

from stockstack.network.packets import PACKETS, PacketT

if TYPE_CHECKING:
    from stockstack.network.connection import ClientConnection


@PACKETS.register(3)
class InternalErrorResp(PacketT):
    def __init__(self, connection: 'ClientConnection', d: Exception):
        super().__init__(connection, None, d)

    async def process(self):
        self._d = {"en": type(self._d).__name__,
                   "ed": str(self._d)}
        await super().process()
