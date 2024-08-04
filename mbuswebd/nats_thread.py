# NATS thread code 
# Start an asyncio thread and retreive data from mbusedb - M-Bus back end daemon
# Uses semaphore to indicate to main-thread data is ready
import asyncio
import threading
import nats
import re
from htutil import easyyaml
from htutil import easyjson

#await nats_start(easyyaml.get('nats','devicetopic'))
# Main thread<->init()-- new thread --> 
natglo={}  # nats globals
#natsclient=None
#natslock=None   # threading.Lock() between asynio nats and Flask
#natsdata=None   # Data protected by natslock

# init() is run from main thread() which starts a new thread with thread_start()
def init():
    global natglo
    natglo['loop']=asyncio.new_event_loop()
    #loop=asyncio.new_event_loop()
    natglo['thread']=threading.Thread(target=start_background_loop, args=(natglo['loop'],), daemon=True)
    natglo['thread'].start()
    task = asyncio.run_coroutine_threadsafe(leg_thread(), natglo['loop'])

# nats_start() starts nats in 
async def nats_start(subject):
    global natglo
    #global natsclient
    #global natslock
    #natglo['lient'] = await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
    print("Natsstart",flush=True)
    print("Natsstart on subjrct: {}".format(subject))
    try:
        natglo['client'] = await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
        print("Natsstart 2",flush=True)
        natglo['sub'] = await natglo['client'].subscribe(subject, cb=nats_sub_handler)
        print("Natsstart 3",flush=True)
    except Exception as e:
        print("Something went wrong: {}".format(e))
        #natglo['headline'] = await natglo['client'].request(easyyaml('nats','request'),bytes("headline","utf8")) # Wait until ready
        #natglo['headline'] = await natglo['client'].request(easyyaml.get('nats','request'),bytes("headline","utf8")) # Wait until ready
    natglo['headline'] = "ERROR"
    while True:
        try:
            natglo['headline'] = await natglo['client'].request(easyyaml.get('nats','request'),b"headline") # Wait until ready
            #natglo['headline'] = await natglo['client'].request("futtog.vogn",b"headline") # Wait until ready
            print("Nats headline er {}".format(natglo['headline']))
            break
        except:
            pass
    natglo['headline'] = easyjson.deser(natglo['headline'].data)
    #print("headline = {}".format(natglo['headline'].data))
    print("headline = {}".format(natglo['headline']))
    print("NATS started on subject: {}".format(subject))
    natglo['lock'] = threading.Lock()
    natglo['lock'].acquire()

async def nats_sub_handler(msg):
    #print("NATS subhandler engaged")
    subtopics=re.split("\.",msg.subject)
    if subtopics[3] == easyyaml.get('nats','subtopic_data'):
        json_data=easyjson.deser(msg.data)
        dataput(json_data)
        return()
    if subtopics[3] == easyyaml.get('nats','subtopic_error'):
        #print(str(msg.data, encoding='utf-8'))
        return()

async def leg_thread():
    print("Thread running")
    await nats_start(easyyaml.get('nats','devicetopic'))
    print("NATS running")
    while True:
        await asyncio.sleep(5)

# No queueing of data as latest is sufficient
natsdata=None
def dataget():
    natglo['lock'].acquire()
    data=natsdata
    return(data)

def dataput(data):
    global natsdata
    natsdata=data
    if natglo['lock'].locked() == True:
        natglo['lock'].release()

def headlineget():
    return(natglo['headline'])

async def sub_handler(msg):
    #print("NATS subhandler engaged...")
    #print("RAW: {}".format(msg.data))

    subtopics=re.split("\.",msg.subject)
    if subtopics[3] == easyyaml.get('nats','subtopic_data'):
        json_data=easyjson.deser(msg.data)
        print(json_data)
        return()
    if subtopics[3] == easyyaml.get('nats','subtopic_error'):
        print(msg.data)
        return()

def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

async def thread_start():
    #print("Thread running {}".format(data))
    print("Thread running")
    await start(easyyaml.get('nats','devicetopic'))
    print("NATS running")
    while True:
        await asyncio.sleep(5)
        #time.sleep(5)
        print("Woke up")

