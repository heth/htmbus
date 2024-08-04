import asyncio
import aiofiles
from htutil import log

async def open(filename):
    try:
        fd=await aiofiles.open(filename,"w")
        return(fd)

    except:
        log.error("Could not create {} for writing.".format(filename))
        return(None)

async def write(fd,line):
    try:
        line=line + "\n"
        await fd.write(str(line))
        await fd.flush()
    except:
        log.error("Could not write.")

async def close(fd):
    try:
        await fd.close()
    except:
        log.error("Could not close file descriptor.")
        
