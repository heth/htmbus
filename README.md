# htmbus
htmbus is the measuring and visualization of a project for an energy measurement system using a heat exchanger. The scope of the project will be described later.

- htmbus consists of several wired M-Bus [Meter-Bus](https://m-bus.com/) devices.
- A [BeagleBone Black](https://www.beagleboard.org/boards/beaglebone-black) as gateway between M-Bus and Ethernet - running this htmbus software (And a little extra hardware - described elsewhere)
  - For the low level M-Bus protocol conversion _htmbus_ use [rscada/libmbus](https://github.com/rscada/libmbus)
- A [Intel NUC13ANHI3000](https://www.intel.com/content/dam/support/us/en/documents/intel-nuc/NUC13AN_TechProdSpec.pdf) running [ThingsBoard](https://thingsboard.io/)
## Physical topology view
![Physical topology view of project](/docs/pics/htmbus_topology.png)

## Logical topology view
![Logical topology view](/docs/pics/htmbus%20logical%20topology.png)

## Hardware installation
See: [Harware installation](https://mars.merhot.dk/w/index.php/M-bus_Linux#Hardware_configuration)
## Software installation
### Installaing new debian image on micro-SD card
1. Remove micro-SD card (If any)
2. Boot from buildin image on on-board flash (mmcblk1)
3. insert micro-SD card (Minimum 8 GB) 
4. Run: sudo bash
5. Run: wget -qO- https://files.beagle.cc/file/beagleboard-public-2021/images/am335x-debian-12.2-iot-armhf-2023-10-07-4gb.img.xz | xzcat | dd bs=10M of=/dev/mmcblk0 status=progress
6. Run: shutdown -r 0
7. login after boot and check boot device is mmcblk0p1 - run: df -h
### Install htmbus and necesary software
1. login as debian - or another added user with a home directory
2. run: git clone https://github.com/heth/htmbus.git
3. run: cd htmbus
4. run: sudo ./install-stage1
5. run: sudo ./install-stage2
6. run: sudo shutdown -r 0
7. login as same user again
8. run: cd htmbus
9. run: sudo ./install-stage3
10. If everything works - check all four daemons running with: systemctl | grep -P "display|mbus"
## htmbus configuration
Most used configuration variables are in mbus.yaml (Installed in /etc/mbus/ directory on running system)



