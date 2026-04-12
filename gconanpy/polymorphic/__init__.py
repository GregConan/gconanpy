#!/usr/bin/env python3

"""
Unified interface for Collection accessor and mutator functions.
Accessor/mutator functions that work on lists and sets agnostically.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-09
Updated: 2026-04-11
"""
# Import standard libraries
from collections.abc import Collection, Hashable, Iterable, Mapping, \
    MutableMapping, MutableSequence, MutableSet, Sequence
import functools
import itertools
from typing import Any, cast, TypeVar

_C = TypeVar("_C", bound=Collection)
_T = TypeVar("_T")
_KT = TypeVar("_KT", bound=Hashable)
_MM = TypeVar("_MM")


# TOSORT: '__and__', '__delitem__', '__getitem__', '__iadd__', '__iand__', '__imul__', '__ior__', '__isub__', '__ixor__', '__mul__', '__or__', '__rand__', '__rmul__', '__ror__', '__rsub__', '__rxor__', '__setitem__', '__sub__',
# N/A:  '__add__', '__reversed__', 'count', 'index', 'insert', 'reverse', 'sort',
# TODO:
# DONE: '__xor__', 'add', 'append', 'difference', 'difference_update', 'discard', 'extend', 'intersection', 'intersection_update', 'isdisjoint', 'issubset', 'issuperset', 'symmetric_difference', 'symmetric_difference_update', 'union', 'update'


@functools.singledispatch
def add(self: Collection[_T], element: _T) -> None: ...
@functools.singledispatch
def delete(self: Collection[_T], element: _T, /) -> None: ...
@functools.singledispatch
def difference(self: _C, *others: Iterable) -> _C: ...
@functools.singledispatch
def difference_update(self: Collection[_T], *others: Iterable[_T]) -> None: ...
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
def union(self: _C, *others: Iterable) -> _C: ...


@functools.singledispatch
def intersection_update(
    self: Collection[_T], *others: Iterable[_T]) -> None: ...


@functools.singledispatch
def symmetric_difference_update(
    self: Collection[_T], other: Iterable[_T], /) -> None: ...


add.register(MutableSequence, MutableSequence.append)

# TODO: Using register(MutableSet, MutableSet.add) throws NotImplemented
add.register(set, set.add)


@add.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], key: _KT, value: _T = None, /) -> None:
    self[key] = value


append = add

delete.register(MutableSet, MutableSet.remove)
delete.register(MutableSequence, MutableSequence.remove)
delete.register(MutableMapping, MutableMapping.__delitem__)

difference.register(set, set.difference)


@difference.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    excludables = set()
    excludables.update(*others)
    return [el for el in self if el not in excludables]


difference_update.register(set, set.difference_update)


@difference_update.register(MutableSequence | MutableMapping)
def _(self: MutableSequence[_T] | MutableMapping[_T, Any],
      *others: Iterable[_T]) -> None:
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


@discard.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], key: _KT, /) -> None:
    try:
        del self[key]
    except KeyError:
        pass


extend.register(MutableSequence, MutableSequence.extend)
extend.register(set, set.update)
extend.register(MutableMapping, MutableMapping.update)


# TODO define `and_` function as alias for `intersection`, or vice versa?
intersection.register(set, set.intersection)


@intersection.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    interset = set[_T](self)
    interset.intersection_update(*others)
    return [el for el in self if el in interset]  # TODO OPTIMIZE?


@intersection.register(Mapping)
def _(self: Mapping[_KT, _T], *others: Iterable[_KT]) -> dict[_KT, _T]:
    interset = set[_KT](self)
    interset.intersection_update(*others)
    return {k: v for k, v in self.items() if k in interset}  # TODO OPTIMIZE?


intersection_update.register(set, set.intersection_update)


@intersection_update.register(MutableSequence)
def _(self: MutableSequence[_T], *others: Iterable[_T]) -> None:
    # Get a set of all elements to return by intersecting all input Collections
    if others:
        interset = set[_T](self)
        interset.intersection_update(*others)

        # Remove the elements in others that aren't in all input Collections
        excludables = set[_T](self).union(*others) - interset
        for exclude in excludables:  # Yes, declaring set(self) twice is needed
            discard(self, exclude)


@intersection_update.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], *others: Iterable[_T]) -> None:
    # Get a set of all elements to return by intersecting all input Collections
    if others:
        interset = set[_KT](self)
        interset.intersection_update(*others)

        # Remove the elements in others that aren't in all input Collections
        excludables = set[_KT](self).union(*others) - interset
        for exclude in excludables:  # Yes, declaring set(self) twice is needed
            discard(self, exclude)

        for k in interset:
            try:
                self[k] = cast(Mapping, others[-1])[k]
            except (IndexError, KeyError):
                pass


isdisjoint.register(MutableSet, MutableSet.isdisjoint)


@isdisjoint.register(Sequence | Mapping)
def _(self: Sequence[_T] | Mapping[_T, Any], other: Iterable[_T], /) -> bool:
    for el in itertools.chain.from_iterable((self, other)):
        if (el in self) is (el in other):
            return False
    return True


issubset.register(set, set.issubset)


@issubset.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> bool:
    try:
        other = set[_T](other)  # TODO OPTIMIZE?
    except TypeError:  # If other includes unhashables
        pass
    for el in self:
        if el not in other:
            return False
    return True


@issubset.register(Mapping)
def _(self: Mapping[_KT, Any], other: Iterable[_KT], /) -> bool:
    _EXCLUDE = object()
    try:
        other_set = set[_KT](self)  # TODO OPTIMIZE?
    except TypeError:  # If other includes unhashables
        other_set = self
    for k, v in self.items():
        if k not in other_set:
            return False
        try:
            if cast(Mapping, other).get(k, _EXCLUDE) != v:
                return False
        except AttributeError:
            pass
    return True


issuperset.register(set, set.issuperset)


@issuperset.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> bool:
    try:
        self_set = set[_T](self)  # TODO OPTIMIZE?
    except TypeError:  # If other includes unhashables
        self_set = self
    for el in other:
        if el not in self_set:
            return False
    return True


@issuperset.register(Mapping)
def _(self: Mapping[_KT, Any], other: Iterable[_KT], /) -> bool:
    _EXCLUDE = object()
    for k in other:
        if k not in self:
            return False
        try:
            if self.get(k, _EXCLUDE) != cast(Mapping, other)[k]:
                return False
        except AttributeError:
            pass
    return True


symmetric_difference.register(set, set.symmetric_difference)


@symmetric_difference.register(Sequence)
def _(self: Sequence[_T], other: Iterable[_T], /) -> list[_T]:
    return [el for el in itertools.chain.from_iterable((self, other))
            if (el in self) is not (el in other)]


@symmetric_difference.register(Mapping)
def _(self: Mapping[_KT, _T], other: Mapping[_KT, _T], /) -> dict[_KT, _T]:
    ret = {k: v for k, v in self.items() if k not in other}
    for k in other:  # TODO OPTIMIZE?
        if k not in self:
            ret[k] = other[k]
    return ret


symmetric_difference_update.register(set, set.symmetric_difference_update)


@symmetric_difference_update.register(MutableSequence)
def _(self: MutableSequence[_T], other: Iterable[_T], /) -> None:
    interset = set[_T](self).intersection(other)
    for el in interset:
        self.remove(el)
    for el in other:  # TODO OPTIMIZE?
        if el not in interset:
            self.append(el)


@symmetric_difference_update.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], other: Mapping[_KT, _T], /) -> None:
    interset = set[_KT](self).intersection(other)
    for el in interset:
        delete(self, el)  # self.pop(el)

    ret = {k: v for k, v in self.items() if k not in other}
    for k in other:  # TODO OPTIMIZE?
        if k not in self:
            ret[k] = other[k]


union.register(set, set.union)


@union.register(MutableSequence)
def _(self: MutableSequence[_T], *others: Collection[_T]) -> list[_T]:
    others_set = set[_T]()
    others_set.update(*others)
    to_add = others_set - set[_T](self)
    return [*self, *to_add]  # TODO OPTIMIZE?
    # return self + list[_T](to_add)


@union.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], other: MutableMapping[_KT, _T]
      ) -> dict[_KT, _T]:
    return {**self, **other}  # TODO OPTIMIZE?


remove = delete
update = extend
xor = symmetric_difference
