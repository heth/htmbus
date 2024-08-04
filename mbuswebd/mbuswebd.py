# See https://flask.palletsprojects.com/en/2.3.x/quickstart/#a-minimal-application
# Run: flask --debug --app hello2 run --host=0.0.0.0
# HACK om python 3.10
# Change line 49 in /home/heth/flask/nav2/venv/lib/python3.10/site-packages/flask_nav/__init__.py to
#    class ElementRegistry(collections.abc.MutableMapping):
# Flask_nav - See: https://www.youtube.com/watch?v=EJwGV1gjVkY
import asyncio
from flask import Flask, render_template, request
from flask import send_from_directory
from flask_socketio import SocketIO, emit
from queue import Queue
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_bootstrap import Bootstrap
from flask_autoindex import AutoIndex
#from werkzeug.middleware.proxy_fix import ProxyFix
from dominate.tags import img
import re
import time
import os
from htutil import easyyaml
from htutil import easyjson
import nats_thread
#import threading

# Init is here when running unicorn - __main__ never runs
yamlfile="/etc/mbus/mbus.yaml"
number_of_threads = 1
threads=0
work_queue = Queue()
async_mode=None

app = Flask(__name__, instance_relative_config=True)  # Relative_config looks in templates dir
socketio = SocketIO(app,async_mode=async_mode)
nav = Nav(app)
Bootstrap(app)
img()
branding = img(src="static/MBusLogo240.jpg", height='20')
nav.register_element('mbus_navbar', Navbar(branding, #'Main menu',
                                           # Text('MAIN MENU'),
                                           View('Home page', 'index'),
                                           View('Stand 1', 'stand1'),
                                           View('Stand 2', 'stand2'),
                                           View('Alle stande', 'alldevices'),
                                           View('Status stande', 'statusdevices'),
                                           ))
def scroll_worker():
    print("scroll_worker starts")
    count=0

    while True:
        rawdata = nats_thread.dataget()
        
        # Field 2 in entries contain data
        data=[]
        for i in rawdata:
            data.append(i[2])

        socketio.emit('kam603updateall', {'data': data})
        count = count + 1
        if data[2] == 'stand1':
            socketio.emit('kam603updatestand1', {'data': data})
        if data[2] == 'stand2':
            socketio.emit('kam603updatestand2', {'data': data})

        print("-----------------------> Count: {}                                       ".format(count),end='\r',flush=True)


@app.route("/navpage")
def navpage():
    return render_template('navpage.html')


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/statusdevices")
def statusdevices():
    # Example:  [{"address": "68", "timestamp": 1722343820, "count": 826, "error": 0, "device_name": "stand1", "delta": {"\u0394Power": 0, "\u0394Vol flow": 0.0, "\u0394Energy": 1}, "manufacturer": "KAM", "version": "53", "name": "Kamstrup Multical 603"}
    return render_template('devices.html')

@app.route("/stand1")
def stand1():
    headline = nats_thread.headlineget() 
    headings = []
    for i in headline:
        headings.append(i[0])
    return render_template('stand1.html',headings=headings)

@app.route("/stand2")
def stand2():
    headline = nats_thread.headlineget() 
    headings = []
    for i in headline:
        headings.append(i[0])
    return render_template('stand2.html',headings=headings)

@app.route("/csvfile/<name>")
def csvfile():
    headings = ("Fabrikant","Model","Farve","Årstal")
    # Appending app path to upload folder path within app root folder
    #uploads = os.path.join(current_app.root_path, app.config['static/doc'])
    uploads = os.path.join(app.root_path, 'static/doc')
    #filename="hej"
    print("Directory" + uploads,flush=True)
    # Returning file from appended path
    #return send_from_directory(directory=uploads, filename="hej")
    return send_from_directory(uploads, "hej")
    return render_template('dokumentation.html',headings=headings)


@socketio.on('connect')
def kam603_connect():
    global threads
    ipaddr = request.remote_addr
    server = request.server
    print("IPADDR: " + str(ipaddr))
    print("SERVER: " + str(server[0]) + " All: " + str(server))
    #emit('after connect', {'data': 'Lets dance'})
    print("About to start worker")
    if threads < number_of_threads:
        threads = threads + 1
        socketio.start_background_task(scroll_worker)
        print("-------------------------------------------> WORKER STARTED")


#@app.route("/alldevices/<name>")
@app.route("/alldevices")
async def alldevices():
    headline = nats_thread.headlineget() 
    headings = []
    for i in headline:
        headings.append(i[0])
    return render_template('alldevices.html',headings=headings)

def main():
    easyyaml.init(yamlfile)
    # Start asyncio event loop in new thread
    # See: https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058?permalink_comment_id=3895920
    nats_thread.init()
    app.run(debug=False,host="0.0.0.0")
    

if __name__ == '__main__':
    asyncio.run(main())

