from typing import Callable

import aiohttp as aiohttp
import psycopg
from psycopg import rows

from stockstack.settings import Settings

from stockstack.world.marketconfig import MarketConfig


class Company:
    @staticmethod
    async def _factory(curfactory: Callable[[], psycopg.AsyncCursor], worktype: int):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute(
                """SELECT consume, produce FROM world.factories WHERE worktype = %s""",
                (worktype,))
            return await cur.fetchone()

    @staticmethod
    async def _goods(curfactory: Callable[[], psycopg.AsyncCursor], gid: int):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute(
                """SELECT name, baseprice FROM world.goods WHERE gid = %s""",
                (gid,))
            return await cur.fetchone()

    @staticmethod
    async def _getsellprice(curfactory: Callable[[], psycopg.AsyncCursor], cid: int, gid: int) -> int:
        async with curfactory() as cur:
            await cur.execute(
                """SELECT sellprice[%s] FROM market.companies WHERE cid = %s""",
                (gid + 1, cid))
            return (await cur.fetchone())[0]

    @staticmethod
    async def tick(curfactory: Callable[[], psycopg.AsyncCursor]):
        Settings.logger.info("Company tick")
        async with curfactory() as cur:
            await cur.execute("""UPDATE market.companies SET outventory = ARRAY(
                SELECT a.elem * (SELECT 1 - decayrate FROM world.goods WHERE gid = a.nr - 1) FROM
                                        unnest(outventory) WITH ORDINALITY AS a(elem, nr))""")

        for cid in await Company.searchall(curfactory):
            await Company._tick(curfactory, cid)

    @staticmethod
    async def _tick(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
        if cid == 0:
            await Company.deltamoney(0, await Company.getmoney(0) * float(
                await MarketConfig.read(curfactory, 'market_interestrate')) / 365)

        c = await Company.getinfo(curfactory, cid)

        f = await Company._factory(curfactory, c['worktype'])

        for n, a in enumerate(c['inventory']):
            rq = c['factorysize'] * (f['consume'][n]) - a
            if rq > 0:
                async with curfactory() as cur:
                    await cur.execute(
                        """SELECT cid FROM market.companies WHERE outventory[%s] > 0 ORDER BY sellprice[%s] ASC""",
                        (n + 1, n + 1)
                    )
                    while rq > 0:
                        cti = await cur.fetchone()
                        if cti is None: break
                        cti = cti[0]

                        ct = max(0, await Company.getoutventory(curfactory, cti, n))
                        ct = min(rq, ct)
                        up = await Company._getsellprice(curfactory, cti, n)
                        p = up * ct
                        Settings.logger.info(f'Company {cid} Getting [Goods {n}]x{ct} from {cti} by paying {up}/Unit')
                        await Company.deltaoutventory(curfactory, cti, n, -ct)
                        await Company.deltainventory(curfactory, cid, n, +ct)
                        await Company.deltamoney(cti, +p)
                        await Company.deltamoney(cid, -p)
                        rq -= ct

        c = await Company.getinfo(curfactory, cid)
        pu = c['factorysize']
        for n, a in enumerate(c['inventory']):
            q = f['consume'][n]
            if q > 0:
                _pu = a / q
                pu = min(_pu, pu)
        pu = max(pu, 0)
        for n, a in enumerate(c['outventory']):
            if a > c['factorysize'] * f['produce'][n] * 4.0 and f['produce'][n] != 0:
                pu = 0

        pu = int(pu)
        for n, a in enumerate(f['consume']):
            if a * pu == 0: continue
            await Company.deltainventory(curfactory, cid, n, -1 * a * pu)
        for n, a in enumerate(f['produce']):
            if a * pu == 0: continue
            await Company.deltaoutventory(curfactory, cid, n, +1 * a * pu)
        Settings.logger.info(f'Company {cid} Producing {pu}')

        if await Company.getmoney(cid) <= 50000000:
            pass  # TODO: 유상증자
        else:
            pass  # TODO: 성장

    @staticmethod
    async def create(
            curfactory: Callable[[], psycopg.AsyncCursor],
            name: str | None,
            worktype: int | None,
            factorysize: int = 0,
            listable: bool = False
    ):
        async with curfactory() as cur:
            await cur.execute(
                """INSERT INTO market.companies (name, worktype, factorysize, listable, sellprice) VALUES (%s, %s, %s, %s, 
                        (SELECT ARRAY(SELECT baseprice FROM world.goods ORDER BY gid ASC))) RETURNING cid""",
                (name, worktype, factorysize, listable),
            )
            cid = (await cur.fetchone())[0]

        async with aiohttp.ClientSession() as session:
            await session.put(f'http://wallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}',
                              data=f'{{"user_id": {cid}}}'.encode(encoding='UTF-8'))
        return cid

    @staticmethod
    async def searchall(
            curfactory: Callable[[], psycopg.AsyncCursor], ):
        async with curfactory() as cur:
            await cur.execute("""SELECT ARRAY(SELECT cid FROM market.companies)""")
            return (await cur.fetchone())[0]

    @staticmethod
    async def getinfo(
            curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute(
                """SELECT cid, name, worktype, factorysize, inventory, outventory FROM market.companies WHERE cid = %s""",
                (cid,))
            return await cur.fetchone()

    @staticmethod
    async def deltamoney(cid: int, amount: int):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://wallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}',
                                    data=f'{{"amount": {amount} }}'.encode(encoding='UTF-8')) as resp:
                j = await resp.json()
                return j['amount']

    @staticmethod
    async def getmoney(cid: int):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f'http://wallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}') as resp:
                j = await resp.json()
                return j['amount']

    @staticmethod
    async def deltainventory(curfactory, cid: int, what: int, amount: int):
        async with curfactory() as cur:
            await cur.execute("""UPDATE market.companies SET inventory[%s] = inventory[%s] + %s WHERE cid = %s""",
                              (what + 1, what + 1, amount, cid))

    @staticmethod
    async def getinventory(curfactory, cid: int, what: int):
        async with curfactory() as cur:
            await cur.execute("""SELECT inventory[%s] FROM market.companies WHERE cid = %s""",
                              (what + 1, cid))
            return (await cur.fetchone())[0]

    @staticmethod
    async def deltaoutventory(curfactory, cid: int, what: int, amount: int):
        async with curfactory() as cur:
            await cur.execute("""UPDATE market.companies SET outventory[%s] = outventory[%s] + %s WHERE cid = %s""",
                              (what + 1, what + 1, amount, cid))

    @staticmethod
    async def getoutventory(curfactory, cid: int, what: int):
        async with curfactory() as cur:
            await cur.execute("""SELECT outventory[%s] FROM market.companies WHERE cid = %s""",
                              (what + 1, cid))
            return (await cur.fetchone())[0]
