import quart_flask_patch
import asyncio
import socketio
import threading
from quart import Quart, render_template, websocket
from quart_cors import cors
import uvicorn
import nats
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_bootstrap import Bootstrap
from dominate.tags import img
from datetime import datetime
import views

#Local modules
from htutil import easyyaml
from htutil import easyjson
from htutil import log
import htnats

# Init and globals
yamlfile="/etc/mbus/mbus.yaml"  # Generel configuration
branding = img(src="static/MBusLogo240.jpg", height='20')
CORS_ALLOWED_ORIGINS = "*"



class QuartSIO:
    def __init__(self) -> None:
        self.sio = socketio.AsyncServer(
            async_mode="asgi", cors_allowed_origins=CORS_ALLOWED_ORIGINS
        )
        self._quart_app = Quart(__name__)
        self._quart_app = cors(self._quart_app, allow_origin=CORS_ALLOWED_ORIGINS)
        self._sio_app = socketio.ASGIApp(self.sio, self._quart_app)
        self.route = self._quart_app.route
        self.add_url_rule = self._quart_app.add_url_rule
        self.on = self.sio.on
        self.emit = self.sio.emit
        self.start_background_task = self.sio.start_background_task

    async def _run(self, host: str, port: int):
        try:
            print("STARTUP")
            easyyaml.init(yamlfile)
            log.init(level=3)
            await htnats.init()
            views.init(self._quart_app)
            nav=Nav(self._quart_app)
            nav.register_element('mbus_navbar', Navbar(branding, #'Mercantec',
                                           View('Home page', 'index'),
                                           View('Status', 'status'),
                                           #View('Status devices', 'statusdevices'),
                                           View('Stand 1', 'stand1'),
                                           View('Stand 2', 'stand2'),
                                           #View('Alle stande', 'alldevices'),
                                           ))
            Bootstrap(self._quart_app)
            img()
            self.sio.start_background_task(scroll_worker)
            uvconfig = uvicorn.Config(self._sio_app, host=host, port=port)
            server = uvicorn.Server(config=uvconfig)

            await server.serve()
        except KeyboardInterrupt:
            print("Shutting down")
        finally:
            print("Bye!")

    def run(self, host: str, port: int):
        asyncio.run(self._run(host, port))


app = QuartSIO()
#app.add_url_rule('/stand2', view_func=views.stand2)


async def scroll_worker():
# Socketio see: https://github.com/miguelgrinberg/python-socketio/discussions/777
    print("scroll_worker starting")
    count=0

    while True:
        print("scrool_worker - thread ID is {}".format(threading.get_native_id()),flush=True)
        rawdata = await htnats.dataget()
        if rawdata == None:
            log.error("scroll_worker: nats_thread.dataget() failed")
            time.sleep(5)
            continue
        data=[]
        for i in rawdata:
            data.append(i[2])

        await app.emit('kam603updateall', {'data': data})

        count = count + 1
        if data[2] == 'stand1':
            await app.emit('kam603updatestand1', {'data': data})
        if data[2] == 'stand2':
            await app.emit('kam603updatestand2', {'data': data})

        print("-----------------------> Count: {}                                       ".format(count),flush=True)

@app.route("/")
async def index():
    broker=easyyaml.get('mqtt','brokerip') # Broker contains ThingsBoard
    csvserver=easyyaml.get('web','csvserver') # Broker contains ThingsBoard
    return await render_template('index.html',broker=broker, csvserver=csvserver)

@app.route("/status")
async def status():
    #devfields = ['device_name','device_type','address','timestamp','count','error']
    devfields = ['device_name','manufacturer','model','serial','address','timestamp','count','error']
    headline=['Name','Manufacturer','Model','Serial','M-Bus Address','Last seen','Successful reads','Failed reads']
    #headline=['Name','Type','M-Bus Address','Last seen','Successful reads','Failed reads']
    devinfo=[]
    devstatus = await htnats.devices_get()
    if devstatus == None:
        log.error("Route /status: nats_thread.dataget() failed")
    else:
        for dev in devstatus:
            if dev['timestamp'] == None:
                dev['timestamp'] = "Never seen"
            else:
                localtime = datetime.fromtimestamp(dev['timestamp'])
                dev['timestamp'] = localtime.strftime("%d/%m/%Y %H:%M:%S")
            info=[]
            for field in devfields:
                if dev[field] == None:   # If device never seen
                    dev[field] = '?'
                info.append(dev[field])
            devinfo.append(info)

    print("device: {}".format(devinfo))
    return await render_template('status.html', headline=headline, devinfo=devinfo)

@app.on("connect")
async def on_connect(sid, environ):
    print("Connected sid = {}".format(sid))

@app.on("disconnect")
async def on_disconnect(sid):
    print("Disconnected sid = {}".format(sid))


@app.route("/stand1")
async def stand1():
    headline = htnats.headlineget()
    headings = []
    for i in headline:
        headings.append(i[0])
    return await render_template('stand1.html',headings=headings)

@app.on("*")
async def on_message(message, sid, *args):
    print("Message:", message, args)
    await app.emit("echo", message)

if __name__ == "__main__":
    #app.run("localhost", 5000)
    app.run("0.0.0.0", 5000)
