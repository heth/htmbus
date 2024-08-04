#!/usr/bin/python3
import subprocess
import xml.etree.ElementTree as ET
import re
import time
import asyncio
import json
from datetime import timezone
from datetime import datetime
from htutil import log
from htutil import easyyaml

# Servicefunctions for translating values. Fx from W to KW
def divide(value, divisor):
    return value / divisor


def multiply(value, multiplier):
    return value * multiplier


def ts2time(ts):
    return (datetime.utcfromtimestamp(ts).strftime('%D/%M%Y %H:%M:%S'))


function = {
    'divide':   divide,
    'multiply': multiply,
    'int': int,
    'float': float,
    'str': str,
    'ts2time': ts2time
}

# Initialize


def init(ttyline="/dev/ttyS4", baudrate=9600):
    "Initilizes mbus system on given tty and baudrate"
    global tty
    global baud
    tty = ttyline
    baud = baudrate
    if ttyline == "/dev/ttyS4":
        sub = subprocess.run(["config-pin", "P9_11", "uart"],
                             shell=False, capture_output=True)
        sub = subprocess.run(["config-pin", "P9_13", "uart"],
                             shell=False, capture_output=True)


def open(address):
    """ open devdesc - device desciptor - for M-Bus device at M-Bus address 

        devdesc is a dictionary needed for further access to device 
    """
    devdesc = {
        'address': str(address),
        'timestamp': None,       # Last succesfull read
        'count':  0,             # Number of successfull reads
        'error':  0              # Number of failed reads
    }
    return (devdesc)


async def read_raw(devdesc):
    "Reads and returns raw XML data from mbus device on given address"
    args = ["-b", str(baud), tty, devdesc['address']]
    process = await asyncio.create_subprocess_exec("mbus-serial-request-data", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if len(stdout) == 0:
        log.warn("read_raw() from M-Bus address {} failed.".format(devdesc['address']))
        devdesc['error'] = devdesc['error'] + 1
        return None
    devdesc['timestamp'] = int(time.time())
    devdesc['count'] = devdesc['count'] + 1
    return stdout


async def read(devdesc):
    """
    Read and converts XML data from mbus device on open M-Bus device described in devdesc.

    On succes returns xml.etree.ElementTree 
    On error returns None

    """

    rawdata = await read_raw(devdesc)
    if rawdata == None:
        return None
    root = ET.fromstring(rawdata)
    return root

def slave_information(devdesc, root):
    slavedict = {}
    for i in root.findall('./SlaveInformation/'):
        slavedict[i.tag] = i.text
    devdesc['manufacturer']=slavedict['Manufacturer']
    devdesc['version']=slavedict['Version']
    devdesc['name']=slavedict['ProductName']

    return slavedict


def parse_extra(devdesc, format_row):
    row = [format_row.Text, format_row.Type]  # label and datatype
    match format_row.Unit:
        case 'timestamp':
            row.append(devdesc['timestamp'])
            row.append('sec')  # Seconds
        case 'UTC':
            utctime = datetime.utcfromtimestamp(devdesc['timestamp'])
            match format_row.Text:
                case 'Date':
                    row.append(utctime.strftime("%d/%m/%Y"))
                    row.append('UTC date')  # unit
                case 'Time':
                    row.append(utctime.strftime("%H:%M:%S"))
                    row.append('UTC time')  # unit
        case 'Local':
            localtime = datetime.fromtimestamp(devdesc['timestamp'])
            match format_row.Text:
                case 'Date':
                    row.append(localtime.strftime("%d/%m/%Y"))
                    row.append('Date')  # unit
                case 'Time':
                    row.append(localtime.strftime("%H:%M:%S"))
                    row.append('Time')  # unit
        case 'Device':
            row.append(devdesc['device_name'])
            row.append('Name')  # unit
    return (row)


def parse_delta(deltainfo, recorddata):
    return ('parse_delta')


# Tags searched in each DataRecord in this order.
#  Tags are keywords from XML output of mbus-serial-request-data command.
#  See kam603.xml for example
mbustags = ('Function', 'StorageNumber', 'Unit',
            'Value', 'Timestamp', 'Device', 'Tariff')
# Typeinfo is the devicespecific info - fx. kam603info containing

def parse_json(devdesc, mbus_data):
    mbus_dict={}
    for entry in mbus_data:
        mbus_dict[entry[0]]=entry[2]
    json_data=json.dumps(mbus_dict)
    mb2={}
    mb2[devdesc['device_name']]=mbus_dict
    jd2=json.dumps(mb2)
    return(json_data)
  
def parse_match(entry, mbus_record):
    # fi = field index
    try:
        for fi in range(len(mbus_record)):

           if mbus_record[fi] == None:
               continue # Field do not matter

           if not re.search(mbus_record[fi],  entry[fi].text):
               return(False)    # entry do not match
        return(True) # entry match mbus_record
    except:
        log.error("ERROR: parse_match: entry: {} mbus_record: {}".format(entry,mbus_record))
        return(False)

energy=0 # LEG
def parse(devdesc, in_data, mbus_records, display_format):
    """
        Parse M-bus device information from.............................

        There are four data sets involved in parsing:
        1: devdesc - consists of collected information on each M-Bus device
        2: in_data - latest raw information read from device
        3: mbus_records - template for locating selectet data from root 
        4: display_format - How selected data located with mbus_records
           should be presented
    """
    out_data=[] # Collect parsed data entries here
# --> LEG
    global energy
    energy=energy + 1
# <-- LEG

    # ri = record index
    for ri in range(len(mbus_records)):
        out_data.append(['-', None, None, '']) # Empty out_data row to be filled in later
        # Dont waste time on 'extra' mbus_records

        if mbus_records[ri].Function == 'extra':
           out_data[ri] = parse_extra(devdesc,display_format[ri])
           continue
        
        for entry in in_data:

            # Only interested in DataRecords from M-Bus device
            if entry.tag != 'DataRecord':
                continue

            if parse_match(entry, mbus_records[ri]) == True:
                out_data[ri][0] = display_format[ri].Text
                out_data[ri][1] = display_format[ri].Type



# --> LEG
                #print("0: {} 1:{}".format(out_data[ri][0],out_data[ri][1]))
                if re.search("Energy", out_data[ri][0]):
                    entry[3].text = int(energy)
# <-- LEG



                if display_format[ri].Function != None:
                    out_data[ri][2] = \
                        function[display_format[ri].Type](function[display_format[ri].Function](int(entry[3].text), 
                        display_format[ri].Parameter))
                else:
                    out_data[ri][2]=function[display_format[ri].Type](entry[3].text)
                if display_format[ri].Genre == 'Delta':

                    # If first time - store initial value from first set of data from M-Bus device
                    if not display_format[ri].Text in devdesc['delta']:
                        devdesc['delta'][display_format[ri].Text] = out_data[ri][2]

                    # Calculate delta value from stored initial value
                    out_data[ri][2] = out_data[ri][2] - devdesc['delta'][display_format[ri].Text]

    return(out_data)
