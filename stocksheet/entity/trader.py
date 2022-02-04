from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from stocksheet.world.market import Market


class Trader:
    def __init__(self, market, traderident: int):
        self.market = market
        self.ident = traderident
        self.name = "(Unnamed)"
        self.wallet = None
        self.brainv = None

    @staticmethod
    async def create(market: "Market", traderident: int, name: str):
        async with market.cursor() as cur:
            await cur.execute(
                """INSERT INTO traders (tid, name) VALUES (%s, %s) RETURNING tid""",
                (traderident, name),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(market: "Market"):
        async with market.cursor() as cur:
            await cur.execute("""SELECT ARRAY(SELECT tid FROM traders)""")
            return (await cur.fetchone())[0]

    async def load(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT name, brainv FROM traders WHERE tid = %s""",
                (self.ident,),
            )
            r = await cur.fetchone()
            self.name = r[0]
            if r[1] is not None:
                self.brainv = np.array(r[1], dtype=np.float32, copy=True)

    async def dump(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """UPDATE traders SET (name, brainv) = (%s, %s) WHERE tid = %s""",
                (self.name, self.brainv.tolist() if self.brainv is not None else None, self.ident),
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
