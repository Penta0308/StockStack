import logging
import json
import asyncio

import aiofiles
import psycopg
from psycopg import rows
from aiohttp import web


class Settings:
    _settings = None

    @staticmethod
    def load():
        if Settings._settings is None:
            with open("config/settings.json", "r", encoding="utf-8") as f:
                Settings._settings = json.load(f)

    @staticmethod
    def get():
        if Settings._settings is None:
            Settings.load()
        return Settings._settings


app = web.Application()
routes = web.RouteTableDef()
db: psycopg.AsyncConnection


async def on_startup(_):
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stderrlogger = logging.StreamHandler()
    stderrlogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrlogger)

    global dbconn
    dbconn = await psycopg.AsyncConnection.connect(**(Settings.get()['database']), autocommit=True)
    async with dbconn.cursor() as cur:
        async with aiofiles.open("stockstackfe/stockstack_init.sql", encoding="UTF-8") as f:
            await cur.execute(await f.read(), prepare=False)

    # noinspection PyBroadException
    try:
        initdata = Settings.get()['stockstack']['init']
        async with dbconn.cursor() as cur:
            await cur.execute(
                """INSERT INTO market.companies (cid, name, worktype, listable, sellprice) VALUES (0, 'CONSUMER', 0, FALSE,
                        (SELECT ARRAY(SELECT baseprice FROM world.goods ORDER BY gid ASC))) RETURNING cid""")
            await cur.execute(
                """INSERT INTO market.companyfactories (cid, fid, factorysize) VALUES (0, 0, %s)""",
                (initdata['population'],)
            )
        from stockstack.world import Wallet
        await Wallet.putmoney(0, initdata['population'] * initdata['gnpp'])
    except:
        pass


@routes.view(r"/company")
class CompaniesView(web.View):
    async def post(self):
        data = await self.request.json()

        from stockstack.world import Company
        cid = await Company.create(dbconn.cursor, data.get('name'), data.get('worktype'))

        from stockstack.world import Wallet
        await Wallet.putmoney(cid)

        raise web.HTTPSeeOther(f'/company/{cid}')

    async def get(self):
        from stockstack.world import Company
        return web.json_response({'l': await Company.searchall(dbconn.cursor)})


@routes.view(r"/company/{cid:-?[\d]+}")
class CompanyView(web.View):
    @property
    def cid(self):
        return int(self.request.match_info["cid"])

    async def get(self):
        from stockstack.world import Company
        return web.json_response(await Company.getinfo(dbconn.cursor, self.cid))


@routes.view(r"/marketconfig/{kkey}")
class MarketConfigView(web.View):
    @property
    def kkey(self):
        return str(self.request.match_info["kkey"])

    async def put(self):
        data = await self.request.json()

        from stockstack.world import MarketConfig
        await MarketConfig.write(dbconn.cursor, self.kkey, str(data.get('value')))
        return await self.get()

    async def get(self):
        from stockstack.world import MarketConfig
        return web.json_response({"key": self.kkey, "value": await MarketConfig.read(dbconn.cursor, self.kkey)})

app.on_startup.append(on_startup)
app.add_routes(routes)

web.run_app(app, **(Settings.get()['stockstackfe']['web']))
