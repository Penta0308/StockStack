import asyncio
import logging
import time

import aiofiles
import psycopg

from stockstack import TICK_PER_DAY
from stockstack.settings import Settings
from stockstack.world import WorldConfig, Wallet, Company
from stockstack.world.market import Market

global dbconn


def run():
    Settings.logger.debug(f"Starting")
    Settings.load()

    for d in Settings.get()["stockstack"]["markets"]:
        name = d["name"]
        Settings.markets[name] = Market(
            name,
            Settings.get()["database"],
            initfile=d["initfile"]
        )

    def cursor(*args, **kwargs) -> psycopg.AsyncCursor | psycopg.AsyncServerCursor:
        return dbconn.cursor(*args, **kwargs)

    async def init():
        global dbconn
        dbconn = await psycopg.AsyncConnection.connect(
            **(Settings.get()["database"]), autocommit=True
        )
        async with dbconn.cursor() as cur:
            async with aiofiles.open(
                    "stockstack/stockstack_init.sql", encoding="UTF-8"
            ) as f:
                await cur.execute(await f.read(), prepare=False)
        # noinspection PyBroadException
        try:
            initdata = Settings.get()["stockstack"]["init"]
            async with dbconn.cursor() as cur:
                await cur.execute(
                    """INSERT INTO world.companies (cid, name, worktype, listable) VALUES (0, 'CONSUMER', 0, FALSE) RETURNING cid"""
                )
                await cur.execute(
                    """INSERT INTO world.companyfactories (cid, fid, factorysize) VALUES (0, 0, %s)""",
                    (initdata["population"],),
                )
            await Wallet.putmoney(0, initdata["population"] * initdata["gnpp"])
        except:
            pass

    async def _run():
        await init()
        await asyncio.gather(*[market.init() for market in Settings.markets.values()])
        # await vtrader.init(Settings.get()["stockstack"]["vtrader"]["n"])
        while True:
            t = time.time()
            i, n = int(await WorldConfig.read(cursor, "market_tick_n")), int(
                await WorldConfig.read(cursor, "market_day_n"))
            (i, n), d = await tick(i, n)
            await WorldConfig.write(cursor, "market_tick_n", str(i), update=True)
            await WorldConfig.write(cursor, "market_day_n", str(n), update=True)
            ds = t + d - time.time()
            if ds > 0: await asyncio.sleep(ds)
            #else: Settings.logger.info(f"Tick Overloading: {i}")

    async def tick(i, n) -> ((int, int), float):
        if await WorldConfig.read(cursor, "market_tick_active") == "False": return (i, n), 1

        # noinspection PyUnusedLocal
        async def mastertick(i, n):
            if i == 2:
                await Company.seq1(cursor)  # 회사의 시간
            if i == 1:
                await Company.labordecay(cursor)
            if i == 4:
                await Company.seq2(cursor)

        await mastertick(i, n)
        #await vtrader.tick(i, n)
        await asyncio.gather(
            *[market.tick(i, n) for market in Settings.markets.values()]
        )
        if i >= TICK_PER_DAY:
            return (0, n + 1), 1
        else:
            return (i + 1, n), 0.001

    asyncio.run(_run(),
                # debug=True,
                )


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrLogger)
    Settings.logger = logger
    run()
