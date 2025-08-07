#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-08-01
Updated: 2025-08-07
"""
# Import standard libraries
from collections.abc import Collection, Hashable, Iterable, \
    Iterator, MutableSet, MutableMapping, MutableSequence, Sequence
import sys
from typing import Any, cast, overload, Self

# Import local custom libraries
try:
    from meta import AddableSequence, BytesOrStr, DATA_ERRORS, name_of
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.meta import AddableSequence, BytesOrStr, DATA_ERRORS, name_of


class DuckCollection[T]:
    """ Interface to access and modify a `Collection` without \
        knowing exactly what type of `Collection` it is. """
    ducks: Collection[T]  # Collection wrapped to access/modify it

    def __init__(self, ducks: Collection[T]) -> None:
        """ Wrap a `Collection` using an interface including as many \
            different methods from specific `Collection` types as reasonably \
            possible, especially `set` and `list` methods.

        :param ducks: Collection[T] to wrap for access and modification \
            using various methods typically exclusive to `MutableSequence`, \
            `MutableSet`, or `MutableMapping` classes.
        """
        self.ducks = ducks

    def __contains__(self, duck: T) -> bool:
        return duck in self.ducks

    def __eq__(self, other: Collection[T]) -> bool:
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
        return iter(self.ducks)

    def __len__(self) -> int:
        return len(self.ducks)

    def __repr__(self) -> str:
        """ 
        :return: str, a string representation of this `DuckCollection` that \
            includes its type and the `Collection` that it wraps.
        """
        return f"{name_of(self)}({self.ducks})"

    def __reversed__(self) -> Iterator[T]:  # -> reversed[T]:
        """
        :return: Iterator[T], a reverse iterator over this `DuckCollection`.
        """
        try:
            return reversed(self.ducks)  # type: ignore
        except DATA_ERRORS:
            return iter(self.ducks)

    def add(self, duck: T, key: Hashable | None = None) -> None:
        """ Append object to the end of a `Sequence`, or add object to an \
            unordered `Collection`. Replicates `list.append` and `set.add`.

        :param duck: T, object to add to this `DuckCollection`.
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case BytesOrStr():
                self.ducks += duck
            case MutableSequence():
                self.ducks.append(duck)
            case MutableSet():
                self.ducks.add(duck)
            case tuple():
                self.ducks = (*self.ducks, duck)
            case MutableMapping():
                cast(MutableMapping[Hashable, T], self.ducks)[key] = duck
            case _:
                raise TypeError

    append = add

    def clear(self) -> None:
        """
        Replace the contained/wrapped `Collection` with an empty one. 
        """
        self.ducks = type(self.ducks)()

    def copy(self) -> Self:
        """ 
        :return: Self, a shallow copy of this `DuckCollection`.
        """
        return self.__class__(self.ducks)

    def difference_update(self, ducks: Iterable[T]) -> None:
        """ Remove all elements of another iterable (`ducks`) from this one.

        Replicates `set.difference_update`.

        :param ducks: Iterable[T], items to remove from this `DuckCollection`.
        """
        match self.ducks:
            case set():
                self.ducks.difference_update(ducks)
            case _:  # TODO Is there any reason to complicate this?
                for duck in ducks:
                    self.discard(duck)

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
            case _:
                for duck in ducks:
                    self.add(duck)

    def get(self, key: Hashable | None = None) -> T:
        """ 
        :param key: Hashable | None, key mapped to the value to return, if \
            any; else None to return the last value (or an arbitrary one); \
            defaults to None
        :return: T, the value mapped to `key` in this `DuckCollection`, if \
            any; else the last item in this `DuckCollection`, if it is \
            ordered; else an arbitrary item from this `DuckCollection`.
        """
        try:
            gotten = self.ducks[key]  # type: ignore[reportIndexIssue]
        except DATA_ERRORS:
            gotten = next(reversed(self))
        return gotten

    def index(self, duck: T, start: int = 0, stop: int = sys.maxsize) -> int:
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
        return cast(Sequence, self.ducks).index(duck, start, stop)

    def isdisjoint(self, other: Collection[T]) -> bool:
        """ 
        :param other: Collection[T]
        :return: bool, True if this `DuckCollection` has no elements in \
            common with `other`; else False if there's any intersection.
        """
        try:
            return not (self.ducks & other
                        )  # type: ignore[reportOperatorIssue]
        except TypeError:
            for duck in other:
                if duck in self.ducks:
                    return False
            return True

    def insert(self, duck: T, at_ix: int = -1):
        """ Insert `duck` into this `DuckCollection` before `at_ix`.

        :param duck: T, item to insert into this `DuckCollection`
        :param at_ix: int, index to insert `duck` at; defaults to -1
        :raises TypeError: if `self.ducks` is an unsupported type.
        """
        match self.ducks:
            case BytesOrStr():
                self.ducks = self.ducks[:ix] + duck + self.ducks[ix:]
            case MutableSequence():
                self.ducks.insert(at_ix, duck)
            case MutableSet():
                self.ducks.add(duck)
            case tuple():
                self.ducks = (*self.ducks[:at_ix], duck, *self.ducks[at_ix:])
            case _:
                raise TypeError

    def intersection(self, other: Collection[T]) -> set[T]:
        """ Return the intersection of this `DuckCollection` and another \
            `Collection` as a `set` of their shared elements (in both \
            both `Collection`s). Replicates `set.intersection`.

        :param other: Collection[T] to intersect with this `DuckCollection`.
        :return: set[T] of all elements in `self` and in `other`.
        """
        return set(self.ducks) & set(other)

    @overload
    def pop(self, key: int | None = None) -> T: ...
    @overload
    def pop(self, key: T | None = None) -> Any: ...

    def pop(self, key=None):
        """ Remove and return item mapped to `key` (i.e., at index).

        :param key: T | int, key or index of item to pop; default last if \
            this is a `Sequence`, else arbitrary
        :raises TypeError: if `self.ducks` is an unsupported type.
        :raises IndexError: if this `DuckCollection` is empty or `key` is \
            is index out of range.
        :return: T, item that was mapped to `key` (or at that index), now \
            removed from this `DuckCollection`.
        """
        if key is None:
            key = -1
        match self.ducks:
            case MutableSet():
                popped = self.ducks.pop()
            case MutableSequence():
                popped = self.ducks.pop(key)
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

    def set_to(self, ix: int, duck: T) -> None:
        """
        :param ix: int, _description_
        :param duck: T, _description_
        :raises TypeError: _description_
        """
        match self.ducks:
            case MutableSequence():
                self.ducks[ix] = duck
            case tuple():
                self.ducks = (*self.ducks[:ix], duck, *self.ducks[ix + 1:])
            case MutableSet():
                self.ducks.add(duck)
            case _:
                raise TypeError

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
            case _:
                raise TypeError

    update = extend
