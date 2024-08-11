# htmbus
htmbus is the measuring and visualization of a project for an energy measurement system using a heat exchanger. The scope of the project will be described later.

- htmbus consists of several wired M-Bus [Meter-Bus](https://m-bus.com/) devices.
- A [BeagleBone Black](https://www.beagleboard.org/boards/beaglebone-black) as gateway between M-Bus and Ethernet - running this htmbus software (And a little extra hardware - described elsewhere)
- A [Intel NUC13ANHI3000](https://www.intel.com/content/dam/support/us/en/documents/intel-nuc/NUC13AN_TechProdSpec.pdf) running [ThingsBoard](https://thingsboard.io/)
## Physical topology view
![Physical topology view of project](/docs/pics/htmbus_topology.png)

## Logical topology view
![Logical topology view[/docs/pics/htmbus%20logical%20topology.png]

PREREQUISITES:
==============

-libmbus
 Either clone from https://github.com/rscada/libmbus and install it
  or
 Download source or package from http://www.rscada.se/libmbus and install it


 -python3.11



 REMEMBER:
 =========

 When updating:
  - pip freeze > requirements.txt
  - check git status



