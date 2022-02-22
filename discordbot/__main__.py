import asyncio
import logging
import sys
from typing import Dict

import psycopg
from psycopg_pool import AsyncConnectionPool

import dico

from discordbot.bot import Bot
from stockstack.settings import Settings

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrLogger)
    Settings.logger = logger
    dbinfo: Dict[str, str] = Settings.get()["database"]

    with psycopg.connect(**dbinfo, autocommit=True) as dbconn:
        with open("discordbot/discordbot_init.sql", encoding="UTF-8") as f:
            dbconn.execute(f.read(), prepare=False)

    dbinfo["options"] = f"-c search_path={'discordbot'}"

    bot = Bot(
        token=Settings.get()["discordbot"]["token"],
        prefix="",
        default_allowed_mentions=dico.AllowedMentions(),
        intents=dico.Intents.no_privileged(),
        monoshard=True,
        dbconnpool=AsyncConnectionPool(
            conninfo=' '.join((str(k) + "=" + str(v).replace(r' ', r'\ ')) for k, v in dbinfo.items()), open=False,
            kwargs={'autocommit': True})
    )

    bot.load_modules()
    bot.run()
