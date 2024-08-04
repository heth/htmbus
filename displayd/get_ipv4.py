import netifaces

interface='eth0'
ipv4=2          # netifaces index for ipv4

def get_ipv4(iface):
    interface_list = netifaces.interfaces()

    for i in interface_list:
        if iface == i:
            addresses=netifaces.ifaddresses(iface)
            if ipv4 in addresses:
                return(addresses[ipv4][0]['addr'])
            else:
                return("No IPv4 address")
