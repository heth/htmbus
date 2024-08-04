import yaml
from htutil import log

#yamlfd={}

def init(filename):
    global yamlfd
    try:
        with open(filename) as file:
            yamlfd = yaml.safe_load(file)
            return(yamlfd)
    except (yaml.YAMLError,OSError,IOError) as e:
        log.error("YAML error: {}".format(e))
        exit()   

def get(section,item,subitem=None):
    for sec in yamlfd:
        if sec == section:
            for it in yamlfd[sec]:
                if it == item:
                    return(yamlfd[section][item])
    return(None)


# Work in progress :-)
def get2(*args):
    par=[]
    for i in args:
        par.append(i)
        
