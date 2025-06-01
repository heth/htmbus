import netifaces

interface='eth0'
ipv4=2          # netifaces index for ipv4

def get_ipv4(iface):
    interface_list = netifaces.interfaces()

    for i in interface_list:
        if iface == i:
            try:
                addresses=netifaces.ifaddresses(iface)
            except Exception as e:
                print("ERROR: Retriveing IP address on {} {}".format(iface,e))

            if ipv4 in addresses:
                return(addresses[ipv4][0]['addr'])
            else:
                return("No IPv4 address")
