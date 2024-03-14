#!/usr/bin/env -S python3 -BO

from threading import Thread
from sys import argv
from os import fork
from os.path import exists

from core import record
from cli import clifunc
from cli import cli_run


def main(mem):
    is_child = not bool(fork()) if mem["background"] else True
    if not is_child:
        print("[bpsrec] bpsrec is running in the background.")
        exit()
    if mem["verbose"]:
        print(mem)
    try:
        threads = []
        for monitor, dump in zip(mem["monitors"], mem["dumps"]):
            args = (monitor, dump, mem["delay"], mem["lifetime"])
            threads.append(Thread(target=record, args=args, daemon=True))
            thread.start()
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass
    for dump in mem["dumps"]:
        print(f"[bpsrec] Gracefully exited. Dump file '{dump}' generated.")
    exit()


@clifunc
def bpsrec_monitor(call, args, mem):
    path = str(call)
    if not exists(path):
        print(f"[bpsrec] Couldn't find {path}. Skipping to next file.")
        return
    mem["monitors"].append(path)
    if len(mem["monitors"]) == len(mem["dumps"]) + 1:
        mem["dumps"].append(path + '.bpsrec')


@clifunc
def bpsrec_dump(call, args, mem):
    try:
        if mem["dumps"]:
            mem["dumps"].pop(-1)
        mem["dumps"].append(str(next(args)))
    except (StopIteration, ValueError):
        print("[bpsrec] The dump option expects a path.")
        exit()

bpsrec_dump.bindings += ['-o', '--output']


@clifunc
def bpsrec_delay(call, args, mem):
    try:
        mem["delay"] = float(next(args))
    except (StopIteration, ValueError):
        print("[bpsrec] The delay options expects a numeric.")
        exit()

bpsrec_delay.bindings += ['-d', '--delay']


@clifunc
def bpsrec_lifetime(call, args, mem):
    try:
        mem["lifetime"] = float(next(args))
    except (StopIteration, ValueError):
        print("[bpsrec] The lifetime options expects a numeric.")
        exit()

bpsrec_lifetime.bindings += ['-D', '--duration']


@clifunc
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

bpsrec_background.bindings += ['-B', '--background']


@clifunc
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

bpsrec_test.bindings += ['--test']


@clifunc
def bpsrec_verbose(call, args, mem):
    mem["verbose"] = True

bpsrec_verbose.bindings += ['-v', '--verbose']


if __name__ != "__main__":
    raise ImportError("This file cannot be imported as a python module.")

memory = cli_run(
    name="bpsrec",
    args=iter(argv[1:]),
    fallback=bpsrec_monitor,
    memory={"monitors": [], "dumps": [], "delay": 60, "lifetime": -1,
            "background": False, "verbose": False},
    clifuncs=[bpsrec_dump, bpsrec_delay, bpsrec_lifetime, bpsrec_background,
              bpsrec_test, bpsrec_verbose])

main(memory)
