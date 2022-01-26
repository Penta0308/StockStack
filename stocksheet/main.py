import logging
import argparse
import sys

from stocksheet.network.auth import Auth
from stocksheet.network.gateway import Gateway
from stocksheet.world.market import Market
from stocksheet.settings import Settings
import multiprocessing

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

if __name__ == '__main__':
    name = sys.argv[1]
    port = sys.argv[2]

    Settings.load()
    dbinfo = {**(Settings.get()['database'])}

    auth = Auth(dbinfo)

    gateway = Gateway(auth, port)

    Settings.maincontext_put(globals())

    gateway.start()  # blocking

    gateway.stop()
