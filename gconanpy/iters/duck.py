#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-08-01
Updated: 2025-11-14
"""
# Import standard libraries
from copy import copy, deepcopy
from collections.abc import Collection, Hashable, Iterable, Iterator, \
    MutableSet, MutableMapping, MutableSequence, Reversible, Sequence
from more_itertools import all_equal
import sys
from typing import Any, Mapping, cast, overload, Self, TypeVar

# Import local custom libraries
try:
    from gconanpy.mapping import keys_mapped_to
    from gconanpy.meta import DATA_ERRORS, name_of
    from gconanpy.meta.typeshed import AddableSequence, BytesOrStr, \
        DATA_ERRORS, SupportsAnd, SupportsGetItem, SupportsItemAccess, \
        SupportsRichComparison
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from mapping import keys_mapped_to
    from meta import name_of
    from meta.typeshed import AddableSequence, BytesOrStr, DATA_ERRORS, \
        SupportsGetItem, SupportsItemAccess, SupportsRichComparison


_K = TypeVar("_K", Hashable, None)  # Mapping keys type


class DuckCollection[T]:
    """ Interface to access and modify a `Collection` without \
        knowing exactly what type of `Collection` it is. """
    ducks: Collection[T]  # Collection wrapped to access/modify it
    UNIQUE = object()  # Unique value to use as default parameter

    def __init__(self, ducks: Collection[T]) -> None:
        """ Wrap a `Collection` using an interface including as many \
            different methods from specific `Collection` types as reasonably \
            possible, especially `set` and `list` methods.

        :param ducks: Collection[T: Any], wrapped for access & modification \
            using various methods typically exclusive to certain \
            `MutableSequence`, `MutableSet`, and `MutableMapping` classes.
        """
        self.ducks = ducks

    def __add__(self, other: Iterable[T]) -> Self:
        copied = self.copy()
        return copied.extend(other) or copied

    def __contains__(self, duck: T) -> bool:
        """
        :param duck: T: Any, object to look for in this `DuckCollection`.
        :return: bool, True if `duck` is an object in this `DuckCollection`; \
            else False if it isn't.
        """
        return duck in self.ducks

    def __eq__(self, other: Collection[T]) -> bool:
        """ Implement `self == other`.

        :param other: Collection[T: Any] to compare to this `DuckCollection`.
        :return: bool, True if `other` has the same elements in the same \
            order (if any) as this `DuckCollection`; else False.
        """
        if self.ducks == other:
            return True

        try:
            if len(self.ducks) != len(other):
                return False
        except DATA_ERRORS:
            pass
        try:
            match self.ducks, other:
                case Sequence(), Sequence():
                    result = True
                    for mine, yours in zip(self.ducks, other):
                        if mine != yours:
                            result = False
                            break
                case _:
                    try:
                        result = set(self.ducks) == set(other)
                    except DATA_ERRORS:
                        result = self.ducks == other
            return result
        except DATA_ERRORS:
            return False

    def __iter__(self) -> Iterator[T]:
        """
        :return: Iterator[T: Any] over every object ("duck") contained in \
            this `DuckCollection`.
        """
        return iter(self.ducks)

    def __len__(self) -> int:
        """ 
        :return: int, the number of objects ("ducks") contained in this
            `DuckCollection`.
        """
        return len(self.ducks)

    def __repr__(self) -> str:
        """ 
        :return: str, a string representation of this `DuckCollection` that \
            includes its type and the `Collection` that it wraps.
        """
        return f"{name_of(self)}({self.ducks})"

    def __reversed__(self) -> Iterator[T]:  # -> reversed[T]:
        """
        :return: Iterator[T], a reverse iterator over this `DuckCollection`, \
            if it's `Reversible`; else an iterator over this `DuckCollection`
        """
        try:
            return reversed(cast(Reversible[T], self.ducks))
        except DATA_ERRORS:
            return iter(self.ducks)

    def __getitem__(self, key: _K = None) -> T:
        """ 
        :param key: Hashable | None, key mapped to the value to return, if \
            any; else None to return the last value (or an arbitrary one); \
            defaults to None
        :return: T, the value mapped to `key` in this `DuckCollection`, if \
            any; else the last item in this `DuckCollection`, if it is \
            ordered; else an arbitrary item from this `DuckCollection`.
        """
        try:  # If self.ducks has __getitem__, then call that.
            gotten = cast(SupportsGetItem, self.ducks)[key]
        except DATA_ERRORS:  # Otherwise, get an element; preferably the last
            gotten = next(reversed(self))
        return gotten

    def __setitem__(self, key: int | _K, duck: T) -> None:
        """
        :param ix: int, _description_
        :param duck: T, _description_
        :raises TypeError: _description_
        """
        try:
            cast(SupportsItemAccess, self.ducks)[key] = duck
        except DATA_ERRORS:
            match self.ducks:
                case tuple():
                    self.ducks = (*self.ducks[:cast(int, key)], duck,
                                  *self.ducks[cast(int, key) + 1:])
                case MutableSet():
                    self.ducks.add(duck)
                case _:
                    raise TypeError

    def add(self, duck: T, key: _K = None) -> None:
        """ Append `duck` to the end of the `Sequence`, or add `duck` to the \
            unordered `Collection`. Replicates `list.append` and `set.add`.

        :param duck: T: Any, object to add to this `DuckCollection`.
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case str() | bytes():
                self.ducks += duck
            case MutableSequence():
                self.ducks.append(duck)
            case MutableSet():
                self.ducks.add(duck)
            case tuple():
                self.ducks = (*self.ducks, duck)
            case MutableMapping():
                cast(MutableMapping[_K, T], self.ducks)[key] = duck
            case _:
                raise TypeError

    # DuckCollection can use "add" and "append" interchangeably. The class
    # will automatically choose the appropriate method to add a new element
    append = add

    # Alias to check whether all elements are identical to each other
    are_same = all_equal

    def clear(self, *args, **kwargs) -> None:
        """ Replace the contained/wrapped `Collection` with an empty one. 

        :param args: Iterable, positional arguments to initialize a new \
            instance of the contained/wrapped `Collection`.
        :param kwargs: Mapping, keyword arguments to initialize a new \
            instance of the contained/wrapped `Collection`.
        """
        self.ducks = type(self.ducks)(*args, **kwargs)

    def copy(self, deep: bool = False) -> Self:
        """
        :param deep: bool, True to return a deep copy, else False to return \
            a shallow copy; defaults to False.
        :return: Self, a copy of this `DuckCollection`.
        """
        copy_it = deepcopy if deep else copy
        return type(self)(copy_it(self.ducks))

    def difference_update(self, ducks: Iterable[T]) -> None:
        """ Remove all elements of another `Iterable` (`ducks`) from this one.

        Replicates `set.difference_update`.

        :param ducks: Iterable[T], items to remove from this `DuckCollection`.
        """
        try:
            cast(set, self.ducks).difference_update(ducks)
        except DATA_ERRORS:  # If it isn't a set, iteratively remove `ducks`.
            for duck in ducks:  # TODO Is there any reason to complicate this?
                self.discard(duck)

    __sub__ = difference_update

    def discard(self, duck: T) -> None:
        """ Remove an element from this `DuckCollection` if present; if not, \
            then do nothing. Replicates `set.discard`.

        Unlike `DuckCollection.remove`, the `discard` method does not raise \
        an exception when an element is missing from the set.

        :param duck: T, element to try to remove from this `DuckCollection`
        """
        try:
            self.remove(duck)
        except DATA_ERRORS:
            pass

    def extend(self, ducks: Iterable[T]) -> None:
        """ Extend this `DuckCollection` by adding elements from the iterable.

        Replicates `list.extend`, `set.update`, and `dict.update`.

        :param ducks: Iterable[T], elements to add to this `DuckCollection`.
        """
        match self.ducks:
            case MutableSequence():
                self.ducks.extend(ducks)
            case set():
                self.ducks.update(ducks)
            case MutableMapping():
                self.ducks.update(cast(MutableMapping, ducks))
            case AddableSequence():
                self.ducks += ducks
            case _:
                for duck in ducks:
                    self.add(duck)

    get = __getitem__

    def index(self, duck: T, start: int = 0, stop: int = sys.maxsize
              ) -> int | _K:
        """ Return first index of `duck` in the `Sequence` wrapped by this \
            `DuckCollection`. Raise exception if this isn't a `Sequence`, or \
            if `duck` isn't in this `DuckCollection`.

        Replicates `Sequence.index`.

        :param duck: T, item to find the index of in this `DuckCollection`
        :param start: int, first index to check; defaults to 0
        :param stop: int, last index to check; defaults to \
            `min(len(self), sys.maxsize)`
        :raises TypeError: if the container/iterable wrapped by this \
            `DuckCollection` has no `index` method (i.e., isn't a `Sequence`).
        :raises ValueError: if `duck` is not present in this `DuckCollection`.
        :return: int, first index of `duck` in this `DuckCollection`.
        """
        match self.ducks:
            case Sequence():
                key = self.ducks.index(duck, start, stop)
            case Mapping():
                key = None
                for key in keys_mapped_to(cast(Mapping[_K, T],
                                               self.ducks), duck):
                    try:
                        if start < cast(SupportsRichComparison, key) < stop:
                            break
                    except DATA_ERRORS:
                        break
                if key is None:
                    raise TypeError
            case _:
                raise TypeError
        return key

    def insert(self, duck: T, at_ix: int | _K = -1):
        """ Insert `duck` into this `DuckCollection` before `at_ix`.

        :param duck: T, item to insert into this `DuckCollection`
        :param at_ix: int, index to insert `duck` at; defaults to -1
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case bytes() | str():
                self.ducks = self.ducks[:ix] + duck + self.ducks[ix:]
            case MutableSequence():
                self.ducks.insert(cast(int, at_ix), duck)
            case MutableSet():
                self.ducks.add(duck)
            case MutableMapping():
                cast(MutableMapping[_K, T], self.ducks
                     )[cast(_K, at_ix)] = duck
            case tuple():
                self.ducks = (*self.ducks[:at_ix], duck, *self.ducks[at_ix:])
            case _:
                raise TypeError

    def intersection(self, other: Iterable[T]) -> set[T]:
        """ Return the intersection of this `DuckCollection` and another \
            `Iterable` as a `set` of their shared elements.

        Replicates `set.intersection`.

        :param other: Iterable[T] to intersect with this `DuckCollection`.
        :return: set[T] of all elements in `self` and in `other`.
        """
        return set(self.ducks) & set(other)

    def isdisjoint(self, other: Collection[T]) -> bool:
        """ 
        :param other: Collection[T]
        :return: bool, True if this `DuckCollection` has no elements in \
            common with `other`; else False if there's any intersection.
        """
        try:  # Try using bitwise AND to check that there's no intersection
            return not (self.ducks & other
                        )  # type: ignore[reportOperatorIssue]
        except TypeError:  # If bitwise AND doesn't work, iteratively check
            for duck in other:
                if duck in self.ducks:
                    return False
            return True

    @overload
    def pop(self, key: int | None) -> T: ...
    @overload
    def pop(self, key: T | None) -> Any: ...
    @overload
    def pop(self, key: object) -> Any: ...
    @overload
    def pop(self) -> Any: ...

    def pop(self, key=UNIQUE):
        """ Remove and return item mapped to `key` (i.e., at index).

        :param key: T | int, key or index of item to pop; default last if \
            this is a `Sequence`, else arbitrary
        :raises TypeError: if `self.ducks` is an unsupported type.
        :raises IndexError: if this `DuckCollection` is empty or `key` is \
            is index out of range.
        :return: T, item that was mapped to `key` (or at that index), now \
            removed from this `DuckCollection`.
        """
        if key is self.UNIQUE:
            key = -1
        match self.ducks:
            case MutableSet():
                popped = self.ducks.pop()
            case MutableSequence():
                popped = self.ducks.pop(cast(int, key))
            case AddableSequence():
                popped = self.ducks[key]
                all_ducks = self.ducks
                self.ducks = all_ducks[:key]
                if key != -1:
                    self.ducks += all_ducks[key + 1:]
            case MutableMapping():
                popped = self.ducks.pop(cast(T, key))
            case _:
                raise TypeError
        return popped

    def remove(self, duck: T) -> None:
        """ Remove first occurrence of `duck` in this `DuckCollection`. \
            Replicates `list.remove` and `set.remove`.

        :param duck: T, item to remove from this `DuckCollection`.
        :raises ValueError: if `duck` is not present in `DuckCollection`.
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case BytesOrStr() as ducks:
                self.ducks = self.ducks.replace(duck, type(ducks)())
            case MutableSequence() | MutableSet():
                self.ducks.remove(duck)
            case AddableSequence():  # tuple():
                ix = self.ducks.index(duck)
                self.ducks = self.ducks[:ix] + self.ducks[ix + 1:]
            case MutableMapping():
                for key, value in self.ducks.items():
                    if value == duck:
                        self.ducks.pop(key)
                        break
            case _:
                raise TypeError

    def replace(self, old: T, new: T, count: int = -1) -> None:
        """ Replace `count` instances of `old` in this `DuckCollection` with \
            `new`. Replicates `str.replace` and `bytes.replace`.

        :param old: T, the item to replace.
        :param new: T, the replacement item.
        :param count: int, the maximum number of occurrences of `old` to \
            replace with `new`. By default, -1 means replace all occurrences.
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case BytesOrStr():
                self.ducks = self.ducks.replace(old, new, count)
            case MutableSet():
                self.ducks.remove(old)
                self.ducks.add(new)
            case MutableSequence():
                try:
                    for _ in range(count):
                        self.ducks[self.ducks.index(old)] = new
                except ValueError:
                    pass
            case Sequence() as seq:
                ducks = list(self.ducks)
                try:
                    for _ in range(count):
                        ducks[self.ducks.index(old)] = new
                except ValueError:
                    pass
                self.ducks = type(seq)(*ducks)
            case MutableMapping():
                for key, value in self.ducks.items():
                    if value == old:
                        self.ducks[key] = value
                        if count == 0:
                            break
                        else:
                            count -= 1
            case _:
                raise TypeError

    set_to = __setitem__

    # DuckCollection can use "extend" and "update" interchangeably. The class
    # will automatically choose the appropriate method to concatenate/merge.
    update = extend
