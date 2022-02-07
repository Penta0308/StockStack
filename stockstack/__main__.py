import logging
import multiprocessing
import sys

from stockstack.network.gateway import Gateway
from stockstack.settings import Settings
from stockstack.world.market import Market


def run():
    if Settings.logger is None:
        Settings.logger = multiprocessing.get_logger()
    Settings.load()

    market = Market(Settings.get()["database"])
    market.run()

    gateway = Gateway(market.dbinfo, Settings.get()["stockstack"]["wssocket"])

    gateway.run()  # blocking

if __name__ == "__main__":
    Settings.logger = logging.getLogger()
    Settings.logger.setLevel(logging.DEBUG)
    run()
