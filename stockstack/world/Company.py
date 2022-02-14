from typing import Callable, TypedDict, List

import numpy as np
import psycopg
from psycopg import rows

from stockstack.settings import Settings
from stockstack.world import Wallet


class DictCompanyFactory(TypedDict):
    cid: int
    fid: int
    factorysize: int
    efficiency: float


class DictFactory(TypedDict):
    fid: int
    consume: List[int]
    produce: List[int]
    unitprice: int


class DictGood(TypedDict):
    gid: int
    name: str
    baseprice: int


async def _companyfactories(curfactory: Callable[[], psycopg.AsyncCursor], cid: int) -> List[DictCompanyFactory]:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, fid, factorysize, efficiency FROM market.companyfactories WHERE cid = %s""",
            (cid,))
        return await cur.fetchall()


async def _factory(curfactory: Callable[[], psycopg.AsyncCursor], fid: int) -> DictFactory:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT consume, produce FROM world.factories WHERE fid = %s""",
            (fid,))
        return await cur.fetchone()


async def _good(curfactory: Callable[[], psycopg.AsyncCursor], gid: int) -> DictGood:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT name, baseprice FROM world.goods WHERE gid = %s""",
            (gid,))
        return await cur.fetchone()


async def _goodcount(curfactory: Callable[[], psycopg.AsyncCursor]) -> int:
    async with curfactory() as cur:
        await cur.execute("""SELECT COUNT(gid) FROM world.goods""")
        return (await cur.fetchone())[0]


async def _companysellprice(curfactory: Callable[[], psycopg.AsyncCursor], cid: int, gid: int) -> int:
    async with curfactory() as cur:
        await cur.execute(
            """SELECT sellprice[%s] FROM market.companies WHERE cid = %s""",
            (gid + 1, cid))
        return (await cur.fetchone())[0]


async def tick(curfactory: Callable[[], psycopg.AsyncCursor]):
    Settings.logger.info("Company tick")
    async with curfactory() as cur:
        await cur.execute("""UPDATE market.companies SET outventory = ARRAY(
            SELECT a.elem * (SELECT 1 - decayrate FROM world.goods WHERE gid = a.nr - 1) FROM
                                    unnest(outventory) WITH ORDINALITY AS a(elem, nr))""")

    await _tick_consumer(curfactory)
    for cid in await searchall(curfactory):
        await _tick(curfactory, cid)


async def _tick_consumer(curfactory: Callable[[], psycopg.AsyncCursor]):
    cf = (await _companyfactories(curfactory, 0))[0]
    rq = np.ones(await _goodcount(curfactory), np.int) * cf['factorysize'] * 2

    for gid, amount in enumerate(rq):
        if amount > 0:
            async with curfactory() as cur:
                await cur.execute(
                    """SELECT cid FROM market.companies WHERE outventory[%s] > 0 ORDER BY sellprice[%s] ASC""",
                    (gid + 1, gid + 1)
                )
                while amount > 0:
                    cidt = await cur.fetchone()
                    if cidt is None: break
                    cidt = cidt[0]

                    amct = await getoutventory(curfactory, cidt, gid)
                    amct = min(amount, amct)
                    uprice = await _companysellprice(curfactory, cidt, gid)
                    tcost = uprice * amct
                    Settings.logger.info(
                        f'Company {0} Getting [Good {gid}]x{amct} from {cidt} by paying {uprice}/Unit')
                    await deltaoutventory(curfactory, cidt, gid, -amct)
                    await deltainventory(curfactory, 0, gid, +amct)
                    await Wallet.deltamoney(cidt, +tcost)
                    await Wallet.deltamoney(0, -tcost)
                    amount -= amct

    tprod = cf['factorysize']
    f = await _factory(curfactory, cf['fid'])

    for gid, uamount in enumerate(f['produce']):
        if uamount == 0: continue
        moutv = await getoutventory(curfactory, 0, gid) / float(uamount * cf['factorysize'])
        if moutv >= 2:
            tprod *= max(0, 3 - moutv)

    for gid, uamount in enumerate(f['consume']):
        if uamount == 0: continue
        tprod = min(tprod, await getinventory(curfactory, 0, gid) / float(uamount))

    tprod = int(tprod)
    for gid, uamount in enumerate(f['consume']):
        if uamount * tprod == 0: continue
        await deltainventory(curfactory, 0, gid, -1 * uamount * tprod)
    for gid, uamount in enumerate(f['produce']):
        if uamount * tprod == 0: continue
        await deltaoutventory(curfactory, 0, gid, +1 * uamount * tprod)
        Settings.logger.info(f'Company {0} Producing [Good {gid}]x{tprod}')

async def _tick(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    # if cid == 0:
    #    await deltamoney(0, await getmoney(0) * float(
    #        await MarketConfig.read(curfactory, 'market_interestrate')) / 365)

    # c = await getinfo(curfactory, cid)

    # f = await _factory(curfactory, c['worktype'])

    rq = np.zeros(await _goodcount(curfactory), np.int)

    for cf in await _companyfactories(curfactory, cid):
        pu = cf['factorysize']
        f = await _factory(curfactory, cf['fid'])
        rq += np.array(f['consume'], np.int) * pu

    rq -= np.array(await getinventories(curfactory, cid))

    for gid, amount in enumerate(rq):
        if amount > 0:
            async with curfactory() as cur:
                await cur.execute(
                    """SELECT cid FROM market.companies WHERE outventory[%s] > 0 ORDER BY sellprice[%s] ASC""",
                    (gid + 1, gid + 1)
                )
                while amount > 0:
                    cidt = await cur.fetchone()
                    if cidt is None: break
                    cidt = cidt[0]

                    amct = await getoutventory(curfactory, cidt, gid)
                    amct = min(amount, amct)
                    uprice = await _companysellprice(curfactory, cidt, gid)
                    tcost = uprice * amct
                    Settings.logger.info(
                        f'Company {cid} Getting [Good {gid}]x{amct} from {cidt} by paying {uprice}/Unit')
                    await deltaoutventory(curfactory, cidt, gid, -amct)
                    await deltainventory(curfactory, cid, gid, +amct)
                    await Wallet.deltamoney(cidt, +tcost)
                    await Wallet.deltamoney(cid, -tcost)
                    amount -= amct

    for cf in await _companyfactories(curfactory, cid):
        tprod = cf['factorysize']
        f = await _factory(curfactory, cf['fid'])

        for gid, uamount in enumerate(f['produce']):
            if uamount == 0: continue
            moutv = await getoutventory(curfactory, cid, gid) / float(uamount * cf['factorysize'])
            if moutv >= 2:
                tprod *= max(0, 3 - moutv)

        for gid, uamount in enumerate(f['consume']):
            if uamount == 0: continue
            tprod = min(tprod, await getinventory(curfactory, cid, gid) / float(uamount))

        tprod = int(tprod)
        for gid, uamount in enumerate(f['consume']):
            if uamount * tprod == 0: continue
            await deltainventory(curfactory, cid, gid, -1 * uamount * tprod)
        for gid, uamount in enumerate(f['produce']):
            if uamount * tprod == 0: continue
            await deltaoutventory(curfactory, cid, gid, +1 * uamount * tprod)
            Settings.logger.info(f'Company {cid} Producing [Good {gid}]x{tprod}')

    if await Wallet.getmoney(cid) <= 50000000:
        pass  # TODO: 유상증자
    else:
        pass  # TODO: 성장


async def create(
        curfactory: Callable[[], psycopg.AsyncCursor],
        name: str | None,
        worktype: int | None,
        listable: bool = False
):
    async with curfactory() as cur:
        await cur.execute(
            """INSERT INTO market.companies (name, worktype, listable, sellprice) VALUES (%s, %s, %s,
                    (SELECT ARRAY(SELECT baseprice FROM world.goods ORDER BY gid ASC))) RETURNING cid""",
            (name, worktype, listable),
        )
        cid = (await cur.fetchone())[0]

    return cid


async def searchall(
        curfactory: Callable[[], psycopg.AsyncCursor], ):
    async with curfactory() as cur:
        await cur.execute("""SELECT ARRAY(SELECT cid FROM market.companies WHERE cid != 0)""")
        return (await cur.fetchone())[0]


async def getinfo(
        curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, name, worktype, inventory, outventory FROM market.companies WHERE cid = %s""",
            (cid,))
        return await cur.fetchone()


async def deltainventory(curfactory, cid: int, what: int, amount: int):
    async with curfactory() as cur:
        await cur.execute("""UPDATE market.companies SET inventory[%s] = inventory[%s] + %s WHERE cid = %s""",
                          (what + 1, what + 1, amount, cid))


async def getinventories(curfactory, cid: int):
    async with curfactory() as cur:
        await cur.execute("""SELECT inventory FROM market.companies WHERE cid = %s""",
                          (cid,))
        return (await cur.fetchone())[0]


async def getinventory(curfactory, cid: int, what: int):
    async with curfactory() as cur:
        await cur.execute("""SELECT inventory[%s] FROM market.companies WHERE cid = %s""",
                          (what + 1, cid))
        return (await cur.fetchone())[0]


async def deltaoutventory(curfactory, cid: int, what: int, amount: int):
    async with curfactory() as cur:
        await cur.execute("""UPDATE market.companies SET outventory[%s] = outventory[%s] + %s WHERE cid = %s""",
                          (what + 1, what + 1, amount, cid))


async def getoutventories(curfactory, cid: int):
    async with curfactory() as cur:
        await cur.execute("""SELECT outventory FROM market.companies WHERE cid = %s""",
                          (cid,))
        return (await cur.fetchone())[0]


async def getoutventory(curfactory, cid: int, what: int):
    async with curfactory() as cur:
        await cur.execute("""SELECT outventory[%s] FROM market.companies WHERE cid = %s""",
                          (what + 1, cid))
        return (await cur.fetchone())[0]
