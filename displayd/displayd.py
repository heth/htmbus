import display as dsp
import time
import signal
import sdnotify         # Systemd notify - communicate with systemd service
import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from htutil import easyyaml

yamlfile="/etc/mbus/mbus.yaml"

def signal_handler(sig):
    dsp.dsp_clock_stop()
    dsp.dsp_clear()
    dsp.dsp_writeyx(1,1, f"Caught signal: {sig}")
    dsp.dsp_writeyx(2,1,"Stopping.......")
    systemd.notify("STOPPING=1")
    for i in reversed(range(1,6)):
        time.sleep(0.5)
        dsp.dsp_writeyx(2,16,f"{i:1}")

    time.sleep(0.5)
    dsp.dsp_clock_stop()
    dsp.nats_stop()  # Error calling async method from sync method
    exit()

async def main():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT,signal_handler,signal.SIGINT)
    loop.add_signal_handler(signal.SIGTERM,signal_handler,signal.SIGTERM)
    loop.add_signal_handler(signal.SIGQUIT,signal_handler,signal.SIGQUIT)
    easyyaml.init(yamlfile)
    dsp.dsp_init()
    dsp.dsp_clock_start(1,16)
    await dsp.nats_start(easyyaml.get('display','displaytopic'))

    global systemd
    systemd = sdnotify.SystemdNotifier()
    systemd.notify("READY=1")

    while True:
        await asyncio.sleep(1000)

if __name__ == '__main__':
    asyncio.run(main())
