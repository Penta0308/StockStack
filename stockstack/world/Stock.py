from typing import TYPE_CHECKING, List, Callable

import numpy as np
import psycopg
from psycopg import rows

if TYPE_CHECKING:
    from stockstack.world.market import Market


class Stock:
    @staticmethod
    async def create(
            curfactory: Callable[[], psycopg.AsyncCursor],
            ticker: str,
            name: str,
            parvalue: int | float = 5000,
            price: int | float | None = None,
    ):
        if price is None:
            price = parvalue
        async with curfactory() as cur:
            await cur.execute(
                """INSERT INTO market.stocks (ticker, parvalue, closingprice) VALUES (%s, %s, %s) RETURNING ticker""",
                (ticker, name, parvalue, price),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(
            curfactory: Callable[[], psycopg.AsyncCursor], ):
        async with curfactory() as cur:
            await cur.execute("""SELECT ARRAY(SELECT ticker FROM market.stocks)""")
            return (await cur.fetchone())[0]

    @staticmethod
    async def getinfo(
            curfactory: Callable[[], psycopg.AsyncCursor], ticker: str):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute(
                """SELECT ticker, cid, totalamount, parvalue, closingprice FROM market.stocks WHERE ticker = %s""",
                (ticker,))
            return await cur.fetchone()

    """"async def event_close(self):
        self.refprice = self.curprice
        if len(self.sellorders) > 0:
            sp = self.sellorders[0].price
            if sp < self.refprice:
                self.refprice = sp
        if len(self.buyorders) > 0:
            bp = self.buyorders[0].price
            if bp > self.refprice:
                self.refprice = bp
        while len(self.sellorders) > 0:
            self.sellorders.pop().close()
        while len(self.buyorders) > 0:
            self.buyorders.pop().close()

        await self.dump()"""
