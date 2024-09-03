import asyncio
import threading
import nats
import re
from htutil import easyyaml
from htutil import easyjson


# Global nats reference
glo_nats={}


async def init():
    global glo_nats
    print("Nats.init() - thread ID is {}".format(threading.get_native_id()),flush=True)
    try:
        glo_nats['client'] = await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
        #glo_nats['sub'] = await glo_nats['client'].subscribe(subject, cb=nats_sub_handler)
        glo_nats['sub'] = await glo_nats['client'].subscribe(easyyaml.get('nats','devicetopic'), cb=nats_sub_handler)
    except Exception as e:
        print("nats.init() - Something went wrong initializing nats: {}".format(e))
    
    try:
        glo_nats['lock'] = asyncio.Lock()
        await glo_nats['lock'].acquire()
    except Exception as e:
        print("nats.init() - Something went wrong initializing asyncio.Lock: {}".format(e))

    while True:
        try:
            glo_nats['headline'] = await glo_nats['client'].request(easyyaml.get('nats','request'),b"headline kam603") # Wait until ready
            print("Nats headline er {}".format(glo_nats['headline']))
            break
        except Exception as e:
            print("nats.init() - Couldent get headline: {}".format(e))
            await asyncio.sleep(5)  # Waiting for responder - then try again
            pass
    glo_nats['headline'] = easyjson.deser(glo_nats['headline'].data)
    print("Headline = {}".format(glo_nats['headline']))

def headlineget():
    return(glo_nats['headline'])

async def nats_sub_handler(msg):
    print("Nats.nats_sub_handler() - thread ID is {}".format(threading.get_native_id()),flush=True)
    subtopics=re.split("\.",msg.subject)
    if subtopics[3] == easyyaml.get('nats','subtopic_data'):
        json_data=easyjson.deser(msg.data)
        print("GOT IT: {}".format(json_data))
        dataput(json_data)
        return()
    if subtopics[3] == easyyaml.get('nats','subtopic_error'):
        print("Failed {}".format(msg.data))
        return()
    
natsdata=None # global natsdata is used to deliver data from nats-thread to main-thread

def dataput(data):
    global natsdata
    print("Putting data thread ID is {} native is {}".format(threading.get_ident(), threading.get_native_id()),flush=True)
    natsdata=data
    if glo_nats['lock'].locked() == True:
        glo_nats['lock'].release()

async def dataget():
    print("Getting data thread ID is {}".format(threading.get_native_id()),flush=True)
    await glo_nats['lock'].acquire()
    print("Got the data thread ID is {}".format(threading.get_native_id()),flush=True)
    data=natsdata
    return(data)

async def devices_get():
    sub= await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
    try:
        devstat = await sub.request(easyyaml.get('nats','request'),b"devices")
    except Exception as e:
        print("nats devices_get() - Something went wrong: {}".format(e))
        return(None)
    print("Devstat.data = {}".format(devstat.data))
    await sub.close()
    if devstat.data == None:
        print("To bad")
        return(None)
    return(easyjson.deser(devstat.data))





        
