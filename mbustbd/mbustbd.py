#!/home/debian/htmbus/mbustb/venv/bin/python3

import asyncio
import gmqtt
import nats
import json
import time
import re
from htutil import log
from htutil import easyyaml
from htutil import status

defaultyaml="/etc/mbus/mbus.yaml"

mqttclient=None
reconnects=0

# Serialize object to json and encode as bytes
def json_ser(object):
    json_string = json.dumps(object)
    return (json_string.encode())

# Deserialize byte coded json string to object
def json_deser(json_string):
    object = json_string.decode()
    return (json.loads(object))


def parse_json(device_name, mbus_data_byte):
    mbus_dict={}
    mbus_data=[]
    temp=mbus_data_byte.decode()
    mbus_data=json.loads(temp)
    for entry in mbus_data:
        mbus_dict[entry[0]]=entry[2]
    json_data=json.dumps(mbus_dict)
    mb2={}
    ar1=[]
    ar1.append(mbus_dict)
    mb2[device_name]=ar1
    jd2=json.dumps(mb2, sort_keys=True, indent=4)
    return(jd2)

#### NATS implementation
#natsdevicetopic="mbus.device.>"
#natsrequest="mbus.request"
natsclient=None
async def nats_start(subject):
    global natsclient
    natsclient = await nats.connect(easyyaml.get('nats','connect_str') or "nats://127.0.0.1:4222")
    sub = await natsclient.subscribe(subject, cb=nats_sub_handler)
    await status.init("mbustbd",natsclient)

def nats_stop():
    natsclient.close()

async def nats_sub_handler(msg):
    global reconnects
    try:
        subtopics=re.split("\.",msg.subject)
        if subtopics[3] == easyyaml.get('nats','subtopic_data'):
            json_data=parse_json(subtopics[2], msg.data)
            #print(json_data)
            mqttclient.publish(easyyaml.get('mqtt','gatewaytopic'),json_data)
            status.info("Retry connection attempts: {}".format(reconnects))
    except:
        reconnects = reconnects + 1
        status.warning("Writing to Thingsboard MQTT failed (Retrying: {}): {}".format(reconnects,e))
        mqttclient._disconnected = asyncio.Future()
        log.warn('Connection lost')


#### MQTT implementation
#mqtttopicdevice="v1/devices/me/telemetry"
#mqtttopicgateway="v1/gateway/telemetry"
#mqttreqdevice="v1/devices/me/rpc/request/+"
async def mqtt_start():
    global mqttclient
    global reconnects
    try:
        mqttclient=gmqtt.Client(easyyaml.get('mqtt','clientid'))
        mqttclient.on_message=mqtt_message
        mqttclient.on_connect=mqtt_connect
        mqttclient.on_disconnect=mqtt_disconnect
        mqttclient.on_subscribe=mqtt_subscribe

        mqttclient.set_auth_credentials(
            username=easyyaml.get('mqtt','username'),
            password=easyyaml.get('mqtt','password')
        )
        #await mqttclient.connect(host="192.168.1.78",keepalive=300,port=1883)
        await mqttclient.connect(
            host=easyyaml.get('mqtt','brokerip') or "127.0.0.1",
            keepalive=easyyaml.get('mqtt','keepalive') or 300,
            port=easyyaml.get('mqtt','port') or 1883
        )
        status.info("Connection attempts: {}".format(reconnects))
        # subscribe moved to mqtt_connect - as reconnect re.subscribes if broker restartet
        #mqttclient.subscribe(easyyaml.get('mqtt','request'))
        return True
    except Exception as e:
        reconnects = reconnects + 1
        status.warning("Connection to Thingsboard MQTT failed (Retrying: {}): {}".format(reconnects,e))
        mqttclient._disconnected = asyncio.Future()
        return False
        print('Connection failed; Reconnecting ')
        #log.warn('Connection failed; Reconnecting ')

def mqtt_connect(client, flags, rc, properties):
    print('[CONNECTED {}]'.format(client._client_id))
    status.info("Connection attempts: {}".format(reconnects))
    #log.info('[CONNECTED {}]'.format(client._client_id))
    #for i in range(1000000):
    #    i=i+1-1
    mqttclient.subscribe(easyyaml.get('mqtt','request'))


async def mqtt_message(client, topic, payload, qos, properties):
    data=json_deser(payload)
    #response = await natsclient.request(natsrequest,bytes(data['params'],"utf8"))
    response = await natsclient.request(easyyaml.get('nats','request'),bytes(data['params'],"utf8"))


def mqtt_disconnect(client, packet, exc=None):
    #log.warn('[DISCONNECTED {}]'.format(client._client_id))
    print('[DISCONNECTED {}]'.format(client._client_id))


def mqtt_subscribe(client, mid, qos, properties):
    #log.info('[SUBSCRIBED {}] QOS: {}'.format(client._client_id, qos))
    print('[SUBSCRIBED {}] QOS: {}'.format(client._client_id, qos))

async def main():
    easyyaml.init(defaultyaml)
    log.init()
    await nats_start(easyyaml.get('nats','devicetopic'))
    #print("1: What's up doc?")
    #await mqtt_start()
    #print("2: What's up doc?")
    while await mqtt_start() == False:
        print("3: What's up doc?")
        await asyncio.sleep(10)
    while True:
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())

