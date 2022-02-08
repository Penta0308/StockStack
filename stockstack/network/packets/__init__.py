import abc
import json

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from stockstack.network.connection import WSConnection


class Packet:
    OPCODE = None


class PacketR(Packet):
    def __init__(self, connection: "WSConnection", t, d):
        self._connection = connection
        self._t = t
        self._d = d

    @abc.abstractmethod
    async def process(self):
        pass


class PacketT(Packet):
    def __init__(self, connection: "WSConnection", t, d):
        self._connection = connection
        self._t = t
        self._d = d

    async def process(self):
        await self._dump_send()

    async def _dump_send(self):
        j = {"op": self.__class__.OPCODE, "d": self._d}
        if self._t is not None:
            j["t"] = self._t
        await self._connection.send(json.dumps(j, ensure_ascii=False))


class PACKETS:
    PACKETS_OPCODE = dict()

    @staticmethod
    def register(opcode: int):
        def decorator(packet: Packet):
            packet.OPCODE = opcode
            PACKETS.packet_register(opcode, packet)
            return packet

        return decorator

    @staticmethod
    def packet_register(opcode: int, packet) -> None:
        if PACKETS.PACKETS_OPCODE.get(opcode) is not None:
            raise KeyError("Conflicting Packet OPCode")
        PACKETS.PACKETS_OPCODE[opcode] = packet

    @staticmethod
    def packet_lookup(opcode: int):
        return PACKETS.PACKETS_OPCODE[opcode]
