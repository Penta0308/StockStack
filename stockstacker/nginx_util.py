import os
import re
import subprocess
from glob import glob



def sheet_create(x, p):
    """
    :param x: router name
    :param p: port
    :return: None
    """
    with open(f'/app/data/nginxproxy/{x}.conf', 'w') as f:
        f.write(
f"""location /{x} {{
    proxy_pass http://localhost:{p};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Origin "";
}}""")

def sheet_remove(x):
    os.remove(f'/app/data/nginxproxy/{x}.conf')

rx = re.compile(r"location /(?P<x>\S+?) {.*?proxy_pass http://localhost:(?P<p>\d+).*?}", flags=re.DOTALL|re.MULTILINE)

def sheets_read():
    p = []
    for x in glob('/app/data/nginxproxy/*.conf'):
        with open(x) as f:
            p.append(rx.match(f.read()).groupdict())
    return p

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(
"""read list: r
create: c name port
delete: d name""")
    elif sys.argv[1] == 'r':
        print(sheets_read())
    elif sys.argv[1] == 'c':
        sheet_create(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == 'd':
        sheet_remove(sys.argv[2])

def sheets_reload():
    subprocess.call('nginx -s reload', shell=False)
