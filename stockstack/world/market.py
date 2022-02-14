import asyncio
import enum
from threading import Thread
from typing import Union, List, Tuple, Callable, Optional
import math

import aiofiles
import psycopg

from stockstack.settings import Settings
from stockstack.world import Company
from stockstack.world import MarketConfig
from stockstack.world import Order


class Market(Thread):
    class State(enum.IntEnum):
        CLOSE = 0
        EQUIVCALL = 1
        OPEN = 2

    def __init__(self, dbinfo: dict):
        super().__init__()
        self.dbinfo = dbinfo
        self.__dbconn: Optional[psycopg.AsyncConnection] = None

        self._price_stepsize_f = Market.PriceStepsizeFEval()  # Initial... won't work
        self._variancerate = 0.001  # too

    def run(self):
        Settings.logger.info(f"Market Starting")
        asyncio.run(self._run(), debug=True)

    async def _run(self):
        await self.init()
        while True:
            i = int(await MarketConfig.read(self.cursor, 'market_tick_n'))
            i, d = await self.tick(i)
            await MarketConfig.write(self.cursor, 'market_tick_n', str(i), update=True)
            await asyncio.sleep(d)

    async def tick(self, i) -> (int, float):
        if await MarketConfig.read(self.cursor, 'market_tick_active') == 'False':
            return i, 1
        if i == 0:  # 장전동시호가 3초
            return i + 1, 0.001
        if 0 < i < 29:  # 낮 1초 * 많이
            if i == 1:  # 낮 첫 틱
                await Order.tick(self.cursor)  # 장전동시호가 주문처리
                pass
            else:
                await Order.tick(self.cursor)  # 낮 틱 주문처리
            return i + 1, 0.003
        if i == 29:  # 장후동시호가 3초
            await Order.tick(self.cursor)  # 낮 마지막 틱 주문처리
            return i + 1, 0.001
        if i >= 30:  # 밤 3초
            if i == 30:  # 밤 첫 틱
                await Order.tick(self.cursor)  # 장후동시호가 주문처리
                await Company.tick(self.cursor)  # 회사의 시간
            return 0, 1
        return 0, 1

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

    async def init(self):
        self.__dbconn = await psycopg.AsyncConnection.connect(
            **self.dbinfo, autocommit=True
        )

        self._variancerate = float(await MarketConfig.read(self.cursor, "market_variancerate_float"))
        self._price_stepsize_f.compile(
            await MarketConfig.read(self.cursor, "market_pricestepsize_fe")
        )

        ## noinspection PyBroadException
        # try:
        #    await company.create(self.cursor, "CONSUMER", 0, factorysize=1)
        # except:
        #    pass

    def cursor(self, name: str = "") -> psycopg.AsyncCursor | psycopg.AsyncServerCursor:
        return self.__dbconn.cursor(name)


