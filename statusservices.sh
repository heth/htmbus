#!/usr/bin/env bash
SERVICES="displayd mbusbed mbuswebd mbustbd"
echo -e "Status;  $SERVICES"
systemctl status $SERVICES
