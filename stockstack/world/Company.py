import collections
import functools
from typing import Callable, TypedDict, List, Dict

import numpy as np
import psycopg
from psycopg import rows

from stockstack.settings import Settings
from stockstack.world import Wallet, Order


class DictCompanyFactory(TypedDict):
    cid: int
    fid: int
    factorysize: int
    efficiency: float


class DictFactory(TypedDict):
    fid: int
    consume: Dict[str, int]
    produce: Dict[str, int]
    unitprice: int


class DictGood(TypedDict):
    gid: int
    name: str
    baseprice: int


async def _companyfactories(curfactory: Callable[[], psycopg.AsyncCursor], cid: int) -> List[DictCompanyFactory]:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, fid, factorysize, efficiency FROM world.companyfactories WHERE cid = %s""",
            (cid,))
        return await cur.fetchall()


async def _factory(curfactory: Callable[[], psycopg.AsyncCursor], fid: int) -> DictFactory:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT fid, consume, produce, unitprice FROM world.factories WHERE fid = %s""",
            (fid,))
        return await cur.fetchone()


'''async def _good(curfactory: Callable[[], psycopg.AsyncCursor], gid: int) -> DictGood:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT name, baseprice FROM world.goods WHERE gid = %s""",
            (gid,))
        return await cur.fetchone()


async def _goodcount(curfactory: Callable[[], psycopg.AsyncCursor]) -> int:
    async with curfactory() as cur:
        await cur.execute("""SELECT COUNT(gid) FROM world.goods""")
        return (await cur.fetchone())[0]'''

'''async def _companysellprice(curfactory: Callable[[], psycopg.AsyncCursor], cid: int, gid: int) -> int:
    async with curfactory() as cur:
        await cur.execute(
            """SELECT sellprice[%s] FROM world.companies WHERE cid = %s""",
            (gid + 1, cid))
        return (await cur.fetchone())[0]'''


async def tick(curfactory: Callable[[], psycopg.AsyncCursor]):
    Settings.logger.info("Company tick")
    '''async with curfactory() as cur:
        await cur.execute("""UPDATE world.companies SET outventory = ARRAY(
            SELECT a.elem * (SELECT 1 - decayrate FROM world.goods WHERE gid = a.nr - 1) FROM
                                    unnest(outventory) WITH ORDINALITY AS a(elem, nr))""")'''  # Decay Code

    await _tick_consumer(curfactory)
    for cid in await searchall(curfactory):
        cid = cid[0]
        await _tick(curfactory, cid)


async def _tick_consumer(curfactory: Callable[[], psycopg.AsyncCursor]):
    cf = (await _companyfactories(curfactory, 0))[0]
    rq = collections.Counter()

    for cf in await _companyfactories(curfactory, 0):
        pu = cf['factorysize']
        f = await _factory(curfactory, cf['fid'])
        for gid, amount in f['consume'].items():
            if gid in rq.keys():
                rq[gid] += amount * pu
            else:
                rq[gid] = amount * pu

    for gid, amount in (rq - collections.Counter(await getresources(0))).items():
        await orderbuy_resource(0, gid, amount, None)  # TODO: Price Negotiation

    tprod = cf['factorysize']
    f = await _factory(curfactory, cf['fid'])

    for gid, uamount in f['produce'].items():
        moutv = await getresource(0, gid) / float(uamount * cf['factorysize'])
        if moutv >= 2:
            tprod *= max(0, 3 - moutv)

    # for gid, uamount in f['consume'].items():
    #    tprod = min(tprod, await getresource(0, gid) / float(uamount))

    tprod = int(tprod)
    for gid, uamount in f['consume'].items():
        if uamount * tprod == 0: continue
        await consumeresource(0, gid, await getresource(0, gid))
    for gid, uamount in f['produce'].items():
        if uamount * tprod == 0: continue
        await produceresource(0, gid, uamount * tprod)
        Settings.logger.info(f'Company {0} Producing [Good {gid}]x{tprod}')

async def _tick(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    # if cid == 0:
    #    await deltamoney(0, await getmoney(0) * float(
    #        await MarketConfig.read(curfactory, 'market_interestrate')) / 365)

    # c = await getinfo(curfactory, cid)

    # f = await _factory(curfactory, c['worktype'])

    rq = collections.Counter()

    for cf in await _companyfactories(curfactory, cid):
        pu = cf['factorysize']
        f = await _factory(curfactory, cf['fid'])
        for gid, amount in f['consume'].items():
            if gid in rq.keys():
                rq[gid] += amount * pu
            else:
                rq[gid] = amount * pu

    for gid, amount in (rq - collections.Counter(await getresources(cid))).items():
        await orderbuy_resource(cid, gid, amount, None)  # TODO: Price Negotiation

    for cf in await _companyfactories(curfactory, cid):
        tprod = cf['factorysize']
        f = await _factory(curfactory, cf['fid'])

        for gid, uamount in f['produce'].items():
            moutv = await getresource(cid, gid) / float(uamount * cf['factorysize'])
            if moutv >= 2:
                tprod *= max(0, 3 - moutv)

        for gid, uamount in f['consume'].items():
            tprod = min(tprod, await getresource(cid, gid) / float(uamount))

        tprod = int(tprod)
        for gid, uamount in f['consume'].items():
            if uamount * tprod == 0: continue
            await consumeresource(cid, gid, uamount * tprod)
        for gid, uamount in f['produce'].items():
            if uamount * tprod == 0: continue
            await produceresource(cid, gid, uamount * tprod)
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
            """INSERT INTO world.companies (name, worktype, listable) VALUES (%s, %s, %s) RETURNING cid""",
            (name, worktype, listable),
        )
        cid = (await cur.fetchone())[0]

    return cid


async def searchall(
        curfactory: Callable[[], psycopg.AsyncCursor], ):
    async with curfactory() as cur:
        await cur.execute("""SELECT cid FROM world.companies WHERE cid != 0""")
        return await cur.fetchall()


async def getinfo(
        curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, name, worktype FROM world.companies WHERE cid = %s""",
            (cid,))
        return await cur.fetchone()


async def getresources(cid: int):
    return await Settings.markets["spot"].stockowns_get_company(cid)


async def getresource(cid: int, rid: str):
    return await Settings.markets["spot"].stockown_get_company(cid, rid)


async def produceresource(cid: int, rid: str, amount: int):
    return await Settings.markets["spot"].stockown_create(cid, rid, amount)


async def consumeresource(cid: int, rid: str, amount: int):
    return await Settings.markets["spot"].stockown_delete(cid, rid, amount)


async def orderbuy_resource(cid: int, rid: str, amount: int, price: int | None = None):
    await Order.orderbuy_put(Settings.markets["spot"], cid, rid, amount, price)


async def ordersell_resource(cid: int, rid: str, amount: int, price: int | None = None):
    await Order.ordersell_put(Settings.markets["spot"], cid, rid, amount, price)
