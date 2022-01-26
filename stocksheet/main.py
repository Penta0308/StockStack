import logging
import argparse

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
    multiprocessing.set_start_method('spawn')

    Settings.load()
    dbinfo = {**(Settings.get()['database'])}

    from stocksheet.worker import WorkerManager

    auth = Auth(dbinfo)

    gateway = Gateway(auth, **(Settings.get()['server']))
    """
    ,
    "_sslcert": {
      "cert": "cert.pem",
      "key": "cert.pem"
    }
    """

    #for marketident in marketidents:
    #    workerprocess = WorkerProcess(dbinfo)
    #    workerprocess.start()
    #    workerprocess.queue(f'load {marketident}')
    #    gateway.workers_register(marketident, workerprocess)

    Settings.maincontext_put(globals())

    gateway.start()  # blocking

    gateway.stop()
