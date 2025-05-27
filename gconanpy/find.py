#!/usr/bin/env python3

"""
Classes and functions that iterate and break once they find what they're looking for.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-02
Updated: 2025-05-26
"""
# Import standard libraries
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

# Import remote custom libraries
try:
    from metafunc import DATA_ERRORS, FinderTypes as Typ, \
        KeepSkippingExceptions, IgnoreExceptions, WrapFunction
    from trivial import is_not_none, always_none
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.metafunc import DATA_ERRORS, FinderTypes as Typ, \
        KeepSkippingExceptions, IgnoreExceptions, WrapFunction
    from gconanpy.trivial import is_not_none, always_none


def iterfind(find_in: Iterable, found_if: Callable = is_not_none,
             found_args: Iterable = list(),
             found_kwargs: Mapping[str, Any] = dict(),
             default: Typ.D = None, element_is_arg: bool = True
             ) -> Typ.I | Typ.D:
    for each_item in find_in:
        args = [each_item, *found_args] if element_is_arg else found_args
        if found_if(*args, **found_kwargs):
            to_return = each_item
            break
    else:
        to_return = default
    return to_return


def modifind(find_in: Iterable,
             modify: Callable | None = None,
             modify_args: Iterable = list(),
             found_if: Callable = is_not_none,
             found_args: Iterable = list(),
             default: Any = None,
             errs: Iterable[type[BaseException]] = [
                 *DATA_ERRORS, UnboundLocalError]) -> Typ.I | Typ.D:
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


def spliterate(parts: list[str], ready_if:
               Callable[[str | None], bool] = is_not_none,
               min_len: int = 1, get_target:
               Callable[[str], Any] = always_none,
               pop_ix: int = -1, join_on: str = " ") -> tuple[str, Any]:
    """ _summary_

    :param parts: Iterable[str] to iteratively modify, check, and recombine
    :param ready_if: Callable[[str], bool], function that returns True \
        if join_on.join(parts) is ready to return and False if it still \
        needs to be modified further; defaults to is_not_none
    :param pop_ix: int, index of item to remove from parts once per \
        iteration; defaults to -1 (the last item)
    :param join_on: str, delimiter to insert between parts; defaults to " "
    :return: tuple[str, Any], the modified and recombined string built from \
        parts and then something retrieved from within parts
    """
    gotten = get_target(parts[pop_ix])
    rejoined = join_on.join(parts)
    while not ready_if(rejoined) and len(parts) > min_len \
            and gotten is None:
        parts.pop(pop_ix)
        gotten = get_target(parts[pop_ix])
        rejoined = join_on.join(parts)
    return rejoined, gotten


class UntilFound(WrapFunction):
    def check_each(self, find_in: Iterable, default: Any = None,
                   element_is_arg: bool = True) -> Typ.I | Typ.D:
        return iterfind(find_in, self.inner, default=default,
                        element_is_arg=element_is_arg)


class BasicRange(Iterable):
    """ Iterator like range(); base class for custom iterators to add to. """

    def __init__(self, iter_over: Sequence, start_at: int = 0,
                 end_at: int | None = None, step: int = 1) -> None:
        """ 
        :param iter_over: Sequence[Any] to iterate over
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop at; defaults to len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1
        """
        self.end = len(iter_over) - 1 if end_at is None else end_at
        self.is_iterating = True
        self.ix = start_at
        self.start = start_at
        self.step, self.not_yet_at = (-abs(step), int.__ge__) if \
            self.start > self.end else (abs(step), int.__lt__)
        self.to_iter = iter_over

    def __getitem__(self, ix: int) -> Typ.I:
        return self.to_iter[ix]

    def __iter__(self):
        """ Reset some variables to start iterating.

        :return: BasicRange, self
        """
        self.is_iterating = True
        self.ix = self.start
        return self

    def __len__(self) -> int:
        """
        :return: int, total number of items that this BasicRange iterates over
        """
        return len(self.to_iter)

    def __next__(self) -> Typ.I:
        """
        :raises StopIteration: If there are no more items to iterate over.
        :return: Any, the next element of the Sequence being iterated over.
        """
        if self.is_iterating:
            next_value = self[self.ix]  # self.__getitem__(self.ix)
            self.is_iterating = self.has_next()
            self.ix += self.step
            return next_value
        else:
            raise StopIteration()

    def has_next(self) -> bool:
        """
        :return: bool, True if any items remain to iterate over; else False
        """
        return self.not_yet_at(self.ix, self.end)


class ErrIterChecker(BasicRange, IgnoreExceptions, KeepSkippingExceptions):
    def __init__(self, iter_over: Iterable, is_done: bool = False,
                 *catch: type[BaseException]):
        BasicRange.__init__(self, list(iter_over))
        KeepSkippingExceptions.__init__(self, catch, is_done)

    def __enter__(self):
        """ Method called when entering the active block of a context manager.

        Must be explicitly defined here (not only in a superclass) for \
        VSCode to realize that ErrIterChecker(...) returns an instance of \
        the ErrIterChecker class after importing gconanpy via poetry.

        :return: ErrIterChecker, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 exc_val: BaseException | None = None, _: Any = None) -> bool:
        if exc_val:
            self.errors.append(exc_val)
        return super().__exit__(exc_type)  # , exc_val, _)

    def is_not_ready(self) -> bool:
        """ 
        :return: bool, False if there is no more need to iterate; else False.
        """
        return self.is_iterating and not self.is_done


class ReadyChecker(BasicRange):
    """ Context manager class to conveniently check once per iteration \
        whether an item being modified is ready to return. """

    def __init__(self, to_check: Any, iter_over: Iterable[Typ.I],
                 ready_if: Callable, *ready_args: Any, **ready_kwargs: Any
                 ) -> None:
        """
        :param to_check: Any, the item to iteratively check the readiness of.
        :param iter_over: Iterable[Any] to iterate over.
        :param ready_if: Callable[[Any, *ready_args, **ready_kwargs], bool], \
            function that returns either True if to_check is ready to return \
            or False if it needs further modification.
        :param ready_args: Iterable[_R] of positional arguments to pass \
            into the ready_if function
        :param ready_args: Mapping[str, Any] of keyword arguments to pass \
            into the ready_if function
        """
        super().__init__(iter_over=list(iter_over))
        self.args = ready_args
        self.item_is_ready = ready_if
        self.kwargs = ready_kwargs
        self.to_check = to_check

    def __call__(self, item: Any) -> None:  # next_try
        """ Save a thing to iteratively modify and check the readiness of.

        :param item: Any, object to check the readiness of.
        """
        self.to_check = item

    def __enter__(self):
        """ Method called when entering the active block of a context manager.

        Must be explicitly defined here (not only in a superclass) for \
        VSCode to realize that ReadyChecker(...) returns an instance of \
        the ReadyChecker class after importing gconanpy via poetry.

        :return: ReadyChecker, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        """ Method called when exiting the active block of a context manager.

        :param exc_type: type[BaseException] called from within the block, \
            or None if the block executed without raising any errs/exceptions
        :return: bool, True if the block executed without error; else False
        """
        return exc_type is None

    def is_not_ready(self) -> bool:
        """ 
        :return: bool, True to keep iterating; else False if that's unneeded.
        """
        return self.is_iterating and not self.item_is_ready(self.to_check)
