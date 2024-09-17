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
    '''
    Get M-Bus json-data from NATS and convert it to Thingsboard gateway json format

    example:
     mbus_data_byte:
           b'[["Date", "str", "17/09/2024", "Date"], ["Time", "str", "13:09:41", "Time"], ["Device", "str", "stand1", "Name"]]

     mbus_data:
           {"Date": "17/09/2024", "Time": "12:35:51", "Device": "stand1}

     gateway format to thingsboard:
           {'device_name': [{'Date': '17/09/2024', 'Time': '12:35:51', 'Device': 'stand1'}]}"
    '''
    mbus_data=json.loads(mbus_data_byte.decode())

    # Use only entries [0] and [2] from mbus_data_byte to thingsboard
    mbus_dict={}
    for entry in mbus_data:
        mbus_dict[entry[0]]=entry[2]

    # Build thingsboard gateway data structure
    tb_gw = {device_name: [ mbus_dict ]}

    #serialize it
    tb_gw_byte = json.dumps(tb_gw)
    return(tb_gw_byte)

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
    subtopics=re.split("\.",msg.subject)
    try:
        if subtopics[3] == easyyaml.get('nats','subtopic_data'):
            json_data=parse_json(subtopics[2], msg.data)
            mqttclient.publish(easyyaml.get('mqtt','gatewaytopic'),json_data)
            if reconnects > 0:
                status.info("Retry connection attempts: {}".format(reconnects))
    except Exception as e:
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
    mqttclient=gmqtt.Client(easyyaml.get('mqtt','clientid'))
    mqttclient.on_message=mqtt_message
    mqttclient.on_connect=mqtt_connect
    mqttclient.on_disconnect=mqtt_disconnect
    mqttclient.on_subscribe=mqtt_subscribe

    mqttclient.set_auth_credentials(
        username=easyyaml.get('mqtt','username'),
        password=easyyaml.get('mqtt','password')
    )
    try:
        await mqttclient.connect(
            host=easyyaml.get('mqtt','brokerip') or "127.0.0.1",
            keepalive=easyyaml.get('mqtt','keepalive') or 300,
            port=easyyaml.get('mqtt','port') or 1883
        )
        return True
    except Exception as e:
        reconnects = reconnects + 1
        status.warning("Connection to Thingsboard MQTT failed (Retrying: {}): {}".format(reconnects,e))
        mqttclient._disconnected = asyncio.Future()
        return False
        log.warn('Connection failed; Reconnecting ')

def mqtt_connect(client, flags, rc, properties):
    mqttclient.subscribe(easyyaml.get('mqtt','request'))


async def mqtt_message(client, topic, payload, qos, properties):
    data=json_deser(payload)
    response = await natsclient.request(easyyaml.get('nats','request'),bytes(data['params'],"utf8"))


def mqtt_disconnect(client, packet, exc=None):
    log.warn('[DISCONNECTED {}]'.format(client._client_id))


def mqtt_subscribe(client, mid, qos, properties):
    log.info('[SUBSCRIBED {}] QOS: {}'.format(client._client_id, qos))

async def main():
    easyyaml.init(defaultyaml)
    log.init()
    await nats_start(easyyaml.get('nats','devicetopic'))
    while await mqtt_start() == False:
        print("3: What's up doc?")
        await asyncio.sleep(10)
    while True:
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())

