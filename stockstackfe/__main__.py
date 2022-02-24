import logging

import psycopg
from aiohttp import web

from stockstack.settings import Settings
from stockstack.world.market import MarketSQLDesc

app = web.Application()
routes = web.RouteTableDef()
dbconn: psycopg.AsyncConnection


async def on_startup(app: web.Application):
    Settings.logger = logging.getLogger()
    Settings.logger.setLevel(logging.INFO)
    stderrlogger = logging.StreamHandler()
    stderrlogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    Settings.logger.addHandler(stderrlogger)

    for d in Settings.get()["stockstack"]["markets"]:
        name = d["name"]
        Settings.markets[name] = MarketSQLDesc(
            name,
            Settings.get()["database"],
            initfile=d["initfile"]
        )
        await Settings.markets[name].init()

    global dbconn
    dbconn = await psycopg.AsyncConnection.connect(
        **(Settings.get()["database"]), autocommit=True
    )


@routes.view(r"/company")
class CompaniesView(web.View):
    async def post(self):
        data = await self.request.json()

        from stockstack.world import Company

        cid = await Company.create(
            dbconn.cursor, data.get("name"), data.get("worktype")
        )

        from stockstack.world import Wallet

        await Wallet.putmoney(cid)

        raise web.HTTPCreated(headers={"Location": f"/company{cid}"})

    # noinspection PyMethodMayBeStatic
    async def get(self):
        from stockstack.world import Company

        return web.json_response(await Company.searchall(dbconn.cursor))


@routes.view(r"/company/{cid:-?[\d]+}")
class CompanyView(web.View):
    @property
    def cid(self):
        return int(self.request.match_info["cid"])

    async def get(self):
        from stockstack.world import Company

        i = await Company.getinfo(dbconn.cursor, self.cid)
        if i is None: raise web.HTTPNotFound()
        return web.json_response(i)


@routes.view(r"/company/{cid:-?[\d]+}/stockown")
class CompanyStockOwnView(web.View):
    @property
    def cid(self):
        return int(self.request.match_info["cid"])

    async def get(self):
        i = await Settings.markets["stock"].stockowns_get_company(self.cid)
        return web.json_response(i)


@routes.view(r"/order")
class OrdersView(web.View):
    async def post(self):
        data = await self.request.json()

        from stockstack.world import Order

        cid = int(data["cid"])
        amount = int(data["amount"])
        ticker = str(data["ticker"])
        price = data["price"]

        if amount > 0:
            ots = await Order.orderbuy_put(Settings.markets["stock"], cid, ticker, amount, price)
        elif amount < 0:
            ots = await Order.ordersell_put(Settings.markets["stock"], cid, ticker, amount, price)
        else:
            raise web.HTTPBadRequest()

        raise web.HTTPCreated(headers={"Location": f"/order/{ots}"})


@routes.view(r"/order/{ots:-?[\d]+}")
class OrderView(web.View):
    @property
    def ots(self):
        return int(self.request.match_info["ots"])

    async def get(self):
        from stockstack.world import Order

        i = await Order.order_get(Settings.markets["stock"], self.ots)
        if i is None: raise web.HTTPNotFound()
        return web.json_response(i)


@routes.view(r"/stock")
class StocksView(web.View):
    async def get(self):
        from stockstack.world import Stock
        return web.json_response(await Stock.searchall(Settings.markets["stock"].dbconn.cursor))


@routes.view(r"/stock/{ticker:[\w]+}")
class StockView(web.View):
    @property
    def ticker(self):
        return str(self.request.match_info["ticker"])

    async def get(self):
        from stockstack.world import Stock

        i = await Stock.getinfo(Settings.markets["stock"].dbconn.cursor, self.ticker)
        if i is None: raise web.HTTPNotFound()
        return web.json_response(i)


@routes.view(r"/worldconfig/{kkey}")
class MarketConfigView(web.View):
    @property
    def kkey(self):
        return str(self.request.match_info["kkey"])

    async def put(self):
        data = await self.request.json()

        from stockstack.world import WorldConfig

        await WorldConfig.write(dbconn.cursor, self.kkey, str(data.get("value")))
        return await self.get()

    async def get(self):
        from stockstack.world import WorldConfig

        return web.json_response(
            {
                "key": self.kkey,
                "value": await WorldConfig.read(dbconn.cursor, self.kkey),
            }
        )


app.on_startup.append(on_startup)
app.add_routes(routes)

web.run_app(app, **(Settings.get()["stockstackfe"]["web"]))
