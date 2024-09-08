#!/usr/bin/python3
import asyncio
import locale
from mbus import mbus 
from mbus import kam603 #, gav340     # M-Bus device specific modules

# Call wrapper for M-Bus device specific modules
wrap = {
    "kam603": kam603,
#    "gav340": gav340
}

"""
generic_device.py - M-Bus generic device 

Explore device data for specific manufactorer and type - the decode data in devicespecific module
"""
def init(tty, baudrate):
    locale.setlocale(locale.LC_ALL, 'da_DK.UTF-8') # For creating , as decimal point in float in CSV-file
    mbus.init(tty, baudrate)


async def open(address, device_name, device_type, description):
    """Creat device-descriptor to M-Bus device. Needed for further access such as read()."""
    devdesc = mbus.open(address)
    devdesc.update(
        {
            'device_name': device_name,
            'device_type': device_type,
            'description': description,
            'csvfile': None
        }
    )
    await clear_delta(devdesc)
    await wrap[device_type].open(devdesc)
    return(devdesc)

def parse_json(devdesc, mbus_data):
    return(wrap[devdesc['device_type']].parse_json(devdesc,mbus_data))

def parse(devdesc, root):
    return(wrap[devdesc['device_type']].parse(devdesc, root))

async def read(devdesc):
    """ 
    Read and parses data from mbus device on open M-Bus device described in devdesc..

    On succes returns prepared array of arrays - each inner array a datapoint as described in devicespecific display_format
    descriptor. Example of successfull return:

     [["Date", "str", "24/06/2024", "Date"], ["Time", "str", "04:52:01", "Time"], ["Device", "str"], ["Flow temp", "float", 22.92, "\u00b0C"]]

    On error returns None

    """
    return(await wrap[devdesc['device_type']].read(devdesc))


async def read_raw(devdesc):
    return(wrap[devdesc['device_type']].read_raw(devdesc))

def headline(device_type):
    if not device_type in wrap.keys():
        return('ERROR: Non existing device type') # Non exixting device_type
    return(wrap[device_type].headline())

async def clear_delta(devdesc):
    await wrap[devdesc['device_type']].clear_delta(devdesc)
