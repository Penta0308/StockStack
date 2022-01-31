import secrets
from enum import IntFlag
from typing import TYPE_CHECKING, Optional

import psycopg

from stocksheet.settings import Settings

if TYPE_CHECKING:
    from stocksheet.network.packets import PacketR

class Privilege(IntFlag):
    NONE = 0x0
    LOGINSTATE = 1 << 0
    MARKETADMINISTRATION = 1 << 62
    SYSTEMADMINISTRATION = 1 << 63
    ALL = 0xFFFFFFFFFFFFFFFF
    SAFEALL = ALL & ~SYSTEMADMINISTRATION

    @property
    def bitstring(self):
        return format(int(self.value), '064b')

    @staticmethod
    def require(privilege: 'Privilege'):
        def decorator(packet: 'PacketR'):
            packet.REQUIRE_PRIVILEGE = Privilege(privilege)
            return packet
        return decorator


class Auth:
    def __init__(self, dbinfo: dict):
        self.__dbconn = None
        self.__dbinfo = dbinfo

    async def start(self):
        self.__dbconn = await psycopg.AsyncConnection.connect(**self.__dbinfo, autocommit=True)
        async with self.__dbconn.cursor() as cur:
            await cur.execute("""SELECT COUNT(uid) FROM apiusers WHERE privilege = ((%s)::BIT(64))""",
                              (Privilege.SAFEALL.bitstring,))  # New schema
            if (await cur.fetchone())[0] == 0:
                root_uid = await self.user_add()
                await self.user_grant(root_uid, Privilege.SAFEALL)
                root_akey = await self.apikey_generate(root_uid)
                Settings.logger.warning(f'User MA {root_akey} Created')

    async def stop(self):
        if self.__dbconn:
            await self.__dbconn.close()

    async def user_add(self, uid: Optional[int] = None):
        async with self.__dbconn.cursor() as cur:
            if uid is None:
                await cur.execute("""INSERT INTO apiusers DEFAULT VALUES RETURNING uid""")
            else:
                await cur.execute("""INSERT INTO apiusers (uid) VALUES (%s) RETURNING uid""", (uid,))
            return (await cur.fetchone())[0]

    async def user_grant(self, uid: int, privilege: Privilege):
        async with self.__dbconn.cursor() as cur:
            await cur.execute(
                """UPDATE apiusers SET privilege = privilege |((%s)::BIT(64)) WHERE uid = %s RETURNING uid""",
                (privilege.bitstring, uid))
            return (await cur.fetchone())[0]

    async def user_revoke(self, uid: int, privilege: Privilege):
        async with self.__dbconn.cursor() as cur:
            await cur.execute(
                """UPDATE apiusers SET privilege = privilege &(~((%s)::BIT(64))) WHERE uid = %s RETURNING uid;""",
                (privilege.bitstring, uid))
            return (await cur.fetchone())[0]

    async def apikey_generate(self, uid: int):
        apikey = secrets.token_urlsafe(64)
        async with self.__dbconn.cursor() as cur:
            await cur.execute("""INSERT INTO apikeys (uid, apikey) VALUES (%s, %s) RETURNING apikey""",
                        (uid, apikey))
            return (await cur.fetchone())[0]

    async def apikey_check(self, apikey) -> int | None:
        async with self.__dbconn.cursor() as cur:
            await cur.execute("""SELECT uid FROM apikeys WHERE apikey = %s""", (apikey,), prepare=True)
            s = await cur.fetchone()
            if s is None:
                return None
            else:
                return s[0]

    async def privilege_check(self, uid: Optional[int], privilege: Privilege):
        if uid is None:
            return privilege == Privilege.NONE
        async with self.__dbconn.cursor() as cur:
            await cur.execute("""SELECT privilege FROM apiusers WHERE uid = %s""", (uid,), prepare=True)
            s = await cur.fetchone()
            pmask = Privilege(int(s[0], 2))
            return (pmask & privilege) == privilege
