import time
import signal
import re
import sdnotify         # Systemd notify - communicate with systemd service
import json
import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from mbus import GenericDevice as gendev
from htutil import log
from htutil import easyyaml
'''
Abbreviation Table:
===================
    dev = DEV = device
'''
#Global array of opened M-Bus devices and their status (Used in main() and nats_reply_cb()
devdesc_arr = []
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
    for index in range(len(devdesc_arr)):
        if devdesc_arr[index]['device_name'] == device_name:
            return(devdesc_arr[index])
    return(None) # Not found

async def nats_reply_cb(msg):
    message = msg.data.decode()
    res="Error condition"

    # Client request
    match message: 
        case 'devices':
            # csvfile object is not JSON serializable
            # Hack to remove csvfile object from devdesc_arr
            alldevicesinfo=[]
            for i in devdesc_arr:
                deviceinfo={}
                for j in i.items():
                    if j[0] != 'csvfile':
                        deviceinfo[j[0]] = j[1]
                alldevicesinfo.append(deviceinfo)

            res = json_ser(alldevicesinfo)
        case message if re.match('^headline.*',message):
            p=re.compile("^\S+\s*(.*)")
            m=(p.match(message))
            if m.group(1) == '':
                res=b"ERROR: Missing device type"
            else:
                res=json_ser(gendev.headline(m.group(1)))
        case message if re.match('^cleardelta.*',message):
            p=re.compile("^\S+\s*(.*)")
            m=p.match(message)
            if m.group(1) == '':
                res=b"ERROR: Missing device name"
            else:
                devdesc=devdesc_get(m.group(1))
                if devdesc == None:
                    res=b"ERROR: Non existing device name"
                else:
                    await gendev.clear_delta(devdesc)
                    res=b"OK"
        case _:
            res = b"Unknown message received"
            
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
    gendev.init(easyyaml.get('mbus','tty'),easyyaml.get('mbus','baud'))

    devices=easyyaml.get('mbus','devices')
    for dev in devices:
        devdesc_arr.append(await gendev.open(dev['address'],dev['name'],dev['type']))

    mbuscount=0
    while True:
        for devdesc in devdesc_arr:
            root = await gendev.read(devdesc)
            if root == None:
                await nc.publish("{}{}{}".format(easyyaml.get('nats','mbusdevice'),devdesc['device_name'], '.error'), b"Error reading from device")
                continue

            natsdata = json_ser(root)
            await nc.publish("{}{}{}".format(easyyaml.get('nats','mbusdevice'),devdesc['device_name'], '.data'), natsdata)

        # Cheating - All use same time interval
        mbuscount = mbuscount + 1
        await nc.publish(easyyaml.get('display','displaytopic'), bytes("Count: {}".format(mbuscount), 'utf-8'))

        # Dont sleep when in debug mode as MQTT subscriber (Wait for MQTT publisher instead)
        if easyyaml.get('debug','mqttsub') != True:
            await asyncio.sleep(easyyaml.get('mbus','pollinterval'))

if __name__ == '__main__':
    asyncio.run(main())
