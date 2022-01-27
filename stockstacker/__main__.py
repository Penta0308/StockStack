from stockstacker import nginx_util

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(
"""create market: c name
delete market: d name
reload all market: r""")
    elif sys.argv[1] == 'c':
        print(sys.argv[2])
    elif sys.argv[1] == 'd':
        print(sys.argv[2])
    elif sys.argv[1] == 'r':
        print(nginx_util.proxys_read())

while True:
    pass
