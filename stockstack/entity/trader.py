from typing import TYPE_CHECKING, Callable

import numpy as np
import psycopg

if TYPE_CHECKING:
    from stockstack.world.market import Market


class Trader:
    def __init__(self, market, traderident: int):
        self.market = market
        self.ident = traderident
        self.name = "(Unnamed)"
        self.wallet = None
        self.btype = None

    @staticmethod
    async def create(
            curfactory: Callable[[], psycopg.AsyncCursor],
            traderident: int,
            name: str,
            btype: str = None,
            bcoef: np.ndarray | None = None,
    ):
        async with curfactory() as cur:
            await cur.execute(
                """INSERT INTO traders (tid, name, btype) VALUES (%s, %s, %s) RETURNING tid""",
                (traderident, name, btype),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(
            curfactory: Callable[[], psycopg.AsyncCursor], ):
        async with curfactory() as cur:
            await cur.execute("""SELECT tid FROM traders""")
            return await cur.fetchall()

    async def load(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT name, btype FROM traders WHERE tid = %s""",
                (self.ident,),
            )
            r = await cur.fetchone()
            self.name = r[0]
            self.btype = r[1]
            if self.btype is not None:
                pass
                # TODO: BRAIN LOAD
            '''if r[1] is not None:
            await cur.execute(
                """SELECT name, ttype FROM traders WHERE tid = %s""",
                (self.ident,),
            )
                self.brain.setv(np.array(r[1], dtype=np.float32, copy=True))'''

    async def dump(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """UPDATE traders SET (name, btype) = (%s, %s) WHERE tid = %s""",
                (
                    self.name,
                    self.btype,
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
