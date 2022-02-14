import logging

from stockstack.settings import Settings
from stockstack.world.market import Market


def run():
    Settings.logger.debug(f"Starting")
    Settings.load()

    market = Market(Settings.get()["database"])
    market.start()
    market.join()


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrLogger)
    Settings.logger = logger
    run()
