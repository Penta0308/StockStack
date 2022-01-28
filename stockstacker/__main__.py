import os
import signal
import subprocess

from stockstacker import nginx_util

HELP_MESSAGE = """create market: c name
reload all market: r"""

def find_online():
    return [x for x in os.listdir('/run/stockstack')]

def start_offlines():
    pr = nginx_util.proxys_read()
    for x in set([x['x'] for x in pr]) - set(find_online()):
        start_sheet(**nginx_util.proxy_prop(x, pr=pr))

def start_sheet(x, p):
    subprocess.Popen(['python', '-m', 'stocksheet', str(x), str(p)])

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        def main_boot():
            print(nginx_util.proxys_read())
            nginx_util.nginx_restart()
            start_offlines()
            signal.pause()  # WAIT
        main_boot()
    elif sys.argv[1] == 'c':    # CREATE
        def main_create():
            n = sys.argv[2]
            p = nginx_util.proxy_create(n)
            nginx_util.nginx_reload()
            start_sheet(n, p)
        main_create()
    elif sys.argv[1] == 'r':    # RELOAD
        def main_reload():
            nginx_util.nginx_reload()
            start_offlines()
        main_reload()
    else:
        print(HELP_MESSAGE)
