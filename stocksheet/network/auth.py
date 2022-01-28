import secrets
from enum import IntFlag
from typing import TYPE_CHECKING, Type, Optional

import psycopg

if TYPE_CHECKING:
    from stocksheet.network.packets import PacketR


class Privilege(IntFlag):
    NONE = 0x0
    LOGINSTATE = 1 << 0
    GLOBALADMINISTRATION = 1 << 63
    ALL = 0xFFFFFFFFFFFFFFFF    # 주어지지 말아야 하는 권한

    @classmethod
    def to_bitstring(cls):
        return format(int(cls), '064b')

    @staticmethod
    def require(privilege: 'Privilege'):
        def decorator(packet: 'PacketR'):
            packet.REQUIRE_PRIVILEGE = Privilege(privilege)
            return packet
        return decorator


class Auth:
    def __init__(self, dbinfo: dict):
        self.__dbconn = psycopg.connect(**dbinfo, autocommit=True)
        pass

    def __del__(self):
        self.__dbconn.close()

    def user_add(self, uid: Optional[int] = None):
        with self.__dbconn.cursor() as cur:
            if uid is None:
                cur.execute("""INSERT INTO stsk_auth.apiusers DEFAULT VALUES RETURNING uid""")
            else:
                cur.execute("""INSERT INTO stsk_auth.apiusers (uid) VALUES (%s) RETURNING uid""", (uid,))
            return cur.fetchone()[0]

    def user_grant(self, uid: int, privilege: Type[Privilege]):
        with self.__dbconn.cursor() as cur:
            cur.execute("""UPDATE stsk_auth.apiusers SET privilege = privilege
                        |((%s)::BIT(64)) WHERE uid = %s RETURNING uid""", (privilege.to_bitstring(), uid))
            return cur.fetchone()[0]

    def user_get_market(self, uid: int) -> str:
        with self.__dbconn.cursor() as cur:
            cur.execute("""SELECT market FROM stsk_auth.apiusers WHERE uid = %s""", (uid, ))
            return cur.fetchone()[0]

    def user_revoke(self, uid: int, privilege: Type[Privilege]):
        with self.__dbconn.cursor() as cur:
            cur.execute("""UPDATE stsk_auth.apiusers SET privilege = privilege
                        &(~((%s)::BIT(64))) WHERE uid = %s RETURNING uid""", (privilege.to_bitstring(), uid))
            return cur.fetchone()[0]

    def apikey_generate(self, uid: int):
        apikey = secrets.token_urlsafe(64)
        with self.__dbconn.cursor() as cur:
            cur.execute("""INSERT INTO stsk_auth.apikeys (uid, apikey) VALUES (%s, %s) RETURNING apikey""",
                        (uid, apikey))
            return cur.fetchone()[0]

    def apikey_check(self, apikey) -> int | None:
        with self.__dbconn.cursor() as cur:
            cur.execute("""SELECT uid FROM stsk_auth.apikeys WHERE apikey = %s""", (apikey,), prepare=True)
            s = cur.fetchone()
            if s is None:
                return None
            else:
                return s[0]

    def privilege_check(self, uid: Optional[int], privilege: Privilege):
        if uid is None:
            return privilege == Privilege.NONE
        with self.__dbconn.cursor() as cur:
            cur.execute("""SELECT privilege FROM stsk_auth.apiusers WHERE uid = %s""", (uid,), prepare=True)
            s = cur.fetchone()
            pmask = Privilege(int(s[0], 2))
            return (pmask & privilege) == privilege
