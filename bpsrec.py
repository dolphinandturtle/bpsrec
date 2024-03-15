#!/usr/bin/env -S python3 -BO

from threading import Thread
from sys import argv
from os import fork
from os.path import exists
from pickle import dump as pdump
from pickle import load as pload

from core import record
from cli import clifunc
from cli import cli_run


if __name__ != "__main__":
    raise ImportError("This file cannot be imported as a python module.")


def main():

    args = iter(argv[1:])
    fallback = bpsrec_monitor
    memory={"monitors": [], "dumps": [], "delay": 60, "lifetime": -1,
            "background": False, "verbose": False}
    clifuncs=[bpsrec_dump, bpsrec_delay, bpsrec_lifetime, bpsrec_background,
              bpsrec_test, bpsrec_verbose]

    continuing = False
    if exists(".bpsrec.save"):
        continuing = not input("[bpsrec] Previous session deteced. "
                               "Want to continue? [Y/n]") in {'n', 'N'}
        if continuing:
            memory = pload(open(".bpsrec.save", 'rb'))
            
    if not continuing:
        memory = cli_run(args, memory, fallback, clifuncs)

    is_child = not bool(fork()) if memory["background"] else True
    if not is_child:
        print("[bpsrec] bpsrec is running in the background.")
        exit()

    if memory["verbose"]:
        print(memory)

    try:
        threads = []
        for monitor, dump in zip(memory["monitors"], memory["dumps"]):
            args = (monitor, dump, memory["delay"], memory["lifetime"])
            thread = Thread(target=record, args=args, daemon=True)
            threads.append(thread)
            thread.start()
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass

    if not input("[bpsrec] Do you want to continue later? [Y/n] ") in {'n', 'N'}:
        pdump(memory, open(".bpsrec.save", 'wb'))

    for dump in memory["dumps"]:
        print(f"[bpsrec] Gracefully exited. Dump file '{dump}' generated.")
    exit()


@clifunc(tooltip="", bindings=[])
def bpsrec_monitor(call, args, mem):
    path = str(call)
    if not exists(path):
        print(f"[bpsrec] Couldn't find {path}. Skipping to next file.")
        return
    mem["monitors"].append(path)
    if len(mem["monitors"]) == len(mem["dumps"]) + 1:
        mem["dumps"].append(path + '.bpsrec')


@clifunc(tooltip="", bindings=['-o', '--output'])
def bpsrec_dump(call, args, mem):
    try:
        if mem["dumps"]:
            mem["dumps"].pop(-1)
        mem["dumps"].append(str(next(args)))
    except (StopIteration, ValueError):
        print("[bpsrec] The dump option expects a path.")
        exit()


@clifunc(tooltip="", bindings=['-d', '--delay'])
def bpsrec_delay(call, args, mem):
    try:
        mem["delay"] = float(next(args))
    except (StopIteration, ValueError):
        print("[bpsrec] The delay options expects a numeric.")
        exit()


@clifunc(tooltip="", bindings=['-D', '--duration'])
def bpsrec_lifetime(call, args, mem):
    try:
        mem["lifetime"] = float(next(args))
    except (StopIteration, ValueError):
        print("[bpsrec] The lifetime options expects a numeric.")
        exit()


@clifunc(tooltip="", bindings=['-B', '--background'])
def bpsrec_background(call, args, mem):
    mem["background"] = True
    try:
        mem["lifetime"] = float(next(args))
    except (StopIteration, ValueError):
        if mem["lifetime"] >= 0:
            return
        else:
            print("[bpsrec] The background option expects a numeric.",
                  "Or previously specified non-negative lifetime.")
            exit()


@clifunc(tooltip="", bindings=['--test'])
def bpsrec_test(call, args, mem):
    if input("[bpsrec] Enter test mode?",
             "This will last 15 seconds. [y/N] ") in ["y", "Y"]:
        return
    mem["background"] = False
    mem["monitors"].append("monitor.test")
    mem["dumps"].append("dump.test")
    mem["delay"] = 1
    mem["life"] = 15
    file = open('monitor.test', 'w')
    file.close()


@clifunc(tooltip="", bindings=['-v', '--verbose'])
def bpsrec_verbose(call, args, mem):
    mem["verbose"] = True


main()  # Used for forward declaration
