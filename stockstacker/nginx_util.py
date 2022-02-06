import os
import re
import subprocess
from glob import glob


def proxy_create(x, p=None):
    """
    :param x: router name
    :param p: socket
    :return: None
    """
    if p is None:
        p = f"/run/stockstack/stocksheet/{x}"

    with open(f"/app/data/nginxproxy/{x}.conf", "w") as f:
        # noinspection HttpUrlsUsage
        f.write(
            f"""location /{x} {{
    proxy_pass http://unix:{p};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Origin "";
}}"""
        )
    return p


def proxy_remove(x):
    os.remove(f"/app/data/nginxproxy/{x}.conf")


rx = re.compile(
    r"location /(?P<x>\S+?) {.*?proxy_pass http://unix:(?P<p>[\w/.\\\-]+)\s*;.*?}",
    flags=re.DOTALL | re.MULTILINE,
)


# noinspection SpellCheckingInspection
def proxys_read():  # I KNOW plural proxy is proxies
    p = []
    for x in glob("/app/data/nginxproxy/*.conf"):
        with open(x) as f:
            p.append(rx.match(f.read()).groupdict())
    return p


def proxy_prop(x, pr=None):
    if pr is None:
        pr = proxys_read()
    return list(filter(lambda r: r["x"] == x, pr))[0]


HELP_MESSAGE = """read list: r
create: c name sock
delete: d name"""

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(HELP_MESSAGE)
    elif sys.argv[1] == "r":
        print(proxys_read())
    elif sys.argv[1] == "c":
        proxy_create(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "d":
        proxy_remove(sys.argv[2])
    else:
        print(HELP_MESSAGE)


def nginx_restart():
    subprocess.call(["/usr/bin/sudo", "/usr/sbin/service", "nginx", "restart"])


def nginx_reload():
    subprocess.call(["/usr/bin/sudo", "/usr/sbin/service", "nginx", "reload"])
