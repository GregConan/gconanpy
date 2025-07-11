#!/usr/bin/env python3

"""
WrapFunction needs its own file to import ToString which imports MethodWrapper
Greg Conan: gregmconan@gmail.com
Created: 2025-07-09
Updated: 2025-07-09
"""
# Import standard libraries
from collections.abc import Callable, Collection, Container, \
    Hashable, Iterable, Mapping, MutableMapping
import operator
from typing import Any, Literal, NamedTuple, overload

# Import local custom libraries
try:
    from trivial import always_none
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.trivial import always_none


CALL_2ARG = Callable[[Any, Any], Any]
CALL_3ARG = Callable[[Any, Any, Any], Any]


class Methods(NamedTuple):
    get: CALL_2ARG
    has: CALL_2ARG
    set_to: CALL_3ARG

    def lacks(self, an_obj: Any, key: Hashable,
              exclude: Container = set()) -> bool:
        """
        :param key: Hashable
        :param exclude: Container, values to ignore or overwrite. If `a_dict` \
            maps `key` to one, then return True as if `key is not in a_dict`.
        :return: bool, True if `key` is not mapped to a value in `a_dict` or \
            is mapped to something in `exclude`
        """
        return not self.has(an_obj, key) or an_obj[key] in exclude


class Lazily(NamedTuple):

    attribute = Methods(get=getattr, has=hasattr, set_to=setattr)
    item = Methods(get=operator.getitem, has=operator.contains,
                   set_to=operator.setitem)
    _TO_GET = Literal["item", "attribute"]

    @classmethod
    def get(cls, an_obj: Any, key: Hashable,
            get_if_absent: Callable = always_none,
            get_an: _TO_GET = "attribute",
            exclude: Container = set(),
            getter_args: Iterable = tuple(),
            getter_kwargs: Mapping = dict()) -> Any:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from `LazyButHonestDict.lazyget` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to \
            `key` in `a_dict`) will not be returned; instead returning \
            `get_if_absent(*getter_args, **getter_kwargs)`
        """
        meths: Methods = getattr(cls, get_an)
        return get_if_absent(*getter_args, **getter_kwargs) if \
            meths.lacks(an_obj, key, exclude) else meths.get(an_obj, key)

    @classmethod
    def setdefault(cls, an_obj: Any, key: Hashable,
                   get_if_absent: Callable = always_none,
                   get_an: _TO_GET = "attribute",
                   # get_if_present: _2ARG | _3ARG = getitem,
                   getter_args: Iterable = tuple(),
                   getter_kwargs: Mapping = dict(),
                   exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: Container of possible values to replace with \
            `get_if_absent(*getter_args, **getter_kwargs)` and return if \
            they are mapped to `key` in `a_dict`
        """
        meths: Methods = getattr(cls, get_an)
        if meths.lacks(an_obj, key, exclude):
            meths.set_to(an_obj, key, get_if_absent(
                *getter_args, **getter_kwargs))
        return meths.get(an_obj, key)
