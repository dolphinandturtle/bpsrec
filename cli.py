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
            clifuncs: list[CliFunc]):
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
    return memory
