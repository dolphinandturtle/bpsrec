#!/usr/bin/env python3

from os import fork
from os.path import exists
from sys import argv
from time import sleep
from subprocess import check_output
from threading import Thread
from dataclasses import dataclass, field


# TODO: Move to rec.py file
def get_file_bits(path: str) -> int:
    raw = check_output(['du', '-b', path], encoding='utf8')
    return int(raw.split('\t')[0])

# TODO: Move to rec.py file
def record(monitor_path, dump_path, delay_seconds, lifetime):
    time = 0
    bits_i = get_file_bits(monitor_path)
    with open(dump_path, 'a') as dump:
        while True:
            bits_f = get_file_bits(monitor_path)
            bps = round((bits_f - bits_i) / delay_seconds, 2)
            bits_i = bits_f
            dump.write(str(round(time, 2)) + '\t' + str(bps) + '\n')
            dump.flush()
            time += delay_seconds
            sleep(delay_seconds)
            if (lifetime > 0 and lifetime - delay_seconds < 0):
                break
            lifetime -= delay_seconds


@dataclass(slots=True, frozen=True)
class InterpreterBindings:
    command_info: frozenset[str]
    dump_path: frozenset[str]
    delay_seconds: frozenset[str]
    lifetime: frozenset[str]
    background: frozenset[str]
    test: frozenset[str]
    verbose: frozenset[str]

@dataclass(slots=True)
class Options:
    monitor_paths: list[str] = field(default_factory=list)
    dump_paths: list[str] = field(default_factory=list)
    delay_seconds: float = 3.0
    lifetime: float = -1
    isbackground: bool = False
    isverbose: bool = False

def set_info(bindings):
    alias_info = ', '.join(list(bindings.command_info))
    alias_dump = ', '.join(list(bindings.dump_path))
    alias_delay = ', '.join(list(bindings.delay_seconds))
    alias_lifetime = ', '.join(list(bindings.lifetime))
    alias_background = ', '.join(list(bindings.background))
    alias_test = ', '.join(list(bindings.test))
    print("[bpsrec] Command list:"
          f"({alias_info}) The help/info option prints to stdout the programs",
          f"functioning.\n\n",
          f"({alias_dump}) This option allows you to 'set' a specific path for",
          f"dumping data measured.\n\n",
          f"({alias_delay}) This option allows you to 'set' a temporal delay",
          "in between data samplings.\n\n",
          f"({alias_lifetime}) This option allows you to 'set' a lifetime for",
          "the program(s).",
          f"NOTE: If the program parameters include ({alias_background}), then",
          "this option will be overwritten.\n\n",
          f"({alias_background}) This option sends all the program executions",
          "into the background for a 'set' amount of time.\n")
    exit()

def set_dump(arguments, options):
    try:
        if options.dump_paths:
            options.dump_paths.pop(-1)
        options.dump_paths.append(str(next(arguments)))
    except (StopIteration, ValueError):
        print("[bpsrec] The dump option expects a path.")
        exit()

def set_delay(arguments, options):
    try:
        options.delay_seconds = float(next(arguments))
    except (StopIteration, ValueError):
        print("[bpsrec] The delay options expects a numeric.")
        exit()

def set_lifetime(arguments, options):
    try:
        options.lifetime = float(next(arguments))
    except (StopIteration, ValueError):
        print("[bpsrec] The lifetime options expects a numeric.")
        exit()

def set_isbackground(arguments, options):
    options.isbackground = True
    try:
        options.lifetime = float(next(arguments))
    except (StopIteration, ValueError):
        if options.lifetime >= 0:
            return
        else:
            print("[bpsrec] The background option expects a numeric.",
                  "Or previously specified non-negative lifetime.")
            exit()

def set_istest(arguments, option):
    if input("[bpsrec] Enter test mode?",
             "This will last 15 seconds. [y/N] ") in ["y", "Y"]:
        return
    options.isbackground = False
    options.monitor_paths.append("monitor.test")
    options.dump_paths.append("dump.test")
    options.delay_seconds = 1
    options.lifetime = 15
    file = open('monitor.test', 'w')
    file.close()

def set_isverbose(arguments, options):
    options.isverbose = True

def set_monitor(call, options):
    path = str(call)
    if not exists(path):
        print(f"[bpsrec] Couldn't find {path}. Skipping to next file.")
        return
    options.monitor_paths.append(path)
    if len(options.monitor_paths) == len(options.dump_paths) + 1:
        options.dump_paths.append(path + '.bpsrec')

def get_options(bindings) -> Options:
    options = Options()
    arguments = iter(argv[1:])
    while True:
        try:
            call = next(arguments)
            # TODO: Turn this conditional to a switch statement (with dictionaries)
            if call in bindings.command_info:
                set_info(bindings)
            elif call in bindings.dump_path:
                set_dump(arguments, options)
            elif call in bindings.delay_seconds:
                set_delay(arguments, options)
            elif call in bindings.lifetime:
                set_lifetime(arguments, options)
            elif call in bindings.background:
                set_isbackground(arguments, options)
            elif call in bindings.test:
                set_istest(arguments, options)
            elif call in bindings.verbose:
                set_isverbose(arguments, options)
            else:
                set_monitor(call, options)
        except StopIteration:
            break

    if options.delay_seconds > options.lifetime and options.isbackground:
        print(f"[bpsrec] The lifetime specified ({options.lifetime}) must be",
              f"greater than the sampling interval ({options.delay_seconds})." ,
              "Exiting.")
        exit()

    if not options.monitor_paths:
        print("[bpsrec] No file to monitor has been given. Exiting.")
        exit()

    return options


def get_threads(options) -> list[Thread]:
    threads = []
    for monitor, dump in zip(options.monitor_paths, options.dump_paths):
        arguments = monitor, dump, options.delay_seconds, options.lifetime
        threads.append(Thread(target=record, args=arguments, daemon=True))
    return threads

def run(threads, options):
    is_child = not bool(fork()) if options.isbackground else True
    if not is_child:
        print("[bpsrec] bpsrec is running in the background.")
        exit()
    if options.isverbose:
        print(options)
    try:
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
    except KeyboardInterrupt:
        pass
    for monitor, dump in zip(options.monitor_paths, options.dump_paths):
        print(f"[bpsrec] Gracefully exited. Dump file '{dump}' generated.")
    exit()


if __name__ == "__main__":
    stdbingings = InterpreterBindings(
        command_info=frozenset(('-h', '-H', '--help')),
        dump_path=frozenset(('-o', '-o=', '--dump')),
        delay_seconds=frozenset(('-d', '-d=', '--delay')),
        lifetime=frozenset(('-t', '-t=', '--lifetime')),
        background=frozenset(('-b', '--background')),
        test=frozenset(('--test')),
        verbose=frozenset(('-v', '--verbose'))
    )
    options = get_options(stdbingings)
    threads = get_threads(options)
    run(threads, options)
