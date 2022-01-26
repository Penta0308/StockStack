#!/bin/bash

rm -f /etc/nginx/sites-enabled/*
cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

mkdir /run/stockstack

python stockstacker/startup.py

nginx -s reload