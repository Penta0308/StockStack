from typing import TYPE_CHECKING, List

import numpy as np

from stocksheet.world.order import OrderDirection, Order

if TYPE_CHECKING:
    from stocksheet.world.market import Market


class Stock:
    def __init__(self, market: "Market", ticker: str):
        self.market = market
        self.ticker = ticker
        self.name = "(Unnamed)"
        self.sellorders: List[Order] = list()
        self.buyorders: List[Order] = list()
        self.refprice = 0  # 기준가격. 전일종가 또는 기세가
        self.curprice = 0  # 현재가격.
        self.upplimit = 0
        self.lowlimit = 0
        self.sellpriorityfunc = lambda x: (
            (-self.lowlimit if x is None else -x.price),
            x.timestamp,
            x.count,
        )
        self.buypriorityfunc = lambda x: (
            (self.upplimit if x is None else x.price),
            x.timestamp,
            x.count,
        )
        self.worktype = None

    @staticmethod
    async def create(
            market: "Market",
            ticker: str,
            name: str,
            parvalue: int | float = 5000,
            price: int | float | None = None,
    ):
        if price is None:
            price = parvalue
        async with market.cursor() as cur:
            await cur.execute(
                """INSERT INTO stocks (ticker, name, parvalue, closingprice) VALUES (%s, %s, %s, %s) RETURNING ticker""",
                (ticker, name, parvalue, price),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(market: "Market"):
        async with market.cursor() as cur:
            await cur.execute("""SELECT ARRAY(SELECT ticker FROM stocks)""")
            return (await cur.fetchone())[0]

    async def load(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """SELECT name, parvalue, closingprice, worktype FROM stocks WHERE ticker = %s""",
                (self.ticker,),
            )
            r = await cur.fetchone()
            self.name = r[0]
            self.refprice = r[2]
            self.worktype = np.array(r[3], dtype=np.float32, copy=True)

    async def dump(self):
        async with self.market.cursor() as cur:
            await cur.execute(
                """UPDATE stocks SET (name, closingprice, worktype) = (%s, %s, %s) WHERE ticker = %s""",
                (self.name, self.refprice, self.worktype.tolist(), self.ticker),
            )

    async def event_open(self):
        await self.load()

        self.upplimit, self.lowlimit = self.market.price_variance(self.refprice)

    async def event_close(self):
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

        await self.dump()

    def update_curprice(self, ordprice):
        self.curprice = ordprice

    def order_put(self, order: Order):
        if order.direction == OrderDirection.Sell:
            self.sellorders.append(order)
        elif order.direction == OrderDirection.Buy:
            self.buyorders.append(order)
        self.order_process()

    def order_process(self):
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
        self.buyorders = buyorders
