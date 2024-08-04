import sys
import syslog as sl
from htutil import easyyaml



sevLevel=['Emergency',"Alert","Critical","Error","Warning","Notice","Informational","Debug"]
sevLevelAbr=['EMERG',"ALERT","CRIT","ERR","WARN","NOTICE","INFO","DEBUG"]

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# init()
#   1: Use default values or:
#   2: Set values in yml file with ymlfile="YOUR_YML_FILE" in imit() call
#   3: Set level, syslog, tty, file and filename in init() call
#   4: A combination of the above (yml-file values  overwrites manually set values)
setup={}
def init(yamlfile='',level=sl.LOG_ERR,syslog=False,tty=True,file=False,filename=''):
    #setup['yamlfile'] = yamlfile
    setup["level"]=level
    setup["syslog"]=syslog
    setup["tty"]=tty
    setup["file"]=file
    setup["filename"]=filename
   
    if yamlfile != '':
        easyyaml.init(yamlfile)
        yamltags=['level','syslog','tty','file','filename']

        for tag in yamltags:
         if easyyaml.get('log',tag) != None:
             setup[tag] = easyyaml.get('log',tag)
         else:
             # Spoky way of using "pointer" - but fun making :-)
             exec(tag + (" = {}".format(tag)))
             setup[tag] = tag

    if setup['file'] == True:
        if setup['filename'] == '':
            warn("init(): Filename not set")
        #try:
        #open file
        # setup[filehandle] = open...
def log(severity,message):
    if severity > setup['level']:
        return
    if setup['syslog'] == True:
        sl.syslog(severity,message)
    if setup['tty'] == True:
        eprint("{}: {}".format(sevLevelAbr[severity],message))

def error(message):
    log(sl.LOG_ERR,message)

def warn(message):
    log(sl.LOG_WARNING,message)

def info(message):
    log(sl.LOG_INFO,message)

def debug(message):
    log(sl.LOG_DEBUG,message)

