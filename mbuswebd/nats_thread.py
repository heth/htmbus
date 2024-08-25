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


# --> All code below is run by main-thread
# init() is run from main thread() which starts a new thread with thread_start()
def init():
    global natglo
    natglo['loop']=asyncio.new_event_loop()
    natglo['thread']=threading.Thread(target=start_background_loop, args=(natglo['loop'],), daemon=True)
    natglo['thread'].start()
    task = asyncio.run_coroutine_threadsafe(nats_thread(), natglo['loop'])
    natglo['lock'] = threading.Lock()
    print("nats_init done")

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
    
def headlineget():
    return(natglo['headline'])

# No queueing of data as latest is sufficient
# natglo['lock'] is used between main-thread and nats-thread to synchronize
natsdata=None # global natsdata is used to deliver data from nats-thread to main-thread
def dataget():
    print("Getting data thread ID is {}".format(threading.get_native_id()),flush=True)
    natglo['lock'].acquire()
    print("Got the data thread ID is {}".format(threading.get_native_id()),flush=True)
    data=natsdata
    return(data)

# --> All code below is run by nats_thread created by init

def dataput(data):
    global natsdata
    print("Putting data thread ID is {} native is {}".format(threading.get_ident(), threading.get_native_id()),flush=True)
    natsdata=data
    if natglo['lock'].locked() == True:
        natglo['lock'].release()

# nats_start() starts nats - called from thread initialized in init()
async def nats_start(subject):
    global natglo

    print("Natsstart thread ID is {} native is {}".format(threading.get_ident(), threading.get_native_id()),flush=True)
    print("Natsstart on subject: {}".format(subject))
    try:
        natglo['client'] = await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
        print("Natsstart 2",flush=True)
        natglo['sub'] = await natglo['client'].subscribe(subject, cb=nats_sub_handler)
        print("Natsstart 3",flush=True)
    except Exception as e:
        print("Something went wrong: {}".format(e))

    natglo['headline'] = "ERROR" # Default value
    while True:
        try:
            natglo['headline'] = await natglo['client'].request(easyyaml.get('nats','request'),b"headline kam603") # Wait until ready
            print("Nats headline er {}".format(natglo['headline']))
            break
        except:
            pass
    natglo['headline'] = easyjson.deser(natglo['headline'].data)
    print("headline = {}".format(natglo['headline']))
    print("NATS started on subject: {}".format(subject))
    natglo['lock'].acquire()

async def nats_sub_handler(msg):
    subtopics=re.split("\.",msg.subject)
    if subtopics[3] == easyyaml.get('nats','subtopic_data'):
        json_data=easyjson.deser(msg.data)
        dataput(json_data)
        return()
    if subtopics[3] == easyyaml.get('nats','subtopic_error'):
        return()

async def nats_thread():
    print("Thread running")
    await nats_start(easyyaml.get('nats','devicetopic'))
    print("NATS running")
    while True:
        await asyncio.sleep(60)



def start_background_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

