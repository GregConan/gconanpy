#!/usr/bin/env python3

"""
Functions that iterate and break once they find what they're looking for.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-02
Updated: 2025-04-03
"""
# Import standard libraries
import pdb
from typing import Any, Callable, Iterable

# Import remote custom libraries
try:
    from metafunc import IgnoreExceptions, is_not_none, noop
    from typevars import FinderTypes as Typ
except ModuleNotFoundError:
    from gconanpy.metafunc import IgnoreExceptions, is_not_none, noop
    from gconanpy.typevars import FinderTypes as Typ


def modifind(find_in: Iterable[Typ.I],
             modify: Typ.Modify | None = None,
             modify_args: Iterable[Typ.X] = list(),
             found_if: Typ.Ready = is_not_none,
             found_args: Iterable[Typ.R] = list(),
             default: Typ.D = None,
             errs: Iterable[BaseException] = list()) -> Typ.I | Typ.D:
    i = 0
    is_found = False
    iter_over = list(find_in)
    while not is_found and i < len(iter_over):
        with IgnoreExceptions(*errs):
            modified = modify(iter_over[i], *modify_args
                              ) if modify else iter_over[i]
        with IgnoreExceptions(*errs):
            is_found = found_if(modified, *found_args)
        i += 1
    return modified if is_found else default


def spliterate(parts: Iterable[str], ready_if:
               Callable[[str | None], bool] = is_not_none, min_len: int = 1,
               get_target: Callable[[str], Any] = noop, pop_ix:
               int = -1, join_on: str = " ") -> tuple[str, Any]:
    """ _summary_

    :param parts: Iterable[str], _description_
    :param is_not_ready: Callable[[str], bool], function that returns False \
        if join_on.join(parts) is ready to return and True if it still \
        needs to be modified further; defaults to Whittler.is_none
    :param pop_ix: int,_description_, defaults to -1
    :param join_on: str,_description_, defaults to " "
    :return: _type_, _description_
    """
    gotten = get_target(parts[pop_ix])
    rejoined = join_on.join(parts)
    while not ready_if(rejoined) and len(parts) > min_len \
            and gotten is None:
        parts.pop(pop_ix)
        gotten = get_target(parts[pop_ix])
        rejoined = join_on.join(parts)
    return rejoined, gotten


def whittle(to_whittle: Typ.T, iter_over: Iterable[Typ.I],
            whittler: Typ.Whittler | None = None,
            whittle_args: Iterable[Typ.X] = list(),
            ready_if: Typ.Ready = is_not_none,
            ready_args: Iterable[Typ.R] = list(),
            viable_if: Typ.Viable = len,
            errs: Iterable[BaseException] = list()) -> Typ.T:
    i = 0
    is_ready = False
    while not is_ready and i < len(iter_over):
        prev = to_whittle
        with IgnoreExceptions(*errs):
            to_whittle = whittler(to_whittle, iter_over[i], *whittle_args
                                  ) if whittler else to_whittle
        with IgnoreExceptions(*errs):
            is_ready = ready_if(to_whittle, *ready_args)
        with IgnoreExceptions(*errs):
            if not viable_if(to_whittle):
                to_whittle = prev
        i += 1
    return to_whittle
