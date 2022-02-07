import asyncio
from functools import wraps
from threading import Thread
from typing import Dict, Union, List, Tuple, Callable, Optional
import math

import aiofiles
import psycopg
from psycopg import sql

from stockstack.settings import Settings
from stockstack.world.stock import Stock
from stockstack.entity.trader import Trader


class MarketOpenedError(Exception):
    pass


class MarketClosedError(Exception):
    pass


class StockPriceLimitError(Exception):
    pass


class Market(Thread):
    def __init__(self, dbinfo: dict):
        super().__init__()
        self.__traders: Dict[int, Trader] = dict()
        self.__stocks: Dict[str, Stock] = dict()
        self._is_open: bool = False
        self._timestamp = 0
        self.dbinfo = dbinfo
        self.__dbconn: Optional[psycopg.AsyncConnection] = None

        self._price_stepsize_f = Market.PriceStepsizeFEval()  # Initial... won't work
        self._variancerate = 0.001  # too

        self.__tickT = 1.0

    def run(self):
        Settings.logger.debug(f"Market Starting")
        asyncio.run(self._run(), debug=True)

    async def _run(self):
        await self.init()
        i = 0
        while True:
            i = await self.tick(i)
            await asyncio.sleep(self.__tickT)

    async def tick(self, i):
        if i == 0:
            await self.open()
        if i == 299:
            await self.close()
            return 0
        return i + 1

    class PriceStepsizeFEval:
        _pricerange: Union[List[int], List[float]]
        _steps: Union[List[int], List[float]]

        def __init__(self):
            self._pricerange = list()
            self._steps = list()

        def compile(self, s: str) -> None:
            for p in s.split(" "):
                if p[0] == "/":
                    self._pricerange.append(int(p[1:]))
                else:
                    self._steps.append(int(p))

        def __call__(self, p: Union[int, float]) -> Union[int, float]:
            for n, r in enumerate(self._pricerange):
                if p < r:
                    return self._steps[n]
            try:
                return self._steps[-1]
            except:
                raise NotImplementedError

    def price_round(
            self, price: int | float, roundfunc: Callable[[int | float], int] = math.floor
    ) -> int | float:
        step = self._price_stepsize_f(price)
        return (roundfunc(price / step)) * step

    def price_variance(self, refprice: int) -> Tuple[int | float, int | float]:
        return (
            self.price_round(
                refprice + self.price_round(refprice * self._variancerate)
            ),
            self.price_round(
                refprice - self.price_round(refprice * self._variancerate)
            ),
        )

    @staticmethod
    def closedonly(f):
        @wraps(f)
        async def wrapper(self: "Market", *args, **kwargs):
            if self._is_open:
                raise MarketOpenedError
            else:
                return await f(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def openedonly(f):
        @wraps(f)
        async def wrapper(self: "Market", *args, **kwargs):
            if not self._is_open:
                raise MarketOpenedError
            else:
                return await f(self, *args, **kwargs)

        return wrapper

    async def init(self):
        schema = Settings.get()["stockstack"]["schema"]
        self.__tickT = Settings.get()["stockstack"]["tickT"]
        async with await psycopg.AsyncConnection.connect(
                **self.dbinfo, autocommit=False
        ) as dbconn:
            async with dbconn.cursor() as cur:
                await cur.execute(
                    sql.SQL("""CREATE SCHEMA IF NOT EXISTS {schemaname}""").format(
                        schemaname=sql.Identifier(schema)
                    ),
                    prepare=False,
                )
                await cur.execute(
                    """SELECT set_config('search_path', %s, false)""",
                    (schema,),
                    prepare=False,
                )

                async with aiofiles.open(
                        "stockstack/market_init.sql", encoding="UTF-8"
                ) as f:
                    await cur.execute(await f.read(), prepare=False)

        self.dbinfo["options"] = f"-c search_path={schema}"

        self.__dbconn = await psycopg.AsyncConnection.connect(
            **self.dbinfo, autocommit=True
        )

    def cursor(self, name: str = "") -> psycopg.AsyncCursor | psycopg.AsyncServerCursor:
        return self.__dbconn.cursor(name)

    @staticmethod
    async def config_read(
            curfactory: Callable[[], psycopg.AsyncCursor], key: str) -> str:
        async with curfactory() as cur:
            await cur.execute(
                """SELECT value from config WHERE key = %s""", (key,), prepare=True
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def config_write(
            curfactory: Callable[[], psycopg.AsyncCursor], key: str, value: str, update: bool = True) -> None:
        async with curfactory() as cur:
            if update:
                await cur.execute(
                    """INSERT INTO config (key, value) VALUES (%s, %s) ON CONFLICT DO UPDATE SET (key, value) = (excluded.key, excluded.value)""",
                    (key, value),
                    prepare=True,
                )
            else:
                await cur.execute(
                    """INSERT INTO config (key, value) VALUES (%s, %s)""",
                    (key, value),
                    prepare=True,
                )

    @closedonly
    async def open(self) -> None:
        """
        Start a day.
        :return:
        """

        Settings.logger.info("Market opening")

        self._variancerate = float(await Market.config_read(self.cursor, "market_variancerate_float"))
        self._price_stepsize_f.compile(
            await Market.config_read(self.cursor, "market_pricestepsize_fe")
        )

        for ticker in await Stock.searchall(self.cursor):
            await self.stock_load(ticker)

        for tid in await Trader.searchall(self.cursor):
            await self.trader_load(tid)

        for stock in self.__stocks.values():
            await stock.event_open()
        self._is_open = True

    @openedonly
    async def close(self) -> None:
        """
        End a day.
        :return:
        """

        Settings.logger.info("Market closing")

        self._is_open = False
        for stock in self.__stocks.values():
            await stock.event_close()

    async def trader_list(self):
        return self.__traders

    @closedonly
    async def trader_load(self, ident: int) -> None:
        t = self.__traders.get(ident)
        if t is None:
            t = Trader(self, ident)
        await t.load()
        self.__traders[ident] = t

    async def trader_get(self, ident: int) -> Trader:
        return self.__traders[ident]

    async def stock_list(self):
        """
        Show the stocks.
        :return:
        """
        return self.__stocks

    @closedonly
    async def stock_load(self, ticker: str) -> None:
        """
        When closed,
        Add a stock.
        :param ticker:
        :return:
        """
        s = self.__stocks.get(ticker)
        if s is None:
            s = Stock(self, ticker)
        await s.load()
        self.__stocks[ticker] = s

    async def stock_get(self, ticker: str) -> Stock:
        """
        Get a stock.
        :param ticker:
        :return:
        """
        return self.__stocks[ticker]

    '''@openedonly
    async def order_put(
            self,
            traderident: int,
            ticker: str,
            orderdirection: OrderDirection,
            count: int,
            price: Union[int, None] = None,
    ) -> None:
        """
        Trader에서 order을 넣을 것.
        :param traderident:
        :param ticker:
        :param orderdirection:
        :param count:
        :param price: 시장가 매매를 원할 시 None
        :return:
        """

        stock = await self.stock_get(ticker)
        price = self.price_round(price)

        if not (stock.lowlimit <= price <= stock.upplimit):
            raise StockPriceLimitError

        order = None
        if orderdirection == OrderDirection.Buy:
            order = OrderBuy(self, traderident, ticker, count, price, self._timestamp)
        elif orderdirection == OrderDirection.Sell:
            order = OrderSell(self, traderident, ticker, count, price, self._timestamp)
        self._timestamp += 1
        stock.order_put(order)
        order.activate()
        return order'''
