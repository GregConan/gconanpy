#!/usr/bin/env python3

"""
Type annotations for custom Mapping base classes in bases.py
Greg Conan: gregmconan@gmail.com
Created: 2026-04-14
Updated: 2026-04-14
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, \
    Iterable, Mapping, MutableMapping, Sequence
import functools
# from numbers import Number
import operator
from typing import Any, cast, Literal, overload, Self, ParamSpec, TypeVar

# Import local custom libraries
try:
    from gconanpy.meta.typeshed import SupportsRichComparison
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from ..meta.typeshed import SupportsRichComparison

# Name of attribute storing names of protected attributes that cannot be
# overwritten by keys accessible through dot notation. Used by
# mapping.dicts.DotDict, mapping.attrmap.AttrMap, and their subclasses.
PROTECTEDS = "__protected_keywords__"

REALNUM = int | float
NUMBER = REALNUM | complex

# Type hint variables
_D = TypeVar("_D")  # for ExcluderMap "default" parameter
_P = ParamSpec("_P")  # for LazyMap lazy getter functions


class InitMutableMap[KT, VT](MutableMapping[KT, VT]):
    def __init__(self, from_map: Mapping[KT, VT] | Iterable[tuple[KT, VT]]
                 | None = None, /, **kwargs: VT) -> None: ...

    def copy(self) -> Self:
        """ `D.copy()` -> a shallow copy of `D`. 

        :return: Self, another instance of this same type of custom \
            dictionary with the same contents.
        """


class ExcluderMap[KT, VT](MutableMapping[KT, VT]):
    """ Custom `MutableMapping` class that adds `exclude=` options to
        `MutableMapping` methods, letting it ignore specified values as if they
        were blank. It also has extended functionality centered around the
        `default=` option, functionality used by various other custom
        `Mapping`s. The `ExcluderMap` can also use `setdefault` on many 
        different elements at once via `setdefaults`.

        `ExcluDict`, `LazyDict`, `ExcludAttrMap`, & `LazyAttrMap` base class.

        All subclasses inheriting this must define a custom `get` method with
        the `exclude` parameter.
    """

    def chain_get(self, keys: Sequence[KT], default: _D = None,
                  exclude: Container[VT] = set()) -> VT | _D:
        """ Return the value mapped to the first key if any, else return
            the value mapped to the second key if any, ... etc. recursively.
            Return `default` if this dict doesn't contain any of the `keys`.

        :param keys: Sequence[KT], keys mapped to the value to return
        :param default: _D: Any, object to return if none of the `keys` are
            in this `ExcluderMap`
        :param exclude: Container[VT], values to ignore or overwrite. If one
            of the `keys` is mapped to a value in `exclude`, then skip that
            key as if `key is not in self`.
        :return: Any, value mapped to the first key (of `keys`) in this mapping
            if any; otherwise `default` if no `keys` are in this mapping.
        """

    def has(self, key: KT, exclude: Container[VT] = set()) -> bool:
        """
        :param key: KT: Hashable
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `self` maps `key` to one, then return False as if \
            `key is not in self`.
        :return: bool, True if `key` is mapped to a value in `self` and \
            is not mapped to anything in `exclude`.
        """

    def has_all(self, keys: Iterable[KT], exclude: Container[VT] = set()
                ) -> bool:
        """
        :param keys: Iterable[KT], keys to find in this `ExcluderMap`.
        :param exclude: Container[VT], values to overlook/ignore such that
            if `self` maps a key to one of those values, then this method
            will return False as if `key is not in self`.
        :return: bool, True if every key in `keys` is mapped to a value that
            is not in `exclude`; else False.
        """

    def missing_keys(self, keys: Iterable[KT], exclude: Container[VT] = set()
                     ) -> Generator[KT, None, None]:
        """
        :param keys: Iterable[KT], keys to find in this `ExcluderMap`.
        :param exclude: Container[VT], values to overlook/ignore such that \
            if `self` maps a key to one of those values, then this method \
            will yield that key as if `key is not in self`.
        :yield: Generator[KT, None, None], all `keys` that either are not in \
            this `ExcluderMap` or are mapped to a value in `exclude`.
        """

    @overload
    def setdefaults(self, **kwargs: VT) -> None: ...
    @overload
    def setdefaults(self, exclude: Container[VT], **kwargs: VT) -> None: ...

    def setdefaults(self, exclude=set(), **kwargs: VT) -> None:
        """ Fill any missing values in self from kwargs.
            `dict.update` prefers to overwrite old values with new ones.
            `setdefaults` is like `update`, but prefers to keep old values.

        :param exclude: Container[VT], values to overlook/ignore such that \
            if `self` maps `key` to one of those values, then this method \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key is not in self`.
        :param kwargs: Mapping[str, Any] of values to add to self if needed.
        """


class LazyMap[KT, VT](ExcluderMap[KT, VT]):
    """ `MutableMapping` that can get/set items and ignore the default
        parameter until/unless it is needed, ONLY evaluating it after failing
        to get/set an existing key. Benefit: The `default=` code does not need
        to be valid (yet) if `self` already has the key. Any function passed to
        a "lazy" method only needs to work if a value is missing.

    Keeps core functionality of the Python `MutableMapping`.
    Extended `LazyButHonestDict` from https://stackoverflow.com/q/17532929 """

    def lazyget(self, key: KT, get_if_absent: Callable[_P, _D],
                exclude: Container[VT] = set(), *args: _P.args,
                **kwargs: _P.kwargs) -> VT | _D:
        """ Adapted from `LazyButHonestDict.lazyget` from \
            https://stackoverflow.com/q/17532929

        :param key: KT, a key this LazyDict might map to the value to return
        :param get_if_absent: Callable that returns the default value
        :param args: Iterable[Any], `get_if_absent` arguments
        :param kwargs: Mapping, `get_if_absent` keyword arguments
        :param exclude: Container[VT] of possible values which (if they are \
            mapped to `key` in `self`) won't be returned; instead returning \
            `get_if_absent(*args, **kwargs)`
        :return: VT, the value that this dict maps to `key`, if that value \
            isn't in `exclude`; else `return get_if_absent(*args, **kwargs)`
        """

    def lazysetdefault(self, key: KT, get_if_absent: Callable[_P, VT],
                       exclude: Container[VT] = set(),
                       *args: _P.args, **kwargs: _P.kwargs) -> VT:
        """ Return the value for key if key is in this `LazyDict` and not \
            in `exclude`; else add that key to this `LazyDict`, set its \
            value to `get_if_absent(*args, **kwargs)`, and then return that.

        Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: KT, a key this LazyDict might map to the value to return
        :param get_if_absent: Callable, function to set & return default value
        :param args: Iterable[Any], `get_if_absent` arguments
        :param kwargs: Mapping, `get_if_absent` keyword arguments
        :param exclude: Container[VT] of possible values to replace with \
            `get_if_absent(*args, **kwargs)` and return if \
            they are mapped to `key` in `self` but not in `exclude`
        :return: VT, the value that this dict maps to `key`, if that value \
            isn't in `exclude`; else `return get_if_absent(*args, **kwargs)`
        """


# TODO Why does `VT: numbers.Number` make MathMap[str, int] raise warnings?
class MathMap[KT, VT: NUMBER](InitMutableMap[KT, VT]):
    """ `dict` that can perform math operations on its items. For example:

    ```
    MathDict(a=4, b=3) + MathDict(a=2, b=1) = MathDict(a=6, b=4)
    MathDict(a=4, b=3) - MathDict(a=2, b=0) = MathDict(a=2, b=3)
    MathDict(a=4, b=3) * MathDict(a=2, b=3) = MathDict(a=8, b=9)
    MathDict(a=4, b=3) / MathDict(a=2, b=3) = MathDict(a=2, b=1)
    ```

    Etc. All basic operations are supported:

    - Basic arithmetic: add (`+`), divide (`/`), multiply (`*`), subtract (`-`)
    - Bit shifting: left (`<<`) and right (`>>`)
    - Comparison: equal (`==`), greater or equal (`>=`), greater (`>`), less
        or equal (`<=`), less (`<`), and unequal (`!=`)
    - Division precisely: floor (`//`), modulo (`%`)
    - Exponentiation: power (`**`)
    - Sign: absolute value (`abs`), negative (`-`), positive (`+`)

    Additional operations currently include: averaging (`avg`) 

    Missing items are treated as `0` or `1`, whichever is least affected by 
    the operation. If any item is missing from `self` or from the other
    `Mapping`(s), then by default,

    - `add`, `avg`, `lshift`, `mul`, `rshift`, and `sub` will always use `0`.
    - `div`, `floordiv`, `mod`, and `pow` will use `0` for values missing from
      `self` and `1` for values missing from `other`, partly to prevent
       divide-by-zero errors.
    """

    def __abs__(self) -> Self: ...
    def __add__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __div__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __floordiv__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __lshift__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __mod__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __mul__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __neg__(self) -> Self: ...
    def __pos__(self) -> Self: ...
    def __pow__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __rshift__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __sub__(self, other: VT | Mapping[KT, VT]) -> Self: ...
    def __truediv__(self, other: VT | Mapping[KT, VT]) -> Self: ...

    def avg(self, *others: VT | Mapping[KT, VT]) -> Self:
        """ Take the average of (every value in) this `MathDict` with 
            other values and/or with (every value in) other `MathDict`s.

        :param others: VT | Mapping[KT, VT], other values to average this 
            `MathDict`'s values with.
        :return: Self, a `MathDict` where every value is the average of
            this `MathDict` and all `others`.
        """
        return functools.reduce(operator.add, (self, *others)
                                ) / (len(others) + 1)


class ComparableMathMap[KT, VT: REALNUM](Mapping[KT, VT]):
    def __ge__(self, other: VT | Mapping[KT, VT]) -> dict[KT, bool]: ...
    def __gt__(self, other: VT | Mapping[KT, VT]) -> dict[KT, bool]: ...
    def __le__(self, other: VT | Mapping[KT, VT]) -> dict[KT, bool]: ...
    def __lt__(self, other: VT | Mapping[KT, VT]) -> dict[KT, bool]: ...


class PromptMap[KT, VT](LazyMap[KT, VT]):
    """ LazyMap able to interactively prompt the user to fill missing values.
    """

    def get_or_prompt_for(self, key: KT, prompt: str,
                          prompt_fn: Callable[[str], str] = input,
                          exclude: Container[VT] = set()) -> VT | str:
        """ Return the value mapped to key in self if one already exists and \
            is not in `exclude`; else prompt the user to interactively \
            provide it and return that.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `self` maps `key` to one, prompt the user as if \
            `key is not in self`.
        :return: Any, the value mapped to `key` if one exists, else the \
                 value that the user interactively provided
        """

    def setdefault_or_prompt_for(self, key: KT, prompt: str,
                                 prompt_fn: Callable[[str], VT] = input,
                                 exclude: Container[VT] = set()) -> VT:
        """ Return the value mapped to key in self if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, prompt the user as if `key is not in self`.
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """


class SortMap[KT: SupportsRichComparison, VT: SupportsRichComparison
              ](MutableMapping[KT, VT]):
    """ Custom MutableMapping class that can yield a generator of its
        key-value pairs sorted in order of either keys or values. """
    _BY = Literal["keys", "values"]
    _WHICH: dict[_BY, operator.itemgetter] = {"keys": operator.itemgetter(0),
                                              "values": operator.itemgetter(1)}

    def sorted_by(self, by: _BY, descending: bool = False
                  ) -> Generator[tuple[KT, VT], None, None]:
        """ Adapted from https://stackoverflow.com/a/50569360

        :param by: Literal["keys", "values"], "keys" to yield key-value \
            pairings sorted by keys; else "values" to sort them by values
        :param descending: bool, True to yield the key-value pairings with \
            the largest ones first; else False to yield the smallest first; \
            defaults to False
        :yield: Generator[tuple[KT, VT], None, None], each key-value pairing \
            in this Sortionary as a tuple, sorted `by` keys or values in \
            ascending or `descending` order
        """
