import gpiod
from gpiod.line import Direction, Value
import smbus2 as smbus
import sys
import time
import datetime
from threading import Thread, Event, Lock
import psutil
import get_ipv4
import nats
from htutil import easyyaml
from htutil import easyjson
from htutil import status

# Implementaion of Newhaven 2x20 characters 3v3 display
# Link: https://newhavendisplay.com/content/specs/NHD-C0220BiZ-FSW-FBW-3V3M.pdf
# Implementation on Beagbone Black
# Info on python gpiod: https://pypi.org/project/gpiod/ and https://www.acmesystems.it/libgpiod
#  and https://www.kernel.org/doc/html/v4.19/driver-api/gpio/index.html ( C but explains concepts)

# Module globals
dsp_functional=True # Is display functional True/False
i2cdsp=''           # Open SMbus file descriptor for i2c bus
dsp_write_lock=''   # Display write lock (Mutex)

def eprint(*args, **kwargs):
    printt(*args, file=sys.stderr, **kwargs)

# Write single byte to open i2cbus 
def dsp_write_byte(address,register,data):
    global dsp_functional   # Is display functional True/False
    if dsp_functional == False:
        return(False)
    try:
        i2cdsp.write_byte_data(address,register,data)
        return(True)
    except:
        dsp_functional = False
        status.message("Warning","Display not functional")
        return(False)


def dsp_init():
    global dsp_functional   # Is display functional True/False
    global i2cdsp           # Open SMbus file descriptor for i2c bus
    global dsp_write_lock   # Display write lock (Mutex)

    # Reset display by issuing a low pulse to XRESET pin on display using GPIO-line
    try:
        resetpin = gpiod.request_lines(
            easyyaml.get('display','gpiochip'),
            consumer="M-Bus display reset",
            config={
                easyyaml.get('display','gpiopin'): gpiod.LineSettings(
                    direction=Direction.OUTPUT, output_value=Value.ACTIVE
                )
            },
        )
        # Set low for at least 1 mS - See: http://www.newhavendisplay.com/app_notes/ST7036.pdf
        resetpin.set_value(easyyaml.get('display','gpiopin'), Value.INACTIVE)
        time.sleep(10/1000)

        # Display busy at least 40 mS - resetting and starting
        resetpin.set_value(easyyaml.get('display','gpiopin'), Value.ACTIVE)
        time.sleep(80/1000)
    except Exception as e:
        dsp_functional = False
        status.message("Warning","Display not functional")
        print("ERROR: Failed to reset display - GPIO-line: {}".format(e))
        return(False)

    #I2C initialize
    dsp_write_lock = Lock()
    dsp_write_lock.acquire()

    try:
        i2cdsp=smbus.SMBus(easyyaml.get('display','i2cbus'))
    except Exception as e:
        dsp_functional = False
        status.message("Warning","Display not functional")
        

    initdata=[0x38,0x39,0x14,0x78,0x5E,0x6D,0x0C,0x01,0x06,0x86];
    for i in initdata:
        dsp_write_byte(easyyaml.get('display','i2caddr'),easyyaml.get('display','cmd_reg'),i)

    time.sleep(1/1000)
    dsp_write_lock.release()
    return(dsp_functional)


def dsp_writeyx(y, x, txt):
    x-=1    # First character in line 1 not 0
    line=[easyyaml.get('display','line1'), easyyaml.get('display','line2')]
    if y < 1 and y > 2:
        eprint("WARNING: Attempt to write on illegal display line")
        return
    dsp_write_lock.acquire()
    try:
        dsp_write_byte(easyyaml.get('display','i2caddr'), easyyaml.get('display','cmd_reg'), line[y-1]+x)
    except Exception as e:
        print("ERROR: Display absent on i2c-bus: {}".format(e))
        dsp_write_lock.release()
        return

    for char in txt:
        dsp_write_byte(easyyaml.get('display','i2caddr'), easyyaml.get('display','data_reg'), ord(char))
    dsp_write_lock.release()

def dsp_clear():
    dsp_write_lock.acquire()
    dsp_write_byte(easyyaml.get('display','i2caddr'), easyyaml.get('display','cmd_reg'), 0x01)
    dsp_write_lock.release()

#### NATS implementation
async def nats_start(subject):
    global nc
    nc = await nats.connect(easyyaml.get('nats','connect_str'))
    sub = await nc.subscribe(subject, cb=nats_handler)
    #status = await nc.subscribe("mbus.status", cb=status_handler)
    await status.init("displayd",nc)

async def nats_stop():
    await nc.close()

async def nats_handler(msg):
    subject = msg.subject
    reply = msg.reply
    # Set string to 15 characters - overwriting existing fields in display
    data = "{:<15}".format(msg.data.decode())
    data = data.ljust(15)[:15]  # Truncate to 15 chars
    dsp_writeyx(1,1, str(data))

#### Clock in thread
def dsp_clock_write(y,x, now, colon_visible):
    if colon_visible == True:
        dsp_writeyx(y,x,now.strftime("%H:%M"))
    else:
        dsp_writeyx(y,x,now.strftime("%H %M"))

def dsp_clock_thread(y,x,event):
    colon_visible=True
    ip=get_ipv4.get_ipv4(easyyaml.get('display','network'))
    dsp_writeyx(2,1,f"IP: {ip:16}")
    while event.is_set():
        now=datetime.datetime.now()
        if colon_visible == True:
            colon_visible=False
        else:
            colon_visible=True
        dsp_clock_write(y,x,now,colon_visible)
        ip_now=get_ipv4.get_ipv4(easyyaml.get('display','network'))
        if ip != ip_now:
            ip = ip_now
            dsp_writeyx(2,1,f"IP: {ip:16}")

        time.sleep(0.5)

def dsp_clock_start(y,x):       # Live clock on pos y,x HH:MM
    global thread
    global event
    event = Event()
    event.set()     # Thread runs when event set
    thread = Thread(target=dsp_clock_thread, args=(y,x,event))
    thread.start()

def dsp_clock_stop():   # Live clock on pos y,x HH:MM:SS
    print("Stop 1")
    event.clear()
    print("Stop 2")
    thread.join()
    print("Stop 3")
