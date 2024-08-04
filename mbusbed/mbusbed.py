import time
import signal
import re
import sdnotify         # Systemd notify - communicate with systemd service
import json
import asyncio
from threading import Thread, Event, Lock
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from mbus import kam603
from htutil import log
from htutil import easyyaml
'''
Abbreviation Table:
===================
    dev = DEV = device
'''
#Global array of opened M-Bus devices and their status (Used in main() and nats_reply_cb()
open_dev = []
yamlfile="/etc/mbus/mbus.yaml"

# Serialize object to json and encode as bytes
def json_ser(object):
    json_string = json.dumps(object)
    return (json_string.encode())

# Deserialize byte coded json string to object
def json_deser(json_string):
    object = json_string.decode()
    return (json.loads(object))

def signal_handler(sig):
    print("Stopping mbus handler daemon")
    systemd.notify("Stopping mbus handler daemon")
    exit()

def devdesc_get(device_name):
    for index in range(len(open_dev)):
        if open_dev[index]['device_name'] == device_name:
            return(open_dev[index])
    return(None) # Not found

async def nats_reply_cb(msg):
    message = msg.data.decode()
    res="Error condition"

    # Client request
    match message: 
        case 'devices':
            # csvfile object is not JSON serializable
            # Hack to remove csvfile object from open_dev
            alldevicesinfo=[]
            for i in open_dev:
                deviceinfo={}
                for j in i.items():
                    if j[0] != 'csvfile':
                        deviceinfo[j[0]] = j[1]
                alldevicesinfo.append(deviceinfo)

            res = json_ser(alldevicesinfo)
        case 'headline':
            res = json_ser(kam603.headline())
        case message if re.match('^cleardelta.*',message):
            p=re.compile("^\S+\s*(.*)")
            m=p.match(message)
            if m.group(1) == '':
                res=b"ERROR: Missing device name"
            else:
                device=devdesc_get(m.group(1))
                if device == None:
                    res=b"ERROR: Non existing device name"
                else:
                    await kam603.clear_delta(device)
                    res=b"OK"
        case _:
            res = b"Unknown message received"
            print("Unknown: {}".format(message))
            
    await msg.respond(res)


async def main():
    easyyaml.init(yamlfile)
    log.init(level=3)
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, signal_handler, signal.SIGINT)
    loop.add_signal_handler(signal.SIGTERM, signal_handler, signal.SIGTERM)
    loop.add_signal_handler(signal.SIGQUIT, signal_handler, signal.SIGQUIT)
    global systemd
    systemd = sdnotify.SystemdNotifier()
    systemd.notify("Starting mbus handler daemon")
    nc = await nats.connect(easyyaml.get('nats','connect_str'))

    sub = await nc.subscribe(easyyaml.get('nats','request'), cb=nats_reply_cb)

    # Init serial M-bus port
    kam603.init(easyyaml.get('mbus','tty'),easyyaml.get('mbus','baud'))

    devices=easyyaml.get('mbus','devices')
    for dev in devices:
        open_dev.append(await kam603.open(dev['address'],dev['name']))

    mbuscount=0
    while True:
        for devdesc in open_dev:
            root = await kam603.read(devdesc)
            if root == None:
                await nc.publish("{}{}{}".format(easyyaml.get('nats','mbusdevice'),devdesc['device_name'], '.error'), b"Error reading from device")
                continue

            natsdata = json_ser(root)
            await nc.publish("{}{}{}".format(easyyaml.get('nats','mbusdevice'),devdesc['device_name'], '.data'), natsdata)

        # Cheating - All use same time interval
        mbuscount = mbuscount + 1
        await nc.publish(easyyaml.get('display','displaytopic'), bytes("Count: {}".format(mbuscount), 'utf-8'))
        await asyncio.sleep(easyyaml.get('mbus','pollinterval'))


if __name__ == '__main__':
    asyncio.run(main())
