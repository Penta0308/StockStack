import logging
import multiprocessing
import sys

from stocksheet.network.gateway import Gateway
from stocksheet.settings import Settings

def run(name, socket):
    if Settings.logger is None:
        Settings.logger = multiprocessing.get_logger()
    Settings.load()

    Settings.logger.name = name

    gateway = Gateway(name, Settings.get()['database'], socket)

    Settings.maincontext = globals()

    gateway.run()   # blocking

if __name__ == '__main__':
    Settings.logger = logging.getLogger()
    Settings.logger.setLevel(logging.DEBUG)
    run(sys.argv[1], sys.argv[2])
