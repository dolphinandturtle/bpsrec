#!/usr/bin/env -S python3 -BO

from datetime import datetime
from threading import Thread
from sys import argv
from os import fork
from os.path import exists
from os import remove
from pickle import dump as pdump
from pickle import load as pload

from core import monitor_bytes_per_second
from cli import clifunc
from cli import cli_run


if __name__ != "__main__":
    raise ImportError("This file cannot be imported as a python module.")

today = datetime.now()

FILE = "FILE"
QUERY_PAUSE_SESSION = "[bpsrec] Do you want to pause this session for later? [Y/n] "
QUERY_CONTINUE_SESSION = "[bpsrec] Previous session deteced. Want to continue? [Y/n] "
QUERY_TEST_MODE = "[bpsrec] Enter test mode? This will last 15 seconds. [y/N] "
MESSAGE_GRACEFUL_EXIT = f"[bpsrec] Gracefully exited. Dump file '{FILE}' generated."
MESSAGE_LOST_FILE = f"[bpsrec] Couldn't find '{FILE}'. Skipping to next file."
MESSAGE_DUMP_MISSING_PATH = "[bpsrec] The dump option expects a path."
MESSAGE_DELAY_BAD_TYPE = "[bpsrec] The delay options expects a numeric."
MESSAGE_DURATION_BAD_TYPE = "[bpsrec] The duration options expects a numeric."

TOOLTIP_MONITOR = ""
TOOLTIP_DUMP = "Specify the dump path for the earliest undefined monitor."
TOOLTIP_DELAY = "Specify the temporale delay inbetween samplings in seconds."
TOOLTIP_DURATION = "Specify the duration of the program in seconds."
TOOLTIP_TEST = "This option is for development. Test out the program for 15 seconds, edit the generated 'monitor.test' file."
TOOLTIP_VERBOSE = "This option is for development. Get program memory dump."
TOOLTIP_SYNCHRONIZE = "Synchronize the recorded time with real-world time."

BINDINGS_MONITOR = []
BINDINGS_DUMP = ['-o', '--output']
BINDINGS_DELAY = ['-d', '--delay']
BINDINGS_DURATION = ['-D', '--duration']
BINDINGS_TEST = ['--test']
BINDINGS_VERBOSE = ['-v', '--verbose']
BINDINGS_SYNCHRONIZE = ['-s', '--synch', '--synchronize']

MONITORS = "monitors"
DUMPS = "dumps"
DELAY = "delay"
DURATION = "duration"
TIME = "time"
VERBOSE = "verbose"

SAVEFILE = ".bpsrec.save"
GENERIC_DUMP_EXTENSION = ".bpsrec"


def main():

    args = iter(argv[1:])
    fallback = bpsrec_monitor
    memory={MONITORS: [], DUMPS: [], DELAY: 60, DURATION: -1, TIME: 0,
            VERBOSE: False}
    clifuncs=[bpsrec_dump, bpsrec_delay, bpsrec_duration,
              bpsrec_test, bpsrec_verbose, bpsrec_synchronize]

    previous_session = False
    if exists(SAVEFILE):
        if input(QUERY_CONTINUE_SESSION) not in {'n', 'N'}:
            memory = pload(open(SAVEFILE, 'rb'))
            previous_session = True

    if not reload_memory(memory, SAVEFILE):
        memory = cli_run(args, memory, fallback, clifuncs)

    if memory[VERBOSE]:
        print(memory)

    try:
        threads = get_threads(memory)
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        if input(QUERY_PAUSE_SESSION) not in {'n', 'N'}:
            archive_memory(memory, SAVEFILE)
        elif exists(SAVEFILE):
            remove(SAVEFILE)
    for dump in memory[DUMPS]:
        print(MESSAGE_GRACEFUL_EXIT.replace(FILE, dump))
    exit()


def get_threads(memory) -> list[Thread]:
    threads = []
    target = monitor_bytes_per_second
    for monitor, dump in zip(memory[MONITORS], memory[DUMPS]):
        args = (monitor, dump, memory[DELAY], memory[DURATION], memory[TIME])
        threads.append(Thread(target=target, args=args, daemon=True))
    return threads

def reload_memory(memory, save) -> bool:
    if exists(save):
        if input(QUERY_CONTINUE_SESSION) not in {'n', 'N'}:
            memory = pload(open(save, 'rb'))
            return True
    else:
        return False

def archive_memory(memory, save) -> None:
    with open(memory[DUMPS][0], 'r') as dump:
        data = dump.read().split('\n')
        line = list(filter(lambda item: item, data))[-1]
        memory[TIME] = float(line.split('\t')[0]) + memory[DELAY]
    pdump(memory, open(save, 'wb'))


@clifunc(TOOLTIP_MONITOR, BINDINGS_MONITOR)
def bpsrec_monitor(call, args, mem):
    path = str(call)
    if not exists(path):
        print(MESSAGE_LOST_FILE.replace(FILE, path))
        return
    mem[MONITORS].append(path)
    if len(mem[MONITORS]) == len(mem[DUMPS]) + 1:
        mem[DUMPS].append(path + GENERIC_DUMP_EXTENSION)

@clifunc(TOOLTIP_DUMP, BINDINGS_DUMP)
def bpsrec_dump(call, args, mem):
    try:
        if mem[DUMPS]:
            mem[DUMPS].pop(-1)
        mem[DUMPS].append(str(next(args)))
    except (StopIteration, ValueError):
        print(MESSAGE_DUMP_MISSING_PATH)
        exit()

@clifunc(TOOLTIP_DELAY, BINDINGS_DELAY)
def bpsrec_delay(call, args, mem):
    try:
        mem[DELAY] = float(next(args))
    except (StopIteration, ValueError):
        print(MESSAGE_DELAY_BAD_TYPE)
        exit()

@clifunc(TOOLTIP_DURATION, BINDINGS_DURATION)
def bpsrec_duration(call, args, mem):
    try:
        mem[DURATION] = float(next(args))
    except (StopIteration, ValueError):
        print(MESSAGE_DURATION_BAD_TYPE)

        exit()

@clifunc(TOOLTIP_TEST, BINDINGS_TEST)
def bpsrec_test(call, args, mem):
    if input(QUERY_TEST_MODE) not in {"y", "Y"}:
        return
    mem[DURATION] = 15
    mem[MONITORS].append("monitor.test")
    mem[DUMPS].append("dump.test")
    file = open('monitor.test', 'w')
    file.close()

@clifunc(TOOLTIP_VERBOSE, BINDINGS_VERBOSE)
def bpsrec_verbose(call, args, mem):
    mem[VERBOSE] = True

@clifunc(TOOLTIP_SYNCHRONIZE, BINDINGS_SYNCHRONIZE)
def bpsrec_synchronize(call, args, mem):
    mem[TIME] = today.hour * 60**2 + today.minute * 60 + today.second


main()  # Used for forward declaration
