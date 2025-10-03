#!/usr/bin/env python3

"""
Classes for use in type hints/checks. No behavior, except in MultiTypeMeta.
Greg Conan: gregmconan@gmail.com
Created: 2025-08-12
Updated: 2025-09-18
"""
# Import standard libraries
import abc
from collections.abc import Callable, Collection, Hashable, Iterable, Mapping
from typing import Any, Protocol, overload, Self, SupportsIndex, \
    runtime_checkable, TYPE_CHECKING

# Purely "internal" errors only involving local data; ignorable in some cases
DATA_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)


@runtime_checkable
class SupportsContains[T](Protocol):
    def __contains__(self, x: T, /): ...


if TYPE_CHECKING:
    from _typeshed import SupportsGetItem, \
        SupportsItemAccess, SupportsLenAndGetItem
else:  # Can't import _typeshed at runtime, so define its imports manually

    @runtime_checkable
    class SupportsGetItem[T](Protocol):
        def __getitem__(self, key, /) -> T: ...

    @runtime_checkable
    class SupportsLenAndGetItem[T](SupportsGetItem[T], Protocol):
        def __len__(self) -> int: ...

    @runtime_checkable
    class SupportsItemAccess[KT, VT](SupportsContains[KT],
                                     SupportsGetItem[VT], Protocol):
        def __delitem__(self, key: KT, /): ...
        def __setitem__(self, key: KT, value: VT, /): ...


@runtime_checkable
class SupportsRichComparison(Protocol):
    def __eq__(self, value, /) -> bool: ...
    def __le__(self, value, /) -> bool: ...
    def __lt__(self, value, /) -> bool: ...
    def __ge__(self, value, /) -> bool: ...
    def __gt__(self, value, /) -> bool: ...
    def __ne__(self, value, /) -> bool: ...


@runtime_checkable
class ComparableHashable(SupportsRichComparison, Protocol):
    def __hash__(self) -> int: ...


@runtime_checkable
class Poppable[T](Protocol):
    """ Any object or class with a `pop` method is a `Poppable`.
        `dict`, `list`, and `set` are each `Poppable`. """

    def pop(self, *_, **_kw) -> T: ...


@runtime_checkable
class Updatable(Protocol):
    """ Any object or class with an `update` method is an `Updatable`.
        `dict`, `MutableMapping`, and `set` are each `Updatable`. """

    def update(self, *_, **_kw): ...


@runtime_checkable
class SupportsGetSlice[T](Protocol):
    @overload
    def __getitem__(self, key: SupportsIndex, /): ...  # -> T: ...
    @overload
    def __getitem__(self, key: slice, /): ...  # -> Self: ...
    def __getitem__(self, key, /): ...  # -> T | Self: ...


@runtime_checkable
class SupportsLenAndGetSlice[T](SupportsGetSlice[T], Protocol):
    def __len__(self) -> int: ...


@runtime_checkable
class SupportsHash(Protocol):
    def __hash__(self) -> int: ...


@runtime_checkable
class SupportsHashAndGetItem[T](SupportsGetSlice[T], SupportsHash, Protocol):
    ...


# Define Sequence Protocol to subclass it to hint certain Sequences
@runtime_checkable
class ProtoSequence[T](SupportsLenAndGetSlice[T], SupportsContains[T],
                       Protocol):
    def __iter__(self): ...
    # def __reversed__(self): ...  # NOTE: tuple lacks __reversed__
    def count(self, value, /) -> int: ...
    def index(self, value, start, stop, /) -> int: ...


@runtime_checkable
class AddableSequence[T](ProtoSequence[T], Protocol):
    def __add__(self, value): ...


@runtime_checkable
class HashableSequence[T](ProtoSequence[T], SupportsHash, Protocol):
    ...


class HasClass(abc.ABC):
    __class__: type  # Callable[[Any], Any]


class HasSlots(abc.ABC):
    __slots__: tuple


class MultiTypeMeta(type, abc.ABC):
    _TypeArgs = type | tuple[type, ...]
    _TypeChecker = Callable[[Any, _TypeArgs], bool]

    IS_A: _TypeArgs = (object, )
    ISNT_A: _TypeArgs = tuple()

    @staticmethod
    def check(thing: Any, is_if: _TypeChecker,
              is_a: _TypeArgs = IS_A,
              isnt_a: _TypeArgs = ISNT_A) -> bool:
        return is_if(thing, is_a) and not is_if(thing, isnt_a)

    def __instancecheck__(cls, instance: Any) -> bool:
        return cls.check(instance, isinstance, cls.IS_A, cls.ISNT_A)

    def __subclasscheck__(cls, subclass: Any) -> bool:
        return cls.check(subclass, issubclass, cls.IS_A, cls.ISNT_A)


class BytesOrStrMeta(MultiTypeMeta):
    IS_A = (bytes, str, bytearray)


class BytesOrStr(metaclass=BytesOrStrMeta):
    """ Any `bytes`, `str`, or `bytearray` instance is also an instance \
        of the `BytesOrStr` class. """


class PureIterableMeta(MultiTypeMeta):
    IS_A = (Iterable, )
    ISNT_A = (str, bytes, Mapping)


class PureIterable(metaclass=PureIterableMeta):
    """ Iterables that aren't strings, bytes, or Mappings are "Pure." """


class NonTxtColMeta(MultiTypeMeta):
    IS_A = (Collection, )
    ISNT_A = (str, bytes, bytearray)


class Unhashable(MultiTypeMeta):
    ISNT_A = (Hashable, )


class NonTxtCollection(metaclass=NonTxtColMeta):
    """ All Collections except `str`, bytes, & `bytearray` are \
        `NonTxtCollection`s. """


class SkipException(BaseException):
    """ Exception raised by ErrCatcher subclasses to skip a block of code. """
