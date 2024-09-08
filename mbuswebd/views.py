from quart import  render_template
#from htnats import headlineget
from datetime import datetime

import htnats
from htutil import log
from htutil import status
from htutil import easyyaml
from htutil import easyjson



def init(app):
    app.add_url_rule('/stand2', view_func=stand2)
    app.add_url_rule('/status', view_func=status)


#@app.route("/stand2")
async def stand2():
    headline =  htnats.headlineget()
    headings = []
    for i in headline:
        headings.append(i[0])
    return await render_template('stand2.html',headings=headings)

async def mbus_dev_status():
    ''' Get M-Bus meter status from all devices '''
    devfields = ['device_name','manufacturer','model','serial','address','timestamp','count','error']
    headline=['Name','Manufacturer','Model','Serial','M-Bus Address','Last seen','Successful reads','Failed reads']
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
                    dev[field] = '-'
                info.append(dev[field])
            devinfo.append(info)
    return headline,devinfo

#@app.route("/status")
async def status():

    devheadline,devinfo = await mbus_dev_status()
    svcheadline,svcinfo = await htnats.servicestatus_get()

    return await render_template('status.html',
        devheadline=devheadline, devinfo=devinfo,
        svcheadline=svcheadline, svcinfo=svcinfo
    )


