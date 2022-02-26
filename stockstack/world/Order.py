import asyncio
from enum import IntEnum
from typing import TYPE_CHECKING, Union, TypedDict

from psycopg import rows

import stockstack
from stockstack.settings import Settings
from stockstack.world import Wallet
from stockstack.world import Stock

if TYPE_CHECKING:
    from market import Market, MarketSQLDesc


class OrderDirection(IntEnum):
    BUY = 1
    SELL = 2


class OrderInfo(TypedDict):
    ots: int
    cid: int
    ticker: str
    direction: OrderDirection
    iamount: int
    pamount: int
    price: Union[int, None]


async def _tick(market: Union["Market", "MarketSQLDesc"], ticker: str, i: int, n: int):
    async with market.dbconn.cursor() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT ots FROM stockorderspending WHERE ticker = %s ORDER BY ots ASC""",
            (ticker,),
        )

        ol = await cur.fetchall()
        hprice = None
        lprice = None
        tamount = 0
        tp = await Stock.getlastp(market.dbconn.cursor, ticker)
        for ots in (OrderInfo(**o)["ots"] for o in ol):
            # async with market.dbconn.transaction():
            cur.row_factory = rows.dict_row
            await cur.execute(
                """WITH moved_rows AS (DELETE FROM stockorderspending WHERE ots = %s RETURNING *) INSERT INTO stockorders SELECT * FROM moved_rows RETURNING *""",
                (ots,))
            od = OrderInfo(**await cur.fetchone())
            #
            if od["direction"] == OrderDirection.BUY:  # buy
                if od["price"] is not None:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (pamount < iamount) AND ((price <= %s) OR (price IS NULL)) AND (direction = %s) ORDER BY price ASC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], od["price"], OrderDirection.SELL),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        if od["iamount"] == od["pamount"]:
                            break
                        amount = min(oa["iamount"] - oa["pamount"], od["iamount"] - od["pamount"])
                        price = od["price"]
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_create(od["cid"], ticker, amount, price)
                        await market.stockown_delete(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], -amount * price)
                        await Wallet.deltamoney(oa["cid"], +amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {oa['cid']} -> {od['cid']} by {price}/unit")
                        #
                        if (hprice is None) or (hprice < price): hprice = price
                        if (lprice is None) or (lprice > price): lprice = price
                        tp = price
                        od["pamount"] += amount
                        tamount += amount
                else:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (pamount < iamount) AND (direction = %s) ORDER BY price ASC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], OrderDirection.SELL),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        if od["iamount"] == od["pamount"]:
                            break
                        amount = min(oa["iamount"] - oa["pamount"], od["iamount"] - od["pamount"])
                        price = oa["price"]
                        if price is None:
                            price = tp
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_create(od["cid"], ticker, amount, price)
                        await market.stockown_delete(oa["cid"], ticker, amount)
                        await Wallet.deltamoney(od["cid"], -amount * price)
                        await Wallet.deltamoney(oa["cid"], +amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {oa['cid']} -> {od['cid']} by {price}/unit")
                        #
                        if (hprice is None) or (hprice < price): hprice = price
                        if (lprice is None) or (lprice > price): lprice = price
                        tp = price
                        od["pamount"] += amount
                        tamount += amount
            elif od["direction"] == OrderDirection.SELL:  # sell
                if od["price"] is not None:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (pamount < iamount) AND ((price >= %s) OR (price IS NULL)) AND (direction = %s) ORDER BY price DESC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], od["price"], OrderDirection.BUY),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        if od["iamount"] == od["pamount"]:
                            break
                        amount = min(oa["iamount"] - oa["pamount"], od["iamount"] - od["pamount"])
                        price = od["price"]
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_delete(od["cid"], ticker, amount)
                        await market.stockown_create(oa["cid"], ticker, amount, price)
                        await Wallet.deltamoney(od["cid"], +amount * price)
                        await Wallet.deltamoney(oa["cid"], -amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {od['cid']} -> {oa['cid']} by {price}/unit")
                        #
                        if (hprice is None) or (hprice < price): hprice = price
                        if (lprice is None) or (lprice > price): lprice = price
                        tp = price
                        od["pamount"] += amount
                        tamount += amount
                else:
                    await cur.execute(
                        """SELECT * FROM stockorders WHERE (ticker = %s) AND (ots < %s) AND (iamount > pamount) AND (direction = %s) ORDER BY price DESC NULLS FIRST, ots ASC""",
                        (ticker, od["ots"], OrderDirection.BUY),
                    )
                    r = await cur.fetchall()
                    for oa in r:
                        if od["iamount"] == od["pamount"]:
                            break
                        amount = min(oa["iamount"] - oa["pamount"], od["iamount"] - od["pamount"])
                        price = oa["price"]
                        if price is None:
                            price = tp
                        # async with market.dbconn.transaction():
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, oa["ots"]),
                        )
                        await cur.execute(
                            """UPDATE stockorders SET pamount = pamount + %s WHERE ots = %s""",
                            (amount, od["ots"]),
                        )
                        await market.stockown_delete(od["cid"], ticker, amount)
                        await market.stockown_create(oa["cid"], ticker, amount, price)
                        await Wallet.deltamoney(od["cid"], +amount * price)
                        await Wallet.deltamoney(oa["cid"], -amount * price)
                        Settings.logger.info(f"Trading {ticker} {amount} {od['cid']} -> {oa['cid']} by {price}/unit")
                        #
                        if (hprice is None) or (hprice < price): hprice = price
                        if (lprice is None) or (lprice > price): lprice = price
                        tp = price
                        od["pamount"] += amount
                        tamount += amount

        if tamount > 0:
            await Stock.updlastp(market.dbconn.cursor, ticker, tp)

            tickn = i + n * stockstack.TICK_PER_DAY

            await cur.execute(
                """INSERT INTO stockpricechart (tickn, ticker, mprice, hprice, lprice, tamount) VALUES (%s, %s, %s, %s, %s, %s)""",
                (tickn, ticker, tp, hprice, lprice, tamount))


async def tick(market: Union["Market", "MarketSQLDesc"], i: int, n: int):
    async with market.dbconn.cursor() as cur:
        await cur.execute("""SELECT DISTINCT ticker FROM stockorderspending""")
        td = await cur.fetchall()
    await asyncio.gather(*[_tick(market, t[0], i, n) for t in td])


async def clear(market: Union["Market", "MarketSQLDesc"]):
    async with market.dbconn.cursor() as cur:
        # noinspection SqlInsertValues
        await cur.execute(
            """WITH moved_rows AS (DELETE FROM stockorders RETURNING *) INSERT INTO stockordershistory SELECT * FROM moved_rows;""")


async def orderbuy_put(market: Union["Market", "MarketSQLDesc"], cid, ticker, amount, price):
    async with market.dbconn.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorderspending (cid, ticker, direction, iamount, price) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT stockorderspending_cid_ticker_constraint DO UPDATE SET (iamount, price) = (excluded.iamount, excluded.price) RETURNING ots""",
            (cid, ticker, OrderDirection.BUY, amount, price),
        )
        return (await cur.fetchone())[0]


async def ordersell_put(market: Union["Market", "MarketSQLDesc"], cid, ticker, amount, price):
    async with market.dbconn.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorderspending (cid, ticker, direction, iamount, price) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT stockorderspending_cid_ticker_constraint DO UPDATE SET (iamount, price) = (excluded.iamount, excluded.price) RETURNING ots""",
            (cid, ticker, OrderDirection.SELL, amount, price),
        )
        return (await cur.fetchone())[0]


async def order_get(market: Union["Market", "MarketSQLDesc"], ots: int):
    async with market.dbconn.cursor() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT * FROM stockorderspending WHERE ots = %s""",
            (ots,),
        )
        v = await cur.fetchone()
        if v is not None: return v
        await cur.execute(
            """SELECT * FROM stockorders WHERE ots = %s""",
            (ots,),
        )
        return await cur.fetchone()
