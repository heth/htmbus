import gpiod
from gpiod.line import Direction, Value
import smbus2 as smbus
import sys
import time
import datetime
from threading import Thread, Event, Lock
import get_ipv4
import nats
from htutil import easyyaml

# Implementaion of Newhaven 2x20 characters 3v3 display
# Link: https://newhavendisplay.com/content/specs/NHD-C0220BiZ-FSW-FBW-3V3M.pdf
# Implementation on Beagbone Black
# Info on python gpiod: https://pypi.org/project/gpiod/ and https://www.acmesystems.it/libgpiod
#  and https://www.kernel.org/doc/html/v4.19/driver-api/gpio/index.html ( C but explains concepts)

def eprint(*args, **kwargs):
    printt(*args, file=sys.stderr, **kwargs)

def dsp_init():
#Reset display with RESET gpio line
    global request
    request = gpiod.request_lines(
        easyyaml.get('display','gpiochip'),
        consumer="M-Bus display reset",
        config={
            easyyaml.get('display','gpiopin'): gpiod.LineSettings(
                direction=Direction.OUTPUT, output_value=Value.ACTIVE
            )   
        },
    )
    request.set_value(easyyaml.get('display','gpiopin'), Value.INACTIVE)
    time.sleep(10/1000)
    request.set_value(easyyaml.get('display','gpiopin'), Value.ACTIVE)
    time.sleep(40/1000)

#I2C initialize
    global i2cdsp
    global dsp_write_lock
    dsp_write_lock = Lock()

    dsp_write_lock.acquire()
    i2cdsp=smbus.SMBus(easyyaml.get('display','i2cbus'))

    initdata=[0x38,0x39,0x14,0x78,0x5E,0x6D,0x0C,0x01,0x06,0x86];
    for i in initdata:
        i2cdsp.write_byte_data(easyyaml.get('display','i2caddr'),easyyaml.get('display','cmd_reg'),i)
        time.sleep(1/1000)
    dsp_write_lock.release()


def dsp_writeyx(y, x, txt):
    x-=1    # First character in line 1 not 0
    line=[easyyaml.get('display','line1'), easyyaml.get('display','line2')]
    if y < 1 and y > 2:
        eprint("WARNING: Attempt to write on illegal display line")
        return
    dsp_write_lock.acquire()

    i2cdsp.write_byte_data(easyyaml.get('display','i2caddr'), easyyaml.get('display','cmd_reg'), line[y-1]+x)
    for char in txt:
        i2cdsp.write_byte_data(easyyaml.get('display','i2caddr'), easyyaml.get('display','data_reg'), ord(char))
    dsp_write_lock.release()

def dsp_clear():
    dsp_write_lock.acquire()
    i2cdsp.write_byte_data(easyyaml.get('display','i2caddr'), easyyaml.get('display','cmd_reg'), 0x01)
    dsp_write_lock.release()

#### NATS implementation
async def nats_start(subject):
    global nc
    nc = await nats.connect(easyyaml.get('nats','connect_str'))
    sub = await nc.subscribe(subject, cb=nats_handler)

def nats_stop():
    nc.close()

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
    event.clear()
    thread.join()
