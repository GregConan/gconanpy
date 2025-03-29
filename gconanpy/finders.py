#!/usr/bin/env python3

"""
Iterator classes that break once they find what they're looking for.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-19
Updated: 2025-03-28
"""
# Import standard libraries
import pdb
from typing import Any, Callable, Iterable, Sequence

# Import local custom libraries
try:
    from metafunc import is_not_none, noop
    from seq import insert_into
    from typevars import FinderTypes as Types
except ModuleNotFoundError:
    from gconanpy.metafunc import is_not_none, noop
    from gconanpy.seq import insert_into
    from gconanpy.typevars import FinderTypes as Types


# TODO Clean up and optimize for efficiency


class BasicRange(Iterable):
    """ Iterator like range() """

    def __init__(self, iter_over: Sequence[Types.S], start_at: int = 0,
                 end_at: int | None = None, step: int = 1) -> None:
        """ Iterator like range()

        :param iter_over: Sequence[Any] to iterate over
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop at; defaults to len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1
        """
        self.end_ix = len(iter_over) - 1 if end_at is None else end_at
        self.is_iterating = True
        self.ix = start_at
        self.start_ix = start_at
        self.step, self.not_yet_at = (abs(step), int.__lt__) if \
            self.start_ix <= self.end_ix else (-abs(step), int.__ge__)
        self.to_iter = iter_over

    def __getitem__(self, ix: int) -> Types.S:
        return self.to_iter[ix]

    def __iter__(self):
        self.is_iterating = True
        self.ix = self.start_ix
        return self

    def __len__(self) -> int:
        return len(self.to_iter)

    def __next__(self) -> Types.S:
        if self.is_iterating:
            next_value = self[self.ix]  # self.__getitem__(self.ix)
            self.is_iterating = self.has_next()
            self.ix += self.step
            return next_value
        else:
            raise StopIteration()

    def end(self) -> Types.S:
        try:
            while self.is_iterating:
                to_return = self.__next__()
            return to_return
        except IndexError:
            pdb.set_trace()
            print()

    def has_next(self) -> bool:
        return self.not_yet_at(self.ix, self.end_ix)


class RangeFinder(BasicRange):
    """ Iterator like range() except that it breaks out of the loop early \
    if it finds an element that meets a specific condition. """

    # TODO Add el_ix to RangeFinder descendants?
    def __init__(self, iter_over: Sequence[Types.S], found_if: Types.Found,
                 found_args: Iterable[Types.F] = list(), el_ix: int = 0,
                 start_at: int = 0, end_at: int | None = None, step: int = 1
                 ) -> None:
        """ Iterator like range() except that it breaks out of the loop \
        early if it finds an element that meets a specific condition.

        :param iter_over: Sequence[S] to iterate over
        :param found_if: Callable[[S, tuple[F, ...]], bool], function \
            that accepts an item of iter_over and returns either True if the \
            item is what we're looking for or False to continue iterating
        :param found_args: Iterable[F] of positional arguments to pass into \
            the found_if function after the iter_over item
        :param el_ix: int, the index/position within found_args to place the \
            next iter_over element at when calling found_if; defaults to 0
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop at; defaults to \
            len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1
        """
        super().__init__(iter_over, start_at, end_at, step)
        self.item_is_ready = lambda x: found_if(*insert_into(found_args,
                                                             x, el_ix))

    def has_next(self) -> bool:
        return not self.item_is_ready(self[self.ix]) and \
            super(RangeFinder, self).has_next()


class Modifinder(RangeFinder):
    def __init__(self, iter_over: Sequence[Types.S], modify: Types.Modify,
                 modify_args: Iterable[Types.X] = list(),
                 found_if: Types.Found = is_not_none,
                 found_args: Iterable[Types.F] = list(),
                 start_at: int = 0, end_at: int | None = None, step: int = 1
                 ) -> None:
        super().__init__(iter_over, found_if, found_args,
                         start_at, end_at, step)
        self.modify = lambda x: modify(x, *modify_args)

    def __getitem__(self, ix: int) -> Types.M:
        return self.modify(self.to_iter[ix])  # super().__getitem__(ix))


class TryExceptifinder(Modifinder):
    def __init__(self, iter_over: Sequence[Types.S], modify: Types.Modify,
                 modify_args: Iterable[Types.X] = list(),
                 found_if: Types.Found = is_not_none,
                 found_args: Iterable[Types.F] = list(),
                 default: Types.D = None, start_at: int = 0,
                 end_at: int | None = None, step: int = 1,
                 catch: Iterable[type] = Types.Errors) -> None:
        super().__init__(iter_over, modify, modify_args, found_if,
                         found_args, start_at, end_at, step)
        self.errs = catch
        self.prev_item = default  # iter_over[start_at]

    def __next__(self) -> Types.S | Types.D:
        try:
            next_item = super(TryExceptifinder, self).__next__()
        except self.errs:
            next_item = self.prev_item
            try:  # self.not_yet_at(self.ix, self.end_ix)
                self.is_iterating = self.has_next()
            except self.errs:
                self.is_iterating = self.not_yet_at(self.ix, self.end_ix)
            self.ix += 1
        return next_item


class PickyModifinder(Modifinder):
    def __init__(self, iter_over: Sequence[Types.S], modify: Types.Modify,
                 modify_args: Iterable[Types.X] = list(),
                 found_if: Types.Found = is_not_none,
                 found_args: Iterable[Types.F] = list(),
                 viable_if: Types.Viable = is_not_none,
                 default: Types.D = None, start_at: int = 0,
                 end_at: int | None = None, step: int = 1) -> None:
        """
        _summary_
        :param iter_over: Sequence[Types.S], _description_
        :param modify: Types.Modify, _description_
        :param modify_args: Iterable[Types.X],_description_, defaults to list()
        :param found_if: Types.Found,_description_, defaults to is_not_none
        :param found_args: Iterable[Types.F],_description_, defaults to list()
        :param viable_if: Types.Viable,_description_, defaults to is_not_none
        :param default: Types.D,_description_, defaults to None
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop iterating at; \
            defaults to len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1
        """
        super().__init__(iter_over, modify, modify_args,
                         found_if, found_args, start_at, end_at, step)
        self.prev_item = default  # iter_over[start_at]

        def is_viable(x):
            try:
                return viable_if(x)
            except Types.Errors:
                return False

        self.item_is_viable = is_viable

    def __next__(self) -> Types.S | Types.D:
        next_item = super(PickyModifinder, self).__next__()
        return next_item if self.item_is_viable(next_item) else self.prev_item


class Whittler(PickyModifinder):

    def __init__(self, to_whittle: Types.T, iter_over: Sequence[Types.S],
                 whittle: Types.Whittler,
                 whittle_args: Iterable[Types.W] = list(),
                 ready_if: Types.Ready = is_not_none,
                 ready_args: Iterable[Types.R] = list(),
                 viable_if: Types.Whittled = len,
                 default: Types.D = None, start_at: int = 0,
                 end_at: int | None = None, step: int = 1) -> None:
        """ Until to_whittle is viable and ready, iteratively modify it.

        :param to_whittle: T, Any object
        :param iter_over: Sequence[S] to iterate over
        :param whittle: Callable[[T, S, tuple[W, ...]], _T] that accepts \
            to_whittle, an element of iter_over element, & *whittle_args if \
            there are any, and then returns a changed version of to_whittle.
        :param whittle_args: Iterable[W], additional positional arguments \
            to call modify(to_whittle, *whittle_args) with on every iteration.
        :param is_ready: Callable[[_T], bool], sufficient condition; \
            returns True if to_whittle is ready to return and False if it \
            needs further modification; defaults to "to_whittle isn't None"
        :param ready_args: Iterable[R],_description_, defaults to list()
        :param viable_if: Callable[[_T], bool], necessary condition; \
            returns True if to_whittle is a valid/acceptable/sensical value \
            to return or True otherwise; defaults to len(to_whittle) > 0
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop iterating at; \
            defaults to len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1

        :return: T, to_whittle but iteratively modified ("whittled down") \
            until is_viable(to_whittle) and is_ready(to_whittle).
        """
        super().__init__(iter_over, whittle, whittle_args, ready_if,
                         ready_args, viable_if, default, start_at,
                         end_at, step)
        self.to_whittle = to_whittle
        self.whittle_next = lambda x, y: whittle(x, y, *whittle_args)

    def __getitem__(self, ix: int) -> Types.M:
        return self.whittle_next(self.to_whittle, self.to_iter[ix])


def spliterate(parts: Iterable[str], ready_if:
               Callable[[str | None], bool] = is_not_none, min_len: int = 1,
               get_target: Callable[[str], Types.T | None] = noop, pop_ix:
               int = -1, join_on: str = " ") -> tuple[str, Types.T | None]:
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
