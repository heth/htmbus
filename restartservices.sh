#!/usr/bin/env bash
SERVICES="displayd mbusbed mbuswebd mbustbd"
echo -e "Restaring $SERVICES"
sudo systemctl restart $SERVICES
