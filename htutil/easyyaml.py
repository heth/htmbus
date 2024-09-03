import yaml
from htutil import log

#yamlfd={}

def init(filename):
    global yamldict
    try:
        with open(filename) as file:
            yamldict = yaml.safe_load(file)
            file.close()
            return(yamldict)
    except (yaml.YAMLError,OSError,IOError) as e:
        log.error("YAML error: {}".format(e))
        exit()   

def get(section,item,subitem=None):
    for sec in yamldict:
        if sec == section:
            for it in yamldict[sec]:
                if it == item:
                    return(yamldict[section][item])
    return(None)


# Work in progress :-)
def get2(*args):
    par=[]
    for i in args:
        par.append(i)
        
