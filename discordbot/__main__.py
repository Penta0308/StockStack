import logging
import sys

import dico

from discordbot.bot import Bot
from stockstack.settings import Settings

bot = Bot(
    token=Settings.get()["discordbot"]["token"],
    prefix="",
    default_allowed_mentions=dico.AllowedMentions(),
    intents=dico.Intents.no_privileged(),
    monoshard=True,
)

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrLogger)
    Settings.logger = logger
    bot.run()
