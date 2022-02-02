import logging
import os
import signal
import multiprocessing

import stocksheet.__main__
from stockstacker import nginx_util

HELP_MESSAGE = """loop: l
create market: c name
reload all market: r"""


def find_online():
    return [x for x in os.listdir("/run/stockstack")]


def start_offlines(renew=False):
    pr = nginx_util.proxys_read()
    onl = find_online()
    if renew:
        for x in onl:
            os.remove(f"/run/stockstack/{x}")
        onl = find_online()
    logger.debug(f"StockStacker Found: {pr} Running: {onl}")
    for x in set([x["x"] for x in pr]) - set(onl):
        start_sheet(**nginx_util.proxy_prop(x, pr=pr))


def start_sheet(x, p):
    logger.debug(f"Stockstack {x} Firing")
    sys.path.append(".")
    from stocksheet import __main__

    sheet = multiprocessing.Process(target=stocksheet.__main__.run, args=(x, str(p)))
    sheet.start()


logger = None
loglevel = logging.DEBUG

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    import sys

    if len(sys.argv) < 2:
        print(HELP_MESSAGE)
    elif sys.argv[1] == "l":

        def main_boot():
            global logger
            logger = multiprocessing.log_to_stderr(loglevel)
            nginx_util.nginx_restart()
            start_offlines(renew=True)
            signal.pause()  # WAIT

        main_boot()
    elif sys.argv[1] == "c":  # CREATE

        def main_create():
            global logger
            logger = logging.getLogger()
            logger.setLevel(loglevel)
            n = sys.argv[2]
            p = nginx_util.proxy_create(n)
            nginx_util.nginx_reload()
            start_sheet(n, p)

        main_create()
    elif sys.argv[1] == "r":  # RELOAD

        def main_reload():
            global logger
            logger = logging.getLogger()
            logger.setLevel(loglevel)
            nginx_util.nginx_reload()
            start_offlines()

        main_reload()
    else:
        print(HELP_MESSAGE)
