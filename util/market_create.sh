#!/bin/bash

echo "Enter the market identifier"
read -r market

docker exec stockstack_web_1 python -m stockstacker c "$market"