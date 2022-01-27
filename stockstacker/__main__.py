import subprocess

from stockstacker import nginx_util

HELP_MESSAGE = """create market: c name
reload all market: r"""

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(nginx_util.proxys_read())
        input()  # WAIT
    elif sys.argv[1] == 'c':    # CREATE
        n = sys.argv[2]
        nginx_util.proxy_create(n)
        subprocess.Popen(f'python -m stocksheet {n}')
        print(sys.argv[2])
    elif sys.argv[1] == 'r':    # RELOAD
        print(nginx_util.proxys_read())
    else:
        print(HELP_MESSAGE)
