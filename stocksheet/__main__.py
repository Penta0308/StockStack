import logging
import multiprocessing
import signal
import sys
import jinja2

from stocksheet.network.auth import Auth
from stocksheet.network.gateway import Gateway
from stocksheet.settings import Settings

"""def kotc_price_stepsize(price):
    if price < 1000:  # 1원 단위
        step = 1
    elif price < 5000:  # 5원 단위
        step = 5
    elif price < 10000:  # 10원 단위
        step = 10
    elif price < 50000:  # 50원 단위
        step = 50
    elif price < 100000:  # 100원 단위
        step = 100
    elif price < 500000:  # 500원 단위
        step = 500
    else:  # 1000원 단위
        step = 1000
    return step


kotc_variancerate = 0.3

kotc = Market(kotc_price_stepsize, kotc_variancerate)

kotc.open()

kotc.close()"""

def run(name, socket):
    if Settings.logger is None:
        Settings.logger = multiprocessing.get_logger()
    Settings.load()

    Settings.templateenv = jinja2.Environment(loader=jinja2.PackageLoader("stocksheet"), autoescape=jinja2.select_autoescape())

    gateway = Gateway(name, Settings.get()['database'], socket)

    Settings.maincontext = globals()

    gateway.run()   # blocking

if __name__ == '__main__':
    Settings.logger = logging.getLogger()
    Settings.logger.setLevel(logging.DEBUG)
    run(sys.argv[1], sys.argv[2])
