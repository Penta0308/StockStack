import enum
from typing import Union, List, Tuple, Callable, Optional, AsyncIterator
import math

import aiofiles
import psycopg
from psycopg import AsyncTransaction

import stockstack
from stockstack.world import Order, Stock

class MarketSQLDesc:
    def __init__(self,
                 marketname: str,
                 dbinfo: dict,
                 initfile="stockstack/stockstack_market_default_init.sql", ):
        self.__marketname = marketname
        self.__initfile = initfile
        self.__schemaname = f"m{marketname}"
        self.__dbinfo = dbinfo
        self.dbconn: Optional[psycopg.AsyncConnection] = None

    async def init(self):
        async with await psycopg.AsyncConnection.connect(
                **self.__dbinfo, autocommit=True
        ) as dbconn:
            async with dbconn.cursor() as cur:
                await cur.execute(
                    f"""CREATE SCHEMA IF NOT EXISTS {self.__schemaname}""",
                    prepare=False,
                )
        self.__dbinfo["options"] = f"-c search_path={self.__schemaname}"

        self.dbconn = await psycopg.AsyncConnection.connect(
            **self.__dbinfo, autocommit=True
        )

        async with self.dbconn.cursor() as cur:
            async with aiofiles.open(self.__initfile, encoding="UTF-8") as f:
                await cur.execute(await f.read(), prepare=False)

    async def config_read(self, key: str) -> str:
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """SELECT value from lconfig WHERE key = %s""", (key,), prepare=True
            )
            return (await cur.fetchone())[0]

    async def config_write(
            self, key: str, value: str, update: bool = True
    ) -> None:
        async with self.dbconn.cursor() as cur:
            if update:
                await cur.execute(
                    """INSERT INTO lconfig (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET (key, value) = (excluded.key, excluded.value)""",
                    (key, value),
                    prepare=True,
                )
            else:
                await cur.execute(
                    """INSERT INTO lconfig (key, value) VALUES (%s, %s)""",
                    (key, value),
                    prepare=True,
                )

    async def stockowns_get_company(self, cid: int):
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """SELECT ticker, amount FROM stockowns WHERE cid = %s""", (cid,)
            )
            return await cur.fetchall()

    async def stockown_get_company(self, cid: int, ticker: str):
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """SELECT coalesce((SELECT amount FROM stockowns WHERE cid = %s AND ticker = %s), 0)""",
                (cid, ticker),
            )
            return (await cur.fetchone())[0]

    async def stockown_priceperunit(self, cid: int, ticker: str):
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """SELECT amprice FROM stockowns WHERE cid = %s AND ticker = %s""",
                (cid, ticker),
            )
            return (await cur.fetchone())[0]

    async def stockown_create(self, cid: int, ticker: str, amount: int, regprice: int):
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """INSERT INTO stockowns (cid, ticker, amount, amprice) VALUES (%s, %s, %s, %s)
                                 ON CONFLICT ON CONSTRAINT stockowns_cid_ticker_constraint DO UPDATE SET 
                                 amount = stockowns.amount + excluded.amount, 
                                 amprice = (stockowns.amprice * stockowns.amount + excluded.amprice * excluded.amount) / (stockowns.amount + excluded.amount)""",
                (cid, ticker, +amount, regprice),
            )
        return amount

    async def stockown_delete(self, cid: int, ticker: str, amount: int):
        async with self.dbconn.cursor() as cur:
            await cur.execute(
                """INSERT INTO stockowns (cid, ticker, amount) VALUES (%s, %s, %s)
                                 ON CONFLICT ON CONSTRAINT stockowns_cid_ticker_constraint DO UPDATE SET 
                                 amount = stockowns.amount + excluded.amount""",
                (cid, ticker, -amount),
            )
        return amount


class Market(MarketSQLDesc):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._price_stepsize_f = Market.PriceStepsizeFEval()  # Initial... won't work
        self._variancerate = 0.001  # too

    async def init(self):
        await super().init()

        self._variancerate = float(await self.config_read("market_variancerate_float"))
        self._price_stepsize_f.compile(
            await self.config_read("market_pricestepsize_fe")
        )

    async def tick(self, i: int, n: int):
        if i == 0:  # 장전동시호가 3초
            await Order.clear(self)
            pass
        elif i == 1:  # 낮 첫 틱
            await Order.tick(self)  # 장전동시호가 주문처리
            pass
        elif 1 < i < stockstack.TICK_PER_DAY - 2:
            await Order.tick(self)  # 낮 틱 주문처리
            pass
        elif i == stockstack.TICK_PER_DAY - 2:  # 장후동시호가 3초
            await Order.tick(self)  # 낮 마지막 틱 주문처리
            pass
        elif i == stockstack.TICK_PER_DAY - 1:  # 밤 첫 틱
            await Order.tick(self)  # 장후동시호가 주문처리
            pass
        elif i == stockstack.TICK_PER_DAY:
            await Stock.updclosp(self.dbconn.cursor)
            pass

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

