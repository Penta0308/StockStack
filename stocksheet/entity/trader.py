import typing
from typing import TYPE_CHECKING, List, Dict

from stocksheet.world.wallet import Wallet

if TYPE_CHECKING:
    from stocksheet.world.market import Market


class Trader:
    def __init__(self, market, traderident: int):
        self.market = market
        self.ident = traderident
        self.name = "(Unnamed)"
        self.wallet = Wallet(self.ident)

    @staticmethod
    async def create(market: "Market", traderident: int, name: str):
        async with market.cursor() as cur:
            await cur.execute(
                """INSERT INTO traders (tid, name) VALUES (%s, %s) RETURNING tid""",
                (traderident, name),
            )
            return (await cur.fetchone())[0]

    async def load(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT name FROM traders WHERE tid = %s""",
                (self.ident,),
            )
            self.name = (await cur.fetchone())[0]

    async def dump(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """UPDATE traders SET (name) = (%s) WHERE tid = %s""",
                (self.name, self.ident),
            )

    async def event_open(self):
        await self.load()

    async def event_close(self):
        await self.dump()

    async def stockown_get(self, ticker: str):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT coalesce((SELECT (amount) from stockowns WHERE tid = %s AND ticker = %s), 0)""",
                (self.ident, ticker),
            )
            r = await cur.fetchone()
            self.name = r[0]

    async def order(
            self, ticker: str, orderdirection, count: int, price: None | int | float
    ):
        order = await self.market.order_put(
            self.ident, ticker, orderdirection, count, price
        )
