import asyncio
import quart_flask_patch
from quart import Quart, render_template, websocket
from quart_cors import cors
from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup, Link, Text, Separator
from flask_bootstrap import Bootstrap
from dominate.tags import img
import nats
import socketio
#Local modules
from htutil import easyyaml
from htutil import easyjson
from htutil import log
import htnats

# Init and globals
yamlfile="/etc/mbus/mbus.yaml"  # Generel configuration


app = Quart(__name__)
app = cors(app,allow_origin="*")
nav = Nav(app)
Bootstrap(app)
sio = socketio.AsyncServer()
sio_app = socketio.ASGIApp(sio,app)
#sio.on
#emit=sio.emit
print("DDDDDDDDDDDDDDDDDOOOOOOOOOOOOOOOOOOOOOOOOOOOOONNNNNNNNNNNNNNNNNNNNNNNNEEEEEEEEEEEEEEEEEEEEEE")
#app2 = socketio.ASGIApp(sio)

branding = img(src="static/MBusLogo240.jpg", height='20')
nav.register_element('mbus_navbar', Navbar(branding, #'Main menu',
                                           View('Home page', 'index'),
                                           #View('Status', 'status'),
                                           #View('Status devices', 'statusdevices'),
                                           View('Stand 1', 'stand1'),
                                           View('Stand 2', 'stand2'),
                                           #View('Alle stande', 'alldevices'),
                                           ))

async def scroll_worker():
# Socketio see: https://github.com/miguelgrinberg/python-socketio/discussions/777 
    print("scroll_worker starts")
    count=0

    while True:
        rawdata = await nats_thread.dataget()
        if rawdata == None:
            log.error("scroll_worker: nats_thread.dataget() failed")
            time.sleep(5)
            continue
        #print("rawdata is {}".format(rawdata))

        # Field 2 in entries contain data
        data=[]
        for i in rawdata:
            data.append(i[2])

        sio.emit('kam603updateall', {'data': data})

        count = count + 1
        if data[2] == 'stand1':
            sio.emit('kam603updatestand1', {'data': data})
        if data[2] == 'stand2':
            sio.emit('kam603updatestand2', {'data': data})

        print("-----------------------> Count: {}                                       ".format(count),end='\r',flush=True)

@sio.on('connect')
async def sioconnect():
    print("Starting background task")
    sio.start_background_task(scroll_worker)
    print("End of background taski - should i wait join?")

@app.route("/navpage")
async def navpage():
    return await render_template('navpage.html')

@app.route("/")
async def index():
    return await render_template("index.html",broker="broker", csvserver="csvserver")

@app.route("/stand1")
async def stand1():
    #return {"hello": "world"}
    headline = htnats.headlineget()
    headings = []
    for i in headline:
        headings.append(i[0])
    return await render_template('stand1.html',headings=headings)


@app.websocket("/stand2")
async def stand2():
    while True:
        await websocket.send("hello all you motherfuckers")
        await websocket.send_json({"hello": "world"})
        await websocket.send("hello all you motherfuckers")

# Initialize before WEB-server starts
@app.before_serving
async def startup():
    print("STARTUP")
    easyyaml.init(yamlfile)
    log.init(level=3)
    await htnats.init()
    # See: https://python-socketio.readthedocs.io/en/stable/client.html#installation


if __name__ == "__main__":
    app.run()
