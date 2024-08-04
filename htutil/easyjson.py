import json
# Serialize python object to byte coded json string
def ser(object):
    json_string = json.dumps(object)
    return (json_string.encode())

# Deserialize byte coded json string to object
def deser(json_string):
    object = json_string.decode()
    return (json.loads(object))


# Create json dictionary from mbusbed.py nats message
# to message compatible with THongsBoard gateway message
def parse(device_name, mbus_data_byte):
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

