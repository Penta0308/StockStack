import typing
from typing import TYPE_CHECKING
from abc import abstractmethod
from enum import Enum

from stockstack.settings import Settings

if TYPE_CHECKING:
    from market import Market


async def tick(market: "Market"):
    # Settings.logger.debug("Order tick")
    pass


async def orderbuy_put(market: "Market", cid, ticker, amount, price):
    async with market.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorders (cid, ticker, amount, price) VALUES (%s, %s, %s, %s) ON CONFLICT (cid, ticker) DO UPDATE SET (amount, price) = (excluded.amount, excluded.price)""",
            (cid, ticker, +amount, price))
        return await cur.fetchone()


async def ordersell_put(market: "Market", cid, ticker, amount, price):
    async with market.cursor() as cur:
        await cur.execute(
            """INSERT INTO stockorders (cid, ticker, amount, price) VALUES (%s, %s, %s, %s) ON CONFLICT (cid, ticker) DO UPDATE SET (amount, price) = (excluded.amount, excluded.price)""",
            (cid, ticker, -amount, price))
        return await cur.fetchone()


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
