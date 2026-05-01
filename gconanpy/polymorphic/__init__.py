#!/usr/bin/env python3

"""
Unified interface for Collection accessor and mutator functions.
Accessor/mutator functions that work on lists and sets agnostically.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-09
Updated: 2026-04-17
"""
# Import standard libraries
from collections.abc import Collection, Hashable, Iterable, Mapping, \
    MutableMapping, MutableSequence, MutableSet, Sequence
import functools
import itertools
from typing import Any, cast, TypeVar

# Type variables for annotations
_KT = TypeVar("_KT", bound=Hashable)
_T = TypeVar("_T")


@functools.singledispatch
def add(self: Collection[_T], element: _T) -> None: ...
@functools.singledispatch
def combine(self: Collection[_T], *others: Iterable[_T]) -> Collection[_T]: ...
@functools.singledispatch
def delete(self: Collection[_T], element: _T, /) -> None: ...
@functools.singledispatch
def difference_update(self: Collection[_T], *others: Iterable[_T]) -> None: ...
@functools.singledispatch
def discard(self: Collection[_T], element: _T, /) -> None: ...
@functools.singledispatch
def extend(self: Collection[_T], other: Iterable[_T], /) -> None: ...
@functools.singledispatch
def isdisjoint(self: Collection[_T], other: Iterable[_T], /) -> bool: ...
@functools.singledispatch
def issubset(self: Collection[_T], other: Iterable[_T], /) -> bool: ...
@functools.singledispatch
def issuperset(self: Collection[_T], other: Iterable[_T], /) -> bool: ...


@functools.singledispatch
def difference(self: Collection[_T], *others: Iterable[_T]
               ) -> Collection[_T]: ...


@functools.singledispatch
def intersection(self: Collection[_T], *others: Iterable[_T]
                 ) -> Collection[_T]: ...


@functools.singledispatch
def symmetric_difference(
    self: Collection[_T], other: Iterable[_T], /) -> Collection[_T]: ...


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


combine.register(set, set.union)


@combine.register(MutableSequence)
def _(self: MutableSequence[_T], *others: Collection[_T]) -> list[_T]:
    return [el for el in itertools.chain.from_iterable((self, *others))]


@combine.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], *others: MutableMapping[_KT, _T]
      ) -> dict[_KT, _T]:
    return {**self, **{k: v for other in others
                       for k, v in other.items()}}  # TODO OPTIMIZE?


delete.register(MutableSet, MutableSet.remove)
delete.register(MutableSequence, MutableSequence.remove)
delete.register(MutableMapping, MutableMapping.__delitem__)


difference.register(set, set.difference)


@difference.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    excludables = combine(*others)
    return [el for el in self if el not in excludables]


@difference.register(Mapping)
def _(self: Mapping[_KT, _T], *others: Iterable[_KT]) -> dict[_KT, _T]:
    excludables = combine(*others)
    return {k: v for k, v in self.items() if k not in excludables}


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


def intersect(self: Collection[_T], *others: Iterable[_T]
              ) -> set[_T] | list[_T]:
    try:
        ret = set[_T](*self)
        ret.intersection_update(*others)
    except TypeError:  # If some items in others are unhashable
        ret = [*self]
        for el in self:
            for other in others:
                if el not in other:
                    ret.remove(el)
                    break
    return ret


# TODO define `and_` function as alias for `intersection`, or vice versa?
intersection.register(set, set.intersection)


@intersection.register(Sequence)
def _(self: Sequence[_T], *others: Iterable[_T]) -> list[_T]:
    interset = intersect(self, *others)
    return [el for el in self if el in interset]  # TODO OPTIMIZE?


@intersection.register(Mapping)
def _(self: Mapping[_KT, _T], *others: Iterable[_KT]) -> dict[_KT, _T]:
    interset = intersect(self, *others)
    return {k: v for k, v in self.items() if k in interset}  # TODO OPTIMIZE?


intersection_update.register(set, set.intersection_update)


@intersection_update.register(MutableSequence)
def _(self: MutableSequence[_T], *others: Iterable[_T]) -> None:
    # Remove the elements in others that aren't in all input Collections
    interset = intersect(self, *others)
    to_remove = [el for el in self if el not in interset]
    for el in to_remove:  # TODO OPTIMIZE
        self.remove(el)


@intersection_update.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], *others: Collection[_T]) -> None:
    # Get a set of all elements to return by intersecting all input Collections
    if others:
        interset = set[_KT](self)  # All Mapping keys are hashable
        interset.intersection_update(*others)

        # Remove the elements in others that aren't in all input Collections
        # Yes, declaring set[_KT](self) twice is needed to keep them separate
        excludables = set[_KT](self).union(*others) - interset
        for exclude in excludables:
            discard(self, exclude)

        # Set each kept element's value to its value in the last other Mapping
        # in which it appears to ensure that later Mappings overrides earliers
        for k in interset:
            for other in reversed(others):
                if k in other:
                    try:
                        self[k] = cast(Mapping, other)[k]
                        break
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
        self_set = set[_KT](self)  # TODO OPTIMIZE?
    except TypeError:  # If other includes unhashables
        self_set = self
    for k, v in self.items():
        if k not in self_set:
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
    interset = intersect(self, other)
    for el in interset:
        self.remove(el)
    for el in other:  # TODO OPTIMIZE?
        if el not in interset:
            self.append(el)


@symmetric_difference_update.register(MutableMapping)
def _(self: MutableMapping[_KT, _T], other: Mapping[_KT, _T], /) -> None:
    interset = intersect(self, other)
    for el in interset:
        delete(self, el)  # self.pop(el)

    ret = {k: v for k, v in self.items() if k not in other}
    for k in other:  # TODO OPTIMIZE?
        if k not in self:
            ret[k] = other[k]


# Aliases
append = add
merge = union = combine
remove = delete
update = extend
xor = symmetric_difference
