#!/usr/bin/bash
#Uncomment easyyaml + natsstart
source venv/bin/activate
gunicorn --config ./gunicorn_config.py mbuswebd:app
