from stockstacker import nginx_util

HELP_MESSAGE = """create market: c name
delete market: d name
reload all market: r"""

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(HELP_MESSAGE)
    elif sys.argv[1] == 'c':    # CREATE
        print(sys.argv[2])
    elif sys.argv[1] == 'd':    # DELETE
        print(sys.argv[2])
    elif sys.argv[1] == 'r':    # RELOAD
        print(nginx_util.proxys_read())
    else:
        print(HELP_MESSAGE)
else:
    while True:
        pass
