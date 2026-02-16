#!/bin/bash
REMOTE_HOST="heth.dk"
REMOTE_PORT="9998"
REMOTE_USER="heth"

#Autossh
autossh -M 0 -gNC $1 -o "ExitOnForwardFailure=yes" -o "ServerAliveInterval=10" -o "ServerAliveCountMax=3" -R ${REMOTE_PORT}:127.0.0.1:22 ${REMOTE_USER}@${REMOTE_HOST}


