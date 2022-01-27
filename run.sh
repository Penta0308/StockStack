#!/bin/bash

rm -f /etc/nginx/sites-enabled/*
mkdir /run/stockstack
cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

#useradd -M stockstack -g www-data

#chown www-data:stockstack /run/stockstack

python stockstacker/startup.py

#nginx -s reload