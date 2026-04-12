#!/usr/bin/env python3

"""
Docstrings and type hints for the Collection accessor and mutator functions.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-10
Updated: 2026-04-11
"""
# Import standard libraries
from collections.abc import Collection, Iterable
from typing import TypeVar

_C = TypeVar("_C", bound=Collection)
_T = TypeVar("_T")


def add(self: Collection[_T], element: _T, /) -> None:
    """ Append object to the end of the list, or add an element to a set.

    :param self: Collection[_T], list or set to add/append `duck` to.
    :param element: _T, element to add/append to `self`.
    """


def delete(self: Collection[_T], element: _T, /) -> None:
    """ Remove an element from this Collection; it must be a member.

    If the element is not a member, raise a KeyError.

    :param self: Collection[_T] to remove `element` from.
    :param element: _T to remove from `self`.
    """


def difference(self: _C, *others: Iterable) -> _C:
    """ Return the difference of two or more Collections as a new Collection.

    :param self: Collection
    :param *others: Collection, each containing elements to remove from `self`
    :return: Collection, elements in `self` that are not in any `others`
    """


def difference_update(self: Collection[_T], *others: Iterable[_T]) -> None:
    """ Remove all elements of (an)other Collection(s) from this Collection.

    :param self: Collection[_T] to remove all elements of `others` from
    :param *others: Iterable, elements to remove from `self`. 
    """


def discard(self: Collection[_T], element: _T, /) -> None:
    """ Remove an element from `self` if it is a member.

    Unlike `remove()`, the `discard()` method does not raise an exception when
    an element is missing from `self`. 

    :param self: Collection[_T], to remove `element` from
    :param element: _T, item to remove from `self`
    """


def extend(self: Collection[_T], other: Iterable[_T], /) -> None:
    """ Extend list by appending elements from the iterable, or update a set 
    with the union of itself and others. 

    :param self: Collection[_T], list or set to extend or update
    :param other: Iterable[_T], elements to add to `self`
    """


def intersection(self: _C, *others: Iterable) -> _C:
    """ Return the intersection of two `Collection`s as a new `Collection`.

    :param self: _C, a Collection of elements.
    :return: _C, every element that is in `self` and in all of the `others`.
    """


def intersection_update(self: Collection[_T], *others: Iterable[_T]) -> None:
    """ Update a Collection with the intersection of itself and another. 
    :param self: Collection[_T], _description_
    :param *others: Iterable[_T], _description_
    """


def isdisjoint(self: Collection[_T], other: Iterable[_T], /) -> bool:
    """
    :param self: Collection[_T]
    :param other: Iterable[_T]
    :return: bool, True if `self` and `other` have a null intersection (zero
        elements in common); else False.
    """


def issubset(self: Collection[_T], other: Iterable[_T], /) -> bool:
    """
    :param self: Collection[_T]
    :param other: Iterable[_T]
    :return: bool, True if every element in `self` is in `other`; else False.
    """


def issuperset(self: Collection[_T], other: Iterable[_T], /) -> bool:
    """
    :param self: Collection[_T]
    :param other: Iterable[_T]
    :return: bool, True if every element in `other` is in `self`; else False.
    """


def symmetric_difference(self: _C, other: Iterable, /) -> _C:
    """ Return the symmetric difference of two Collections as a new Collection.

    (i.e. all elements that are in exactly one of the sets.) 
    :param self: _C, Collection of elements to return if they aren't in `other`
    :param other: Iterable, elements to return if they aren't in `self`
    :return: _C, all elements that are in exactly one of the `Collection`s.
    """


def symmetric_difference_update(self: Collection[_T], other: Iterable[_T], /
                                ) -> None:
    """ Set `self` to the symmetric difference between itself and another
    `Iterable`. Afterwards, `self` will only contain elements that were either
    in `self` or in `other` but not in both.

    :param self: Collection[_T] to set to the symmetric difference with `other`
    :param other: Iterable[_T]
    """


def union(self: _C, *others: Iterable) -> _C:
    """ Return the combination of `self` and `others` as a new `Collection`. 
    The result has all elements that are in `self` or any of the `others`.

    :param self: _C, elements to add to the resultant Collection
    :param *others: Iterable[_T], elements to add to the resultant Collection
    :return: _C, _description_
    """


append = add
remove = delete
update = extend
xor = symmetric_difference
