import secrets
from enum import IntFlag
from typing import Type, Optional

import psycopg


class Privilege(IntFlag):
    ADMINISTRATION = 1 << 63

    def to_bitstring(self):
        return format(int(self), '064b')


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

    def apikey_check(self, apikey):
        with self.__dbconn.cursor() as cur:
            cur.execute("""SELECT uid FROM stsk_auth.apikeys WHERE apikey = %s""", (apikey,), prepare=True)
            s = cur.fetchone()
            if s is None:
                return None
            else:
                return s[0]

    def privilege_check(self, uid: int, privilege: Type[Privilege]):
        pmask = 0
        with self.__dbconn.cursor() as cur:
            cur.execute("""SELECT privilege FROM stsk_auth.apiusers WHERE uid = %s""", (uid,), prepare=True)
            s = cur.fetchone()
            pmask = Privilege(int(s[0], 2))
        return (pmask & privilege) == privilege
