#!/usr/bin/bash
echo -e "Installing Python virtual environment for M-Bus displayd service"
sudo apt install python3-venv
python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip wheel setuptools requests
pip install gpiod  
pip install smbus2
pip install netifaces
pip install sdnotify
pip install nats-py
