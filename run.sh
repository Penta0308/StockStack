#!/bin/bash

rm -f /etc/nginx/sites-enabled/*
cp ./config/server.conf /etc/nginx/sites-enabled/server.conf

python stockstacker/startup.py

nginx -s reload