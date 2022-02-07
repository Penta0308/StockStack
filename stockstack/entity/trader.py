from typing import Callable

import psycopg
from psycopg import rows


class Trader:
    def __init__(self, market, traderident: int):
        self.market = market
        self.ident = traderident
        self.name = "(Unnamed)"
        self.wallet = None

    @staticmethod
    async def create(
            curfactory: Callable[[], psycopg.AsyncCursor],
            traderident: int,
            name: str,
    ):
        async with curfactory() as cur:
            await cur.execute(
                """INSERT INTO traders (tid, name) VALUES (%s, %s) RETURNING tid""",
                (traderident, name),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(
            curfactory: Callable[[], psycopg.AsyncCursor], ):
        async with curfactory() as cur:
            await cur.execute("""SELECT tid FROM traders""")
            return await cur.fetchall()

    @staticmethod
    async def getinfo(
            curfactory: Callable[[], psycopg.AsyncCursor], tid: int):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute("""SELECT tid, name FROM traders WHERE tid = %s""", (tid,))
            return await cur.fetchone()

    async def load(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT name FROM traders WHERE tid = %s""",
                (self.ident,),
            )
            r = await cur.fetchone()
            self.name = r[0]

    async def dump(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """UPDATE traders SET (name) = (%s) WHERE tid = %s""",
                (
                    self.name,
                    self.ident,
                ),
            )

    async def event_open(self):
        await self.load()

    async def event_close(self):
        await self.dump()

    async def stockown_get(self, ticker: str):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT coalesce((SELECT amount from stockowns WHERE tid = %s AND ticker = %s LIMIT 1), 0)""",
                (self.ident, ticker),
            )
            r = await cur.fetchone()
            return r[0]

    async def order(
            self, ticker: str, orderdirection, count: int, price: None | int | float
    ):
        order = await self.market.order_put(
            self.ident, ticker, orderdirection, count, price
        )
