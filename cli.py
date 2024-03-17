from functools import wraps
from typing import Callable, Dict, Any

QUERY_NO_ARGUMENTS_HELP = "No arguments have been given. Need help? [y/N] "


CliFunc = Callable[[str, iter, Dict[str, Any]], None]

def clifunc(tooltip, bindings):
    def _clifunc(func):
        @wraps(func)
        def wrapper(call, args, memory):
            return func(call, args, memory)
        wrapper.tooltip = tooltip
        wrapper.bindings = bindings
        return wrapper
    return _clifunc


def get_info(clifuncs: list[CliFunc]):
    return '\n'.join([
        f"{index}.  ({', '.join(func.bindings)}) {func.tooltip}"
        for index, func in enumerate(clifuncs)])


def get_global_bindings(clifuncs: list[CliFunc]):
    return {bind: func for func in clifuncs for bind in func.bindings}


def cli_run(args: iter, memory: Dict[str, Any], fallback: CliFunc,
            clifuncs: list[CliFunc]):
    arglen = 0
    bindings = get_global_bindings(clifuncs)
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
        if input(QUERY_NO_ARGUMENTS_HELP) in {'y', 'Y'}:
            print(get_info(clifuncs))
        exit()
    return memory
