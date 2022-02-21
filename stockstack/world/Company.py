import collections
import functools
import json
import math
from typing import Callable, TypedDict, List, Dict, Any

import numpy as np
import psycopg
from psycopg import rows

from stockstack.settings import Settings
from stockstack.world import Wallet, Order, WorldConfig, Stock


class DictCompanyFactory(TypedDict):
    cid: int
    fid: int
    factorysize: int
    efficiency: float


class DictFactory(TypedDict):
    fid: int
    consume: Dict[str, int | Any]
    produce: Dict[str, int]
    unitprice: int


class DictGood(TypedDict):
    gid: int
    name: str
    baseprice: int


async def _companyfactories(
        curfactory: Callable[[], psycopg.AsyncCursor], cid: int
) -> List[DictCompanyFactory]:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, fid, factorysize, efficiency FROM world.companyfactories WHERE cid = %s""",
            (cid,),
        )
        return await cur.fetchall()


async def _factory(
        curfactory: Callable[[], psycopg.AsyncCursor], fid: int
) -> DictFactory:
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT fid, consume, produce, unitprice FROM world.factories WHERE fid = %s""",
            (fid,),
        )
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


async def labordecay(curfactory: Callable[[], psycopg.AsyncCursor]):
    Settings.logger.info("Labor decay")
    async with curfactory() as cur:
        await cur.execute("""UPDATE mspot.stockowns SET amount = 0 WHERE ticker = 'labor' AND cid = 0""")  # Decay Code


async def seq1(curfactory: Callable[[], psycopg.AsyncCursor]):
    Settings.logger.info("Company tick seq1")
    await _order_consumer(curfactory)
    for cid in (cid[0] for cid in await searchall(curfactory)):
        await _order(curfactory, cid)


async def seq2(curfactory: Callable[[], psycopg.AsyncCursor]):
    Settings.logger.info("Company tick seq2")
    await _produce_consumer(curfactory)
    for cid in (cid[0] for cid in await searchall(curfactory)):
        await _produce(curfactory, cid)


async def _order_consumer(curfactory: Callable[[], psycopg.AsyncCursor]):
    rq = collections.Counter()

    cf = (await _companyfactories(curfactory, 0))[0]
    pu = cf["factorysize"]
    f = await _factory(curfactory, cf["fid"])
    for gid, d in f["consume"].items():
        Q = math.floor(
            float(max(await Wallet.getmoney(0) - d["fromper"] * cf["factorysize"], 0)) / await Stock.getlastp(
                Settings.markets["spot"].dbconn.cursor,
                gid) / d["amount"])
        if gid in rq.keys():
            rq[gid] += Q
        else:
            rq[gid] = Q

    rq -= collections.Counter(dict(await getresources(0)))

    for gid, amount in rq.items():
        Settings.logger.info(f"Consumer Wants [{gid}]x{amount}")
        await orderbuy_resource(0, gid, amount, None)  # TODO: Price Negotiation


async def _produce_consumer(curfactory: Callable[[], psycopg.AsyncCursor]):
    cf = (await _companyfactories(curfactory, 0))[0]

    tprod = cf["factorysize"]
    f = await _factory(curfactory, cf["fid"])

    tprod = int(tprod)
    tprice = 0.0
    for gid, uamount in f["consume"].items():
        amount = await getresource(0, gid)
        if tprod * amount <= 0: continue
        tprice += await getresourceunitprice(0, gid) * amount
        await consumeresource(0, gid, amount)
        Settings.logger.info(f"Consumer Consuming [{gid}]x{amount}")

    for gid, uamount in f["produce"].items():
        a = uamount * tprod
        if a <= 0: continue
        await produceresource(0, gid, a, max(math.ceil(tprice / a),
                                             (await Stock.getinfo(Settings.markets["spot"].dbconn.cursor, gid))[
                                                 'parvalue']))
        Settings.logger.info(f"Consumer Producing [{gid}]x{a}")
    for gid, uamount in f["produce"].items():
        await ordersell_resource(0, gid, await getresource(0, gid), math.ceil(await getresourceunitprice(0, gid)))


async def _order(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    rq = collections.Counter()

    for cf in await _companyfactories(curfactory, cid):
        pu = cf["factorysize"]
        f = await _factory(curfactory, cf["fid"])
        for gid, amount in f["consume"].items():
            if gid in rq.keys():
                rq[gid] += amount * pu
            else:
                rq[gid] = amount * pu

    h = dict(await getresources(cid))

    for gid, amount in (rq - collections.Counter(h)).items():
        await orderbuy_resource(cid, gid, amount, None)  # TODO: Price Negotiation


async def _produce(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    for cf in await _companyfactories(curfactory, cid):
        tprod = cf["factorysize"]
        f = await _factory(curfactory, cf["fid"])

        board = await getboard(curfactory, cid)
        pricedelta = board.get("sellpricedelta")
        if pricedelta is None:
            pricedelta = {}

        for gid, uamount in f["produce"].items():
            moutv = await getresource(cid, gid) / float(uamount * cf["factorysize"])
            prd = pricedelta.get(gid)
            if prd is None:
                prd = 0.0

            if moutv > 1.0:  # 남음
                prd = max(0.0, prd - 0.01)
            elif moutv < 0.1:
                prd = max(0.0, prd + 0.01)
            pricedelta[gid] = prd

            tprod = min(max(0, tprod * min(1, 2 - moutv)), tprod)

        for gid, uamount in f["consume"].items():
            tprod = min(tprod, await getresource(cid, gid) / float(uamount))

        tprod = int(tprod)
        ubprice = 0.0
        for gid, uamount in f["consume"].items():
            if uamount * tprod <= 0: continue
            ubprice += await getresourceunitprice(cid, gid) * uamount
            await consumeresource(cid, gid, uamount * tprod)
        for gid, uamount in f["produce"].items():
            if uamount * tprod <= 0: continue
            a = await produceresource(cid, gid, uamount * tprod, math.ceil(ubprice / uamount))
            Settings.logger.info(f"Company {cid} Producing [{gid}]x{a}")
        for gid, uamount in f["produce"].items():
            await ordersell_resource(cid, gid, await getresource(cid, gid),
                                     math.ceil(await getresourceunitprice(cid, gid) * (1.0 + pricedelta[gid])))

        await updboard(curfactory, cid, {"sellpricedelta": pricedelta})

    if await Wallet.getmoney(cid) <= 50000000:
        pass  # TODO: 유상증자
    else:
        pass  # TODO: 성장


async def create(
        curfactory: Callable[[], psycopg.AsyncCursor],
        name: str | None,
        worktype: int | None,
        listable: bool = False,
):
    async with curfactory() as cur:
        await cur.execute(
            """INSERT INTO world.companies (name, worktype, listable) VALUES (%s, %s, %s) RETURNING cid""",
            (name, worktype, listable),
        )
        cid = (await cur.fetchone())[0]

    return cid


async def searchall(
        curfactory: Callable[[], psycopg.AsyncCursor],
):
    async with curfactory() as cur:
        await cur.execute("""SELECT cid FROM world.companies WHERE cid != 0""")
        return await cur.fetchall()


async def getinfo(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    async with curfactory() as cur:
        cur.row_factory = rows.dict_row
        await cur.execute(
            """SELECT cid, name, worktype FROM world.companies WHERE cid = %s""", (cid,)
        )
        return await cur.fetchone()


async def getresources(cid: int):
    return await Settings.markets["spot"].stockowns_get_company(cid)


async def getresource(cid: int, rid: str):
    return await Settings.markets["spot"].stockown_get_company(cid, rid)


async def getresourceunitprice(cid: int, rid: str):
    return await Settings.markets["spot"].stockown_priceperunit(cid, rid)


async def produceresource(cid: int, rid: str, amount: int, regprice: int):
    return await Settings.markets["spot"].stockown_create(cid, rid, amount, regprice)


async def consumeresource(cid: int, rid: str, amount: int):
    return await Settings.markets["spot"].stockown_delete(cid, rid, amount)


async def orderbuy_resource(cid: int, rid: str, amount: int, price: int | None):
    await Order.orderbuy_put(Settings.markets["spot"], cid, rid, amount, price)


async def ordersell_resource(cid: int, rid: str, amount: int, price: int | None):
    await Order.ordersell_put(Settings.markets["spot"], cid, rid, amount, price)


async def getboard(curfactory: Callable[[], psycopg.AsyncCursor], cid: int):
    async with curfactory() as cur:
        await cur.execute(
            """SELECT board FROM world.companies WHERE cid = %s""", (cid,)
        )
        return (await cur.fetchone())[0]


async def updboard(curfactory: Callable[[], psycopg.AsyncCursor], cid: int, value: dict):
    async with curfactory() as cur:
        await cur.execute(
            """UPDATE world.companies SET board = board::JSONB || %s::JSONB WHERE cid = %s""", (json.dumps(value), cid,)
        )


async def setboard(curfactory: Callable[[], psycopg.AsyncCursor], cid: int, value: dict):
    async with curfactory() as cur:
        await cur.execute(
            """UPDATE world.companies SET board = %s::JSONB WHERE cid = %s""", (json.dumps(value), cid,)
        )
