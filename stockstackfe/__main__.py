import logging
import json

import aiofiles
import psycopg
from aiohttp import web
from stockstack.world import Wallet


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


@routes.view(r"/company")
class CompaniesView(web.View):
    async def post(self):
        data = await self.request.json()

        from stockstack.world import Company
        cid = await Company.create(dbconn.cursor, data.get('name'), data.get('worktype'))

        from stockstack.world import Wallet
        await Wallet.putmoney(cid)

        raise web.HTTPSeeOther(f'/company/{cid}')

    # noinspection PyMethodMayBeStatic
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


@routes.view(r"/worldconfig/{kkey}")
class MarketConfigView(web.View):
    @property
    def kkey(self):
        return str(self.request.match_info["kkey"])

    async def put(self):
        data = await self.request.json()

        from stockstack.world import WorldConfig
        await WorldConfig.write(dbconn.cursor, self.kkey, str(data.get('value')))
        return await self.get()

    async def get(self):
        from stockstack.world import WorldConfig
        return web.json_response({"key": self.kkey, "value": await WorldConfig.read(dbconn.cursor, self.kkey)})

app.on_startup.append(on_startup)
app.add_routes(routes)

web.run_app(app, **(Settings.get()['stockstackfe']['web']))
