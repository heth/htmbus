#!/usr/bin/bash
#Uncomment easyyaml + natsstart
cd /home/debian/htmbus/mbuswebd
source venv/bin/activate
#gunicorn --config ./gunicorn_config.py --worker-class eventlet mbuswebd:app
#gunicorn --config ./gunicorn_config.py --worker-class gevent mbuswebd:app
gunicorn --config ./gunicorn_config.py mbuswebd:app
