import json
import asyncio
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
    global db
    db = await psycopg.AsyncConnection.connect(**(Settings.get()['database']), autocommit=True)
    async with db.cursor() as cur:
        await cur.execute(
            """CREATE SCHEMA IF NOT EXISTS wallet"""
        )
        await cur.execute(
            """CREATE TABLE IF NOT EXISTS wallet.data (
            user_id BIGINT PRIMARY KEY,
            money BIGINT NOT NULL DEFAULT 0
            )"""
        )


@routes.view(r"/{user_id:-?[\d]+}")
class WalletView(web.View):
    @property
    def user_id(self):
        return int(self.request.match_info["user_id"])

    async def put(self):
        data = await self.request.json()
        bm = data.get('amount')
        async with db.cursor() as cur:
            await cur.execute(
                """INSERT INTO wallet.data VALUES (%s, %s)""",
                (self.user_id, 0 if bm is None else bm),
            )
            return await self.get()

    async def post(self):
        data = await self.request.json()
        async with db.cursor() as cur:
            await cur.execute(
                """UPDATE wallet.data SET money = money + %s WHERE user_id = %s""",
                (data["amount"], self.user_id), prepare=True
            )
            return await self.get()

    async def get(self):
        async with db.cursor() as cur:
            await cur.execute(
                """SELECT money FROM wallet.data WHERE user_id = %s""", (self.user_id,), prepare=True
            )
            r = await cur.fetchone()
            return web.json_response({'amount': None if r is None else r[0]})


app.on_startup.append(on_startup)
app.add_routes(routes)

web.run_app(app, **(Settings.get()['stockwallet']['web']))
