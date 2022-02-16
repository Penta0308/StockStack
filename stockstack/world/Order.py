import asyncio
import typing
from typing import TYPE_CHECKING
from abc import abstractmethod
from enum import Enum

from psycopg import rows

from stockstack.settings import Settings
from stockstack.world import Company, Wallet
from stockstack.world.Stock import Stock

if TYPE_CHECKING:
    from market import Market


async def _tick(market: "Market", ticker: str):
    async with market.dbconn.cursor() as cur:
        await cur.execute(
            """SELECT ots FROM stockorderspending WHERE ticker = %s ORDER BY ots ASC""",
            (ticker,),
        )
        ol = await cur.fetchall()
        for ots in (o[0] for o in ol):
            # async with market.dbconn.transaction():
            cur.row_factory = rows.dict_row
            await cur.execute(
                """WITH moved_rows AS (DELETE FROM stockorderspending WHERE ots = %s RETURNING *) INSERT INTO stockorders SELECT * FROM moved_rows RETURNING *""",
                (ots,))
            od = await cur.fetchone()
            #
            if od["amount"] > 0:  # buy
                if od["price"] is not None:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (amount < 0) AND ((price <= %s) OR (price IS NULL)) ORDER BY price ASC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], od["price"]),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        amount = min(abs(oa["amount"]), abs(od["amount"]))
                        price = od["price"]
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount - %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_create(od["cid"], ticker, amount)
                        await market.stockown_delete(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], -amount * price)
                        await Wallet.deltamoney(oa["cid"], +amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {oa['cid']} -> {od['cid']} by {price}/unit")
                        #
                        await Stock.updlastp(market.dbconn.cursor, ticker, price)
                        od["amount"] -= amount
                        if od["amount"] == 0:
                            break
                else:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (amount < 0) ORDER BY price ASC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"]),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        amount = min(abs(oa["amount"]), abs(od["amount"]))
                        price = oa["price"]
                        if price is None:
                            price = await Stock.getlastp(market.dbconn.cursor, ticker)
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount - %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_create(od["cid"], ticker, amount)
                        await market.stockown_delete(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], -amount * price)
                        await Wallet.deltamoney(oa["cid"], +amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {oa['cid']} -> {od['cid']} by {price}/unit")
                        #
                        await Stock.updlastp(market.dbconn.cursor, ticker, price)
                        od["amount"] -= amount
                        if od["amount"] == 0:
                            break
            elif od["amount"] < 0:  # sell
                if od["price"] is not None:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (amount > 0) AND ((price >= %s) OR (price IS NULL)) ORDER BY price DESC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], od["price"]),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        amount = min(abs(oa["amount"]), abs(od["amount"]))
                        price = od["price"]
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount - %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_delete(od["cid"], ticker, amount)
                        await market.stockown_create(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], +amount * price)
                        await Wallet.deltamoney(oa["cid"], -amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {od['cid']} -> {oa['cid']} by {price}/unit")
                        #
                        await Stock.updlastp(market.dbconn.cursor, ticker, price)
                        od["amount"] -= amount
                        if od["amount"] == 0:
                            break
                else:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (amount > 0) ORDER BY price DESC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"]),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        amount = min(abs(oa["amount"]), abs(od["amount"]))
                        price = oa["price"]
                        if price is None:
                            price = await Stock.getlastp(market.dbconn.cursor, ticker)
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount - %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET amount = amount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_delete(od["cid"], ticker, amount)
                        await market.stockown_create(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], +amount * price)
                        await Wallet.deltamoney(oa["cid"], -amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {od['cid']} -> {oa['cid']} by {price}/unit")
                        #
                        await Stock.updlastp(market.dbconn.cursor, ticker, price)
                        od["amount"] -= amount
                        if od["amount"] == 0:
                            break


async def tick(market: "Market"):
    async with market.dbconn.cursor() as cur:
        await cur.execute("""SELECT DISTINCT ticker FROM stockorderspending""")
        td = await cur.fetchall()
    await asyncio.gather(*[_tick(market, t[0]) for t in td])


async def clear(market: "Market"):
    async with market.dbconn.cursor() as cur:
        await cur.execute("""DELETE FROM stockorders""")


async def orderbuy_put(market: "Market", cid, ticker, amount, price):
    async with market.dbconn.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorderspending (cid, ticker, amount, price) VALUES (%s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT stockorderspending_cid_ticker_constraint DO UPDATE SET (amount, price) = (excluded.amount, excluded.price)""",
            (cid, ticker, +amount, price),
        )


async def ordersell_put(market: "Market", cid, ticker, amount, price):
    async with market.dbconn.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorderspending (cid, ticker, amount, price) VALUES (%s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT stockorderspending_cid_ticker_constraint DO UPDATE SET (amount, price) = (excluded.amount, excluded.price)""",
            (cid, ticker, -amount, price),
        )


"""    def order_process(self):
    self.sellorders.sort(key=self.sellpriorityfunc)
    self.buyorders.sort(key=self.buypriorityfunc)

    for so in self.sellorders:
        if so.price is None:
            for bo in self.buyorders:
                accprice = self.curprice if bo.price is None else bo.price
                tracount = min(bo.count, so.count)
                if tracount > 0:
                    so.trade(accprice, tracount)
                    bo.trade(accprice, tracount)
                    self.update_curprice(accprice)
                if not so.is_active():
                    break
        else:
            for bo in self.buyorders:
                if bo.price is None:
                    accprice = so.price
                    tracount = min(bo.count, so.count)
                    if tracount > 0:
                        so.trade(accprice, tracount)
                        bo.trade(accprice, tracount)
                        self.update_curprice(accprice)
                else:
                    if so.price <= bo.price:
                        accprice = (
                            so.price if so.timestamp < bo.timestamp else bo.price
                        )
                        tracount = min(bo.count, so.count)
                        if tracount > 0:
                            so.trade(accprice, tracount)
                            bo.trade(accprice, tracount)
                            self.update_curprice(accprice)
                if not so.is_active():
                    break

    sellorders: List[Order] = list()
    buyorders: List[Order] = list()

    while len(self.sellorders) > 0:
        i = self.sellorders.pop()
        if i.is_end():
            i.close()
        else:
            sellorders.append(i)

    while len(self.buyorders) > 0:
        i = self.buyorders.pop()
        if i.is_end():
            i.close()
        else:
            buyorders.append(i)

    self.sellorders = sellorders
    self.buyorders = buyorders"""
