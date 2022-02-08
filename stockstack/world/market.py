import asyncio
import enum
from threading import Thread
from typing import Union, List, Tuple, Callable, Optional
import math

import aiofiles
import psycopg
from psycopg import sql

from stockstack.settings import Settings
from stockstack.world.company import Company
from stockstack.world.order import Order


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
        Settings.logger.debug(f"Market Starting")
        asyncio.run(self._run(), debug=True)

    async def _run(self):
        await self.init()
        while True:
            i = int(await self.config_read(self.cursor, 'market_tickn'))
            i, d = await self.tick(i)
            await self.config_write(self.cursor, 'market_tickn', str(i), update=True)
            await asyncio.sleep(d)

    async def tick(self, i) -> (int, float):
        if i == 0:  # 장전동시호가 3초
            return i + 1, 1
        if 0 < i < 29:  # 낮 1초 * 많이
            if i == 1:  # 낮 첫 틱
                await Order.tick(self.cursor)  # 장전동시호가 주문처리
                pass
            else:
                await Order.tick(self.cursor)  # 낮 틱 주문처리
            return i + 1, 0.03
        if i == 29:  # 장후동시호가 3초
            await Order.tick(self.cursor)  # 낮 마지막 틱 주문처리
            return i + 1, 1
        if i >= 30:  # 밤 3초
            if i == 30:  # 밤 첫 틱
                await Order.tick(self.cursor)  # 장후동시호가 주문처리
                await Company.tick(self.cursor)  # 회사의 시간
            return 0, 3
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
        schema = Settings.get()["stockstack"]["schema"]
        async with await psycopg.AsyncConnection.connect(
                **self.dbinfo, autocommit=True
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

        self._variancerate = float(await Market.config_read(self.cursor, "market_variancerate_float"))
        self._price_stepsize_f.compile(
            await Market.config_read(self.cursor, "market_pricestepsize_fe")
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
                    """INSERT INTO config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET (key, value) = (excluded.key, excluded.value)""",
                    (key, value),
                    prepare=True,
                )
            else:
                await cur.execute(
                    """INSERT INTO config (key, value) VALUES (%s, %s)""",
                    (key, value),
                    prepare=True,
                )

