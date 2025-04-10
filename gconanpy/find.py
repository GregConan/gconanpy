#!/usr/bin/env python3

"""
Functions that iterate and break once they find what they're looking for.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-02
Updated: 2025-04-09
"""
# Import standard libraries
import pdb
from typing import Any, Callable, Iterable, Sequence

# Import remote custom libraries
try:
    from metafunc import IgnoreExceptions, Trivial
    from typevars import FinderTypes as Typ
except ModuleNotFoundError:
    from gconanpy.metafunc import IgnoreExceptions, Trivial
    from gconanpy.typevars import FinderTypes as Typ


class BasicRange(Iterable):
    """ Iterator like range(); base class for custom iterators to add to. """

    def __init__(self, iter_over: Sequence[Typ.I], start_at: int = 0,
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


def get_nested_attribute_from(an_obj: Any, *attribute_names: str) -> Any:
    # TODO Integrate this into DotDict.lookup method?
    """
    get_nested_attribute_from(an_obj, "first", "second", "third") will return
    an_obj.first.second.third if it exists, and None if it doesn't.
    :param an_obj: Any
    :param attribute_names: Iterable[str] of attribute names. The first names
                            an attribute of an_obj; the second names an
                            attribute of that first attribute; and etc. 
    :return: Any, the attribute of an attribute ... of an attribute of an_obj
    """
    attributes = list(attribute_names)  # TODO reversed(attribute_names) ?
    while attributes and an_obj is not None:
        an_obj = getattr(an_obj, attributes.pop(0), None)
    return an_obj


def modifind(find_in: Iterable[Typ.I],
             modify: Typ.Modify | None = None,
             modify_args: Iterable[Typ.X] = list(),
             found_if: Typ.Ready = Trivial.is_not_none,
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
               Callable[[str | None], bool] = Trivial.is_not_none,
               min_len: int = 1, get_target:
               Callable[[str], Any] = Trivial.noop,
               pop_ix: int = -1, join_on: str = " ") -> tuple[str, Any]:
    """ _summary_

    :param parts: Iterable[str] to iteratively modify, check, and recombine
    :param is_not_ready: Callable[[str], bool], function that returns False \
        if join_on.join(parts) is ready to return and True if it still \
        needs to be modified further; defaults to Whittler.is_none
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


class ReadyChecker(BasicRange):
    """ Context manager class to conveniently check once per iteration \
        whether an item being modified is ready to return. """

    def __init__(self, to_check: Typ.M, iter_over: Iterable[Typ.I],
                 ready_if: Typ.Ready, *ready_args: Typ.R, **ready_kwargs: Any
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

    def __call__(self, item: Any) -> None:  # next_try
        """ Save a thing to iteratively modify and check the readiness of.

        :param item: Any, object to check the readiness of.
        """
        self.to_check = item

    def is_not_ready(self) -> bool:
        """ 
        :return: bool, False if there is no more need to iterate; else False.
        """
        return self.is_iterating and not self.item_is_ready(self.to_check)
