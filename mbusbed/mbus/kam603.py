#!/usr/bin/python3
# 29 perhaps information code - see 603 manual sec. 7.2.2
import asyncio
from datetime import datetime
from collections import namedtuple
import xml.etree.ElementTree as ET
import re
import locale
from mbus import mbus
from htutil import log, csvlog, easyyaml

# Search string(unit) , Function, display string, unit, function (if any), divisor/multiplier, dataformat as in formatted print :xx
# Search string taken from https://github.com/rscada/libmbus which takes it from https://m-bus.com/documentation
# TODO:  8,9,10,11,12,13,14,17,24 - Historik i regnearksfiler - here-and-now i løbende log


"""
kam603.py - M-Bus specific file for Kamstrup Multical 603 Meter-bus devices
"""

#csvdir="/var/www/data/kam603/"
#csvdir="/tmp/"

# Tags searched in each DataRecord in this order.
# mbustags = ('Function','StorageNumber','Unit','Value','Timestamp','Device','Tariff')

# Defines interesting DataRecords
# Named tuple - keywords from XML from mbus-serial-request-data
# See  mbus.py for details
Mbus_record = namedtuple("Mbus_record", mbus.mbustags)

# Defines combinations of fields which are of interest and should be extracted from XML <MBusData>
mbus_record = (
    Mbus_record('extra', None, None, None, None, None, None),
    Mbus_record('extra', None, None, None, None, None, None),
    Mbus_record('extra', None, None, None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Flow temperature.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Return temperature.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Temperature Difference.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Power.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Power.*',None,None,None,None),  # Same as above but used for delta value
    Mbus_record('Maximum value','0','Power.*',None,None,None,None),
    Mbus_record('Instantaneous value', '0', 'Volume flow.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Volume flow.*', None, None, None, None),
    Mbus_record('Maximum value', '0', 'Volume flow.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Energy.*', None, None, None, None),
    Mbus_record('Instantaneous value', '0', 'Energy.*', None, None, None, None),
)

# Defines which data from each DataRecord should be delivered. Same order as each DataRecord in mbus_record
# delta: u'\u0394'
Display_format = namedtuple(
    "Display", ['Genre', 'Text', 'Type', 'Unit', 'Function', 'Parameter','Visible'])
display_format = (
    Display_format('extra', 'Date', 'str', 'Local', None, None,True),
    Display_format('extra', 'Time', 'str', 'Local', None, None,True),
    Display_format('extra', 'Device', 'str','Device', None, None,True),
    Display_format('Value', 'Flow temp', 'float', '\xb0C', 'divide', 100,True),
    Display_format('Value', 'Return temp', 'float', '\xb0C', 'divide', 100,True),
    Display_format('Value', 'Temp diff', 'float', '\xb0C', 'divide', 100,True),
    Display_format('Value', 'Power', 'int', 'W', 'multiply', 100,True),
    Display_format('Delta', '\u0394Power', 'int','W','multiply',100,True),
    Display_format('Value', 'Max Power', 'int','W','multiply',100,False),
    Display_format('Value', 'Vol flow', 'float', 'm^3', 'divide', 1000,True),
    Display_format('Delta', '\u0394Vol flow', 'float','m^3','divide',1000,True),
    Display_format('Value', 'Max Vol flow', 'float', 'm^3', 'divide', 1000,True),
    Display_format('Value', 'Energy', 'int', 'KWh', None, None,True),
    Display_format('Delta', '\u0394Energy', 'int', 'KWh', None, None,True),
)
# Array of dictionaries


def init(tty, baudrate):
    locale.setlocale(locale.LC_ALL, 'da_DK.UTF-8') # For creating , as decimal point in float in CSV-file
    mbus.init(tty, baudrate)


async def open(address, device_name):
    """Creat device-descriptor to M-Bus device. Needed for further access such as read()."""
    devdesc = mbus.open(address)
    devdesc.update(
        {
            'device_name': device_name,
            'csvfile': None
        }
    )
    devdesc['csvfile'] = None
    await clear_delta(devdesc)
    return(devdesc)

def parse_json(devdesc, mbus_data):
    return(mbus.parse_json(devdesc,mbus_data))

def parse(devdesc, root):
    data = mbus.parse(devdesc, root, mbus_record, display_format)
    return data

async def read(devdesc):
    """ 
    Read and parses data from mbus device on open M-Bus device described in devdesc..

    On succes returns prepared array of arrays - each inner array a datapoint as described in devicespecific display_format
    descriptor. Example of successfull return:

     [["Date", "str", "24/06/2024", "Date"], ["Time", "str", "04:52:01", "Time"], ["Device", "str"], ["Flow temp", "float", 22.92, "\u00b0C"]]

    On error returns None

    """

    root = await mbus.read(devdesc)
    if root == None:
        return (None)
    slave = mbus.slave_information(devdesc,root)
    if slave['Manufacturer'] == 'KAM':
        if slave['Version'] == '53':  # Multical 603
            data = parse(devdesc, root)
            csvdata=''
            for i in data:
                if i[1] == 'float':
                    csvdata=csvdata + locale.format_string('%.2f',i[2]) + ';'
                else:
                    csvdata=csvdata + "{};".format(i[2])
            csvdata=csvdata.rstrip(';') # Remove trailing ';'
            await csvlog.write(devdesc['csvfile'],csvdata)
            return (data)
    return (None)


async def read_raw(devdesc):
    root = await mbus.read_raw(devdesc)
    return (root)


def headline():
    headline = []
    for row in display_format:
        if row.Unit == False:
            unittxt = row.Text  # Without Unit in ()
        else:
            unittxt = row.Text + "(" + row.Unit + ")"  # With Unit in ()
        unitlen = len(unittxt) + 2
        headline.append([unittxt, unitlen])  # Unit
    return (headline)


async def clear_delta(devdesc):
    devdesc['delta'] = {}
    if devdesc['csvfile'] != None:
        await csvlog.close(devdesc['csvfile'])
    # Create and open new csvlog file for device
    csvfilename=easyyaml.get('mbus','csvdir') + devdesc['device_name'] + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
    devdesc['csvfile']=await csvlog.open(csvfilename)
    csvheadline=''
    for i in headline():
        csvheadline=csvheadline + "{};".format(i[0])
    csvheadline=csvheadline.rstrip(';') # Remove trailing ';'
    await csvlog.write(devdesc['csvfile'],str(csvheadline))
