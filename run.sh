#!/bin/bash

rm --force /etc/nginx/sites-enabled/default || true
mkdir /run/stockstack
cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

#useradd -M stockstack -g www-data

#chown www-data:stockstack /run/stockstack

python -m stockstacker

#nginx -s reload
