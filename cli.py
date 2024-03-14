from functools import wraps
from typing import Callable, Dict, Any


CliFunc = Callable[[str, iter, Dict[str, Any]], None]

def clifunc(func):
    @wraps(func)
    def wrapper(call, args, memory):
        return func(call, args, memory)
    wrapper.tooltip = "This function hasn't been documented yet."
    wrapper.bindings = []
    return wrapper


def cli_run(name: str, args: iter, memory: Dict[str, Any], fallback: CliFunc,
            main: Callable, *clifuncs: CliFunc):
    info = '\n'.join([
        f"{index}.  ({', '.join(func.bindings)}) {func.tooltip}"
        for index, func in enumerate(clifuncs)])
    bindings = {bind: func for func in clifuncs for bind in func.bindings}
    arglen = 0
    try:
        while True:
            call = next(args)
            clifunc = bindings.get(call)
            if clifunc is not None:
                clifunc(call, args, memory)
            else:
                fallback(call, args, memory)
            arglen += 1
    except StopIteration:
        pass
    if not arglen:
        if input(f"[{name}] No arguments have been given. "
                 "Need help? [y/N] ") in {'y', 'Y'}:
            print(info)
        exit()
    main(memory)


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
