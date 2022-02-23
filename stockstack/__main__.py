import asyncio
import logging

import aiofiles
import psycopg

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
        while True:
            i = int(await WorldConfig.read(cursor, "market_tick_n"))
            i, d = await tick(i)
            await WorldConfig.write(cursor, "market_tick_n", str(i), update=True)
            await asyncio.sleep(d)

    async def tick(i) -> (int, float):
        if await WorldConfig.read(cursor, "market_tick_active") == "False":
            return i, 1

        async def mastertick(i):
            if i == 2:
                await Company.seq1(cursor)  # 회사의 시간
            if i == 1:
                await Company.labordecay(cursor)
            if i == 4:
                await Company.seq2(cursor)
            # if i == 30:
            #    await Company.labordecay(cursor)
        await mastertick(i)
        await asyncio.gather(
            *[market.tick(i) for market in Settings.markets.values()]
        )
        if i >= 30:
            return 0, 1
        else:
            return i + 1, 0.001

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
