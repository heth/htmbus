import psutil
from datetime import datetime
from datetime import timezone
from htutil import easyjson
from htutil import easyyaml

status="OK" # Default status until something goes wrong
status_text=''
identity=''
async def init(id,nats_connect):
    global identity 
    identity = id
    subject=easyyaml.get('nats','request') + '.' + identity
    await nats_connect.subscribe(subject, cb=handler)

def message(newstatus,newmessage):
    global status
    global status_text
    status=newstatus
    status_text=newmessage

def serviceinfo_data_get():
    sitrep=[]
    headln=[]

    # Find this service
    services = easyyaml.get('services','identity')
    sitrep.append(identity)
    for service in services:
        if service['service'] == identity:
            sitrep.append(service['realname']) # Default 'name'

    # Gather info
    pid=psutil.Process()
    sitrep.append(psutil.threading.active_count())
    ts=int(pid.create_time())
    dt=datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M:%S')
    sitrep.append(dt)
    cpu=pid.cpu_times()
    sitrep.append(round(cpu.user+cpu.children_user,2))
    sitrep.append(round(cpu.system+cpu.children_system,2))
    #sitrep.append("{:,}".format(pid.memory_info().rss).replace(',','.'))  # UPS a bit messy getting '.' as thousand separator
    mem=pid.memory_info().rss / (2**20)  
    sitrep.append(float(round(mem,2)))
    sitrep.append(status)   
    sitrep.append(status_text) 
    return sitrep

def serviceinfo_headline_get():
    headln=[]
    headln.append('Service')
    headln.append('Brief')
    headln.append('Threads')
    headln.append('Start time')
    headln.append('CPU time user (Sec)')
    headln.append('CPU time system (Sec)')
    headln.append('Phys. mem. (MB)')
    headln.append('Status')
    headln.append('Status text')
    return headln

async def handler(msg):
    request = msg.data.decode()
    if request == 'status' or request == 'headline':
        sitrep = serviceinfo_data_get()
        await msg.respond(easyjson.ser(sitrep))

##### System load
def systeminfo_get():
    sitrep=[]
    ts=psutil.getloadavg()
    dt=datetime.fromtimestamp(ts).strftime('%d/%m/%Y %H:%M:%S')
    sitrep.append(dt)
    return sitrep
'''
>>> p.boot_time()
1723288306.0
>>> p.getloadavg()
(0.40673828125, 0.12841796875, 0.03955078125)
>>> p.virtual_memory()
svmem(total=506941440, available=322240512, percent=36.4, used=171233280, free=11321344, active=207962112, inactive=221138944, buffers=73506816, cached=250880000, shared=1527808, slab=49201152)
>>> p.disk_usage('/')
sdiskusage(total=7856414720, used=3064860672, free=4419358720, percent=41.0)
>>>
'''

