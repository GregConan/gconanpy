#!/usr/bin/env python3

"""
Unified interface for Collection accessor and mutator functions.
Accessor/mutator functions that work on lists and sets agnostically.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-09
Updated: 2026-04-10
"""
# Import standard libraries
from collections.abc import Collection, Iterable, MutableSequence, Sequence
import functools
import itertools
from typing import Any, cast, TypeVar

_C = TypeVar("_C", bound=Collection)
_T = TypeVar("_T")


# TOSORT: '__and__', '__delitem__', '__getitem__', '__iadd__', '__iand__', '__imul__', '__ior__', '__isub__', '__ixor__', '__mul__', '__or__', '__rand__', '__reversed__', '__rmul__', '__ror__', '__rsub__', '__rxor__', '__setitem__', '__sub__',
# N/A:  '__add__', 'count', 'index', 'insert', 'reverse', 'sort',
# TODO: 'symmetric_difference_update', 'intersection_update',
# DONE: '__xor__', 'add', 'append', 'difference', 'difference_update', 'discard', 'extend', 'intersection', 'isdisjoint', 'issubset', 'issuperset', 'symmetric_difference', 'union', 'update'


@functools.singledispatch
def add(self: Collection[_T], element: _T) -> None: ...
@functools.singledispatch
def difference(self: _C, *others: Iterable) -> _C: ...
@functools.singledispatch
def difference_update(self: _C, *others: Iterable) -> _C: ...
@functools.singledispatch
def discard(self: Collection[_T], element: _T, /) -> None: ...
@functools.singledispatch
def extend(self: Collection[_T], other: Iterable[_T], /) -> None: ...
@functools.singledispatch
def intersection(self: _C, *others: Iterable) -> _C: ...
@functools.singledispatch
def isdisjoint(self: Collection[_T], other: Iterable[_T], /) -> bool: ...
@functools.singledispatch
def issubset(self: Collection[_T], other: Iterable[_T], /) -> bool: ...
@functools.singledispatch
def issuperset(self: Collection[_T], other: Iterable[_T], /) -> bool: ...
@functools.singledispatch
def symmetric_difference(self: _C, other: Iterable, /) -> _C: ...
@functools.singledispatch
def union(self: _C, *others: Collection) -> _C: ...


@functools.singledispatch
def intersection_update(
    self: Collection[_T], *others: Iterable[_T]) -> None: ...


@functools.singledispatch
def symmetric_difference_update(
    self: Collection[_T], other: Iterable[_T], /) -> None: ...


add.register(MutableSequence, MutableSequence.append)
add.register(set, set.add)
append = add

difference.register(set, set.difference)


@difference.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    excludables = set()
    excludables.update(*others)
    return [el for el in self if el not in excludables]


difference_update.register(set, set.difference_update)


@difference_update.register(list)
def _(self: MutableSequence[_T], *others: Iterable[_T]) -> None:
    for el in itertools.chain.from_iterable(others):
        discard(self, el)


# TODO: Using register(MutableSet, MutableSet.<method>) raises NotImplemented
#       from tests.test_mapping.TestAttrMap.test_contains_get_pop_keys_and_len
discard.register(set, set.discard)


@discard.register(MutableSequence)
def _(self: MutableSequence[_T], element: _T, /) -> None:
    try:
        self.remove(element)
    except ValueError:
        pass


extend.register(MutableSequence, MutableSequence.extend)
extend.register(set, set.update)


# TODO define `and_` function as alias for `intersection`, or vice versa?
intersection.register(set, set.intersection)


@intersection.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    interset = set[_T](self)
    interset.intersection_update(*others)
    return [el for el in self if el in interset]  # TODO OPTIMIZE?


intersection_update.register(set, set.intersection_update)


@intersection_update.register(list)
def _(self: list[_T], *others: Iterable[_T]) -> None:
    # Get a set of all elements to return by intersecting all input Collections
    interset = set[_T](self)
    interset.intersection_update(*others)

    # Remove the elements in others that aren't in all input Collections
    excludables = set[_T](self).union(*others) - interset
    for exclude in excludables:  # Yes, declaring set[_T](self) twice is needed
        discard(self, exclude)


isdisjoint.register(set, set.isdisjoint)


@isdisjoint.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> bool:
    for el in itertools.chain.from_iterable((self, other)):
        if (el in self) is (el in other):
            return False
    return True


issubset.register(set, set.issubset)


@issubset.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> bool:
    other_set = set[_T](other)  # TODO OPTIMIZE?
    for el in self:
        if el not in other_set:
            return False
    return True


issuperset.register(set, set.issuperset)


@issuperset.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> bool:
    self_set = set[_T](self)  # TODO OPTIMIZE?
    for el in other:
        if el not in self_set:
            return False
    return True


symmetric_difference.register(set, set.symmetric_difference)


@symmetric_difference.register(list)
def _(self: list[_T], other: Iterable[_T], /) -> list[_T]:
    return [el for el in itertools.chain.from_iterable((self, other))
            if (el in self) is not (el in other)]


symmetric_difference_update.register(set, set.symmetric_difference_update)


@symmetric_difference_update.register(list)
def _(self: list[_T], other: Iterable[_T], /) -> None:
    interset = set[_T](self).intersection(other)
    for el in interset:
        self.remove(el)
    for el in other:  # TODO OPTIMIZE?
        if el not in interset:
            self.append(el)


union.register(set, set.union)


@union.register(list)
def _(self: list[_T], *others: Collection[_T]) -> list[_T]:
    others_set = set[_T]()
    others_set.update(*others)
    to_add = others_set - set[_T](self)
    return self + list[_T](to_add)


update = extend
xor = symmetric_difference
