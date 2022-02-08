from typing import TYPE_CHECKING, List, Callable

import psycopg
from psycopg import rows

from stockstack.settings import Settings

FACTORY_DESC = [
    {"consume": [1, 0], "produce": [0, 0], "cost": -2000},  # 소비자
    {"consume": [0, 1], "produce": [1, 0], "cost": 400},  # 식품기업
    {"consume": [0, 0], "produce": [0, 1], "cost": 700}  # 농장
]

GOODS_DESC = [
    {"priceperunit": 2000},  # 가공식품
    {"priceperunit": 1000}  # 농산물
]


class Company:
    @staticmethod
    async def tick(curfactory: Callable[[], psycopg.AsyncCursor]):
        Settings.logger.debug("Company tick")
        for cid in await Company.searchall(curfactory):
            await Company._tick(curfactory, cid)

    @staticmethod
    async def _tick(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
        c = await Company.getinfo(curfactory, cid)

        f = FACTORY_DESC[c['worktype']]

        for n, a in enumerate(c['inventory']):
            rq = int(c['factorysize'] * f['consume'][n] * 3.0 - a)
            if rq > 0:
                async with curfactory() as cur:
                    await cur.execute(
                        """SELECT cid FROM companies WHERE inventory[%s] >= 1 ORDER BY inventory[%s] DESC""",
                        (n + 1, n + 1)
                    )
                    while rq > 0:
                        cti = await cur.fetchone()
                        if cti is None: break
                        cti = cti[0]

                        ct = await Company.getinventory(curfactory, cti, n)
                        ct = min(rq, ct)
                        p = ct * GOODS_DESC[n]['priceperunit']
                        Settings.logger.debug(f'Company {cid} Getting {n} {ct} from {cti} with {p}')
                        await Company.deltainventory(curfactory, cti, n, -ct)
                        await Company.deltainventory(curfactory, cid, n, +ct)
                        await Company.deltamoney(curfactory, cti, +p)
                        await Company.deltamoney(curfactory, cid, -p)
                        rq -= ct

        c = await Company.getinfo(curfactory, cid)
        pu = c['factorysize']
        for n, a in enumerate(c['inventory']):
            q = f['consume'][n]
            if q > 0:
                _pu = a / q
                pu = min(_pu, pu)
            if a > c['factorysize'] * f['produce'][n] * 4.0 and f['produce'][n] != 0:
                pu = 0

        await Company.deltamoney(curfactory, cid, -1 * pu * f['cost'])
        for n, a in enumerate(f['consume']):
            if a * pu == 0: continue
            await Company.deltainventory(curfactory, cid, n, -1 * a * pu)
        for n, a in enumerate(f['produce']):
            if a * pu == 0: continue
            await Company.deltainventory(curfactory, cid, n, +1 * a * pu)
        Settings.logger.debug(f'Company {cid} Producing {pu}')

        if c['cash'] <= 50000000:
            pass  # TODO: 유상증자
        else:
            pass  # TODO: 성장

    @staticmethod
    async def create(
            curfactory: Callable[[], psycopg.AsyncCursor],
            name: str,
            worktype: List[float],
    ):
        async with curfactory() as cur:
            await cur.execute(
                """INSERT INTO companies (name, worktype) VALUES (%s, %s) RETURNING cid""",
                (name, worktype),
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def searchall(
            curfactory: Callable[[], psycopg.AsyncCursor], ):
        async with curfactory() as cur:
            await cur.execute("""SELECT ARRAY(SELECT cid FROM companies)""")
            return (await cur.fetchone())[0]

    @staticmethod
    async def getinfo(
            curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
        async with curfactory() as cur:
            cur.row_factory = rows.dict_row
            await cur.execute(
                """SELECT cid, name, cash, worktype, factorysize, inventory FROM companies WHERE cid = %s""",
                (cid,))
            return await cur.fetchone()

    @staticmethod
    async def deltamoney(curfactory, cid: int, amount: int):
        async with curfactory() as cur:
            await cur.execute("""UPDATE companies SET cash = cash + %s WHERE cid = %s""",
                              (amount, cid))

    @staticmethod
    async def deltainventory(curfactory, cid: int, what: int, amount: int):
        async with curfactory() as cur:
            await cur.execute("""UPDATE companies SET inventory[%s] = inventory[%s] + %s WHERE cid = %s""",
                              (what + 1, what + 1, amount, cid))

    @staticmethod
    async def getinventory(curfactory, cid: int, what: int):
        async with curfactory() as cur:
            await cur.execute("""SELECT inventory[%s] FROM companies WHERE cid = %s""",
                              (what + 1, cid))
            return (await cur.fetchone())[0]
