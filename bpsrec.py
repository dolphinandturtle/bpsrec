#!/usr/bin/env -S python3 -BO

from threading import Thread
from sys import argv
from os import fork
from os.path import exists

from core import record
from cli import clifunc
from cli import cli_run
from cli import bpsrec_monitor
from cli import bpsrec_dump
from cli import bpsrec_delay
from cli import bpsrec_lifetime
from cli import bpsrec_background
from cli import bpsrec_test
from cli import bpsrec_verbose


if __name__ != "__main__":
    raise ImportError("This file cannot be imported as a python module.")


def main(mem):
    threads = []
    for monitor, dump in zip(mem["monitors"], mem["dumps"]):
        args = (monitor, dump, mem["delay"], mem["lifetime"])
        threads.append(Thread(target=record, args=args, daemon=True))
    is_child = not bool(fork()) if mem["background"] else True
    if not is_child:
        print("[bpsrec] bpsrec is running in the background.")
        exit()
    if mem["verbose"]:
        print(mem)
    try:
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass
    for dump in mem["dumps"]:
        print(f"[bpsrec] Gracefully exited. Dump file '{dump}' generated.")
    exit()


memory = {"monitors": [],
          "dumps": [],
          "delay": 60,
          "lifetime": -1,
          "background": False,
          "verbose": False}

clifuncs = (bpsrec_dump, bpsrec_delay, bpsrec_lifetime, bpsrec_background,
            bpsrec_test, bpsrec_verbose)

cli_run("bpsrec", iter(argv[1:]), memory, bpsrec_monitor, main, *clifuncs)
