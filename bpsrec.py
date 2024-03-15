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


FILE = "FILE"
MESSAGE_BACKGROUND_RUN = "[bpsrec] bpsrec is running in the background."
QUERY_PREVIOUS_SESSION = "[bpsrec] Previous session deteced. Want to continue? [Y/n] "
QUERY_CONTINUE_LATER = "[bpsrec] Do you want to continue later? [Y/n] "
QUERY_TEST_MODE = "[bpsrec] Enter test mode? This will last 15 seconds. [y/N] "
MESSAGE_GRACEFUL_EXIT = f"[bpsrec] Gracefully exited. Dump file '{FILE}' generated."
MESSAGE_LOST_FILE = f"[bpsrec] Couldn't find '{FILE}'. Skipping to next file."
MESSAGE_DUMP_MISSING_PATH = "[bpsrec] The dump option expects a path."
MESSAGE_DELAY_BAD_TYPE = "[bpsrec] The delay options expects a numeric."
MESSAGE_LIFETIME_BAD_TYPE = "[bpsrec] The lifetime options expects a numeric."
MESSAGE_BACKGROUND_LIFETIME = "[bpsrec] The background option expects a numeric. Or previously specified non-negative lifetime."

TOOLTIP_MONITOR = ""
TOOLTIP_DUMP = "Specify the dump path for the earliest undefined monitor."
TOOLTIP_DELAY = "Specify the temporale delay inbetween samplings in seconds."
TOOLTIP_LIFETIME = "Specify the lifetime of the program in seconds."
TOOLTIP_BACKGROUND = "Launch the program as a brackground process for a set time."
TOOLTIP_TEST = "This option is for development. Test out the program for 15 seconds, edit the generated 'monitor.test' file."
TOOLTIP_VERBOSE = "This option is for development. Get program memory dump."

BINDINGS_MONITOR = []
BINDINGS_DUMP = ['-o', '--output']
BINDINGS_DELAY = ['-d', '--delay']
BINDINGS_LIFETIME = ['-D', '--duration']
BINDINGS_BACKGROUND = ['-B', '--background']
BINDINGS_TEST = ['--test']
BINDINGS_VERBOSE = ['-v', '--verbose']

MONITORS = "monitors"
DUMPS = "dumps"
DELAY = "delay"
LIFETIME = "lifetime"
BACKGROUND = "background"
VERBOSE = "verbose"

SAVEFILE = ".bpsrec.save"
GENERIC_DUMP_EXTENSION = ".bpsrec"


def main():

    args = iter(argv[1:])
    fallback = bpsrec_monitor
    memory={MONITORS: [], DUMPS: [], DELAY: 60, LIFETIME: -1,
            BACKGROUND: False, VERBOSE: False}
    clifuncs=[bpsrec_dump, bpsrec_delay, bpsrec_lifetime, bpsrec_background,
              bpsrec_test, bpsrec_verbose]

    continuing = False
    if exists(SAVEFILE):
        continuing = not input(QUERY_PREVIOUS_SESSION) in {'n', 'N'}
        if continuing:
            memory = pload(open(SAVEFILE, 'rb'))
            
    if not continuing:
        memory = cli_run(args, memory, fallback, clifuncs)

    is_child = not bool(fork()) if memory[BACKGROUND] else True
    if not is_child:
        print(MESSAGE_BACKGROUND_RUN)
        exit()

    if memory[VERBOSE]:
        print(memory)

    try:
        threads = []
        for monitor, dump in zip(memory[MONITORS], memory[DUMPS]):
            args = (monitor, dump, memory[DELAY], memory[LIFETIME])
            thread = Thread(target=record, args=args, daemon=True)
            threads.append(thread)
            thread.start()
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass

    if not input(QUERY_CONTINUE_LATER) in {'n', 'N'}:
        pdump(memory, open(SAVEFILE, 'wb'))

    for dump in memory[DUMPS]:
        print(MESSAGE_GRACEFUL_EXIT.replace(FILE, dump))
    exit()


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

@clifunc(TOOLTIP_LIFETIME, BINDINGS_LIFETIME)
def bpsrec_lifetime(call, args, mem):
    try:
        mem[LIFETIME] = float(next(args))
    except (StopIteration, ValueError):
        print(MESSAGE_LIFETIME_BAD_TYPE)

        exit()

@clifunc(TOOLTIP_BACKGROUND, BINDINGS_BACKGROUND)
def bpsrec_background(call, args, mem):
    mem[BACKGROUND] = True
    try:
        mem[LIFETIME] = float(next(args))
    except (StopIteration, ValueError):
        if mem[LIFETIME] >= 0:
            return
        else:
            print(MESSAGE_BACKGROUND_LIFETIME)
            exit()

@clifunc(TOOLTIP_TEST, BINDINGS_TEST)
def bpsrec_test(call, args, mem):
    if input(QUERY_TEST_MODE) in {"y", "Y"}:
        return
    mem[BACKGROUND] = False
    mem[MONITORS].append("monitor.test")
    mem[DUMPS].append("dump.test")
    mem[DELAY] = 1
    mem[LIFETIME] = 15
    file = open('monitor.test', 'w')
    file.close()

@clifunc(TOOLTIP_VERBOSE, BINDINGS_VERBOSE)
def bpsrec_verbose(call, args, mem):
    mem[VERBOSE] = True


main()  # Used for forward declaration
