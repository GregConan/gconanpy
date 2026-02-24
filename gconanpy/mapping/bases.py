#!/usr/bin/env python3

"""
Custom Mapping base classes inherited by classes in dicts.py and attrmap.py
Greg Conan: gregmconan@gmail.com
Created: 2026-02-23
Updated: 2026-02-23
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, \
    Iterable, Mapping, MutableMapping, Sequence
import functools
from numbers import Number
import operator
from typing import cast, Literal, overload, Self, ParamSpec, TypeVar

# Import local custom libraries
try:
    from gconanpy.meta.typeshed import SupportsRichComparison
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from meta.typeshed import SupportsRichComparison

# Constants for MathDict: numerical type hint, functools.wraps(assigned=...
_ASSIGNED = ("__doc__", "__name__", "__qualname__")
_NUM = int | float | complex

# Name of attribute storing names of protected attributes that cannot be
# overwritten by keys accessible through dot notation. Used by
# mapping.dicts.DotDict, mapping.attrmap.AttrMap, and their subclasses.
PROTECTEDS = "__protected_keywords__"

# Type hint variables
_D = TypeVar("_D")  # for ExcluderMap "default" parameter
_P = ParamSpec("_P")  # for LazyMap lazy getter functions


class InitMutableMap[KT, VT](MutableMapping[KT, VT]):
    def __init__(self, from_map: Mapping[KT, VT] | Iterable[tuple[KT, VT]]
                 | None = None) -> None:
        if from_map:
            self.update(from_map)

    def copy(self) -> Self:
        """ `D.copy()` -> a shallow copy of `D`. 

        :return: Self, another instance of this same type of custom \
            dictionary with the same contents.
        """
        return self.__class__(self)


class ExcluderMap[KT, VT](MutableMapping[KT, VT]):
    """ Custom `MutableMapping` class that adds `exclude=` options to
        `MutableMapping` methods, letting it ignore specified values as if they
        were blank. It also has extended functionality centered around the
        `default=` option, functionality used by various other custom
        `Mapping`s. The `ExcluderMap` can also use `setdefault` on many 
        different elements at once via `setdefaults`.
        `ExcluderMap` and `LazyDict` base class.
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
        for key in keys:
            if self.has(key, exclude):
                return self[key]
        return default

    def get(self, key: KT, default: _D = None,
            exclude: Container[VT] = set()) -> VT | _D:
        """ Return the value mapped to `key` in `self`, if any; else return \
            `default`. Defined to add `exclude` option to `dict.get`.

        :param key: KT: Hashable, key mapped to the value to return
        :param default: _D: Any, object to return `if not self.has` the key, \
            i.e. `if key not in self or self[key] in exclude`
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, then return True as if `key is not in self`.
        :return: VT | _D, value `self` maps to `key` if any; else `default`
        """
        return self[key] if self.has(key, exclude) else default

    def has(self, key: KT, exclude: Container[VT] = set()) -> bool:
        """
        :param key: KT: Hashable
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `self` maps `key` to one, then return False as if \
            `key is not in self`.
        :return: bool, True if `key` is mapped to a value in `self` and \
            is not mapped to anything in `exclude`.
        """
        try:  # If we have the key, return True unless its value doesn't count
            return self[key] not in exclude

        except KeyError:  # If we don't have the key, return False
            return False

        # `self[key] in exclude` raises TypeError if self[key] isn't Hashable.
        # In that case, self[key] can't be in exclude, so self has key.
        except TypeError:
            return True

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
        try:
            next(self.missing_keys(keys, exclude))
            return False
        except StopIteration:
            return True

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
        if exclude:
            for key in keys:
                if not self.has(key, exclude):
                    yield key
        else:
            for key in keys:
                if key not in self:
                    yield key

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
        for key in self.missing_keys(cast(Iterable[KT], kwargs), exclude):
            self[key] = kwargs[cast(str, key)]


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
        return self[key] if self.has(key, exclude) else \
            get_if_absent(*args, **kwargs)

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
        if not self.has(key, exclude):
            self[key] = get_if_absent(*args, **kwargs)
        return self[key]


class MathMap[KT: Hashable, VT: Number](InitMutableMap[KT, VT]):
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
    # Numerical argument default value type hint acceptable by type checker
    _ZERO = cast(VT, 0)

    @staticmethod
    def _math_meth_1_arg(func: Callable[[_NUM], _NUM]):
        """ Given a basic math operation, return a `MathDict` dunder method
            that does that operation on every value in this `MathDict`.

        :param func: Callable[[VT: Number], VT], a function that accepts
            one number, does a basic math operation on it, and returns
            another number (the result of that operation).
        :return: Callable[[Self], Self], a (dunder) method to run
            `func` on for every value in this `MathDict`.
        """
        @functools.wraps(func, assigned=_ASSIGNED)
        def wrapper(self: Self) -> Self:
            return type(self)({k: cast(VT, func(cast(_NUM, v)))
                               for k, v in self.items()})
        return wrapper

    @staticmethod
    def _math_meth_2_args(func: Callable[[VT, VT], VT],
                          default_self: VT = _ZERO, default_other: VT = _ZERO):
        # No return type hint because it'd include unparsable Self type
        """ Given a basic math operation, return a `MathDict` dunder method
            that does that operation on every value in this `MathDict`.

        :param func: Callable[[VT: Number, VT], VT], a function that accepts
            two numbers, does a basic math operation using them, and returns
            one number (the result of that operation).
        :param default_self: VT, the first argument to run `func` with when
            the value is in the other `Mapping`(s) but missing from `self`.
        :param default_other: VT, the second argument to run `func` with when
            the value is in `self` but missing from the other `Mapping`(s).
        :return: Callable[[Self, VT | Mapping[KT, VT]], Self], a (dunder) 
            method to run `func` on for every value in this `MathDict`.
        """
        @functools.wraps(func, assigned=_ASSIGNED)
        def wrapper(self: Self, other: VT | Mapping[KT, VT]) -> Self:
            newMD = type(self)()
            if isinstance(other, Mapping):
                for k in self.keys() | other.keys():
                    newMD[k] = func(self.get(k, default_self),
                                    other.get(k, default_other))
            else:
                for k, v in self.items():
                    newMD[k] = func(v, other)
            return newMD
        return wrapper

    __abs__ = _math_meth_1_arg(operator.abs)
    __add__ = _math_meth_2_args(operator.add)
    __div__ = __truediv__ = _math_meth_2_args(operator.truediv, 0, 1)
    # __eq__ = _math_meth_2_args(operator.eq)  # Unneeded; default dict method
    __floordiv__ = _math_meth_2_args(operator.floordiv, 0, 1)
    __ge__ = _math_meth_2_args(operator.ge)
    __gt__ = _math_meth_2_args(operator.gt)
    __le__ = _math_meth_2_args(operator.le)
    __lshift__ = _math_meth_2_args(operator.lshift)
    __lt__ = _math_meth_2_args(operator.lt)
    __mod__ = _math_meth_2_args(operator.mod, 0, 1)
    __mul__ = _math_meth_2_args(operator.mul)
    # __ne__ = _math_meth_2_args(operator.ne)  # Unneeded; default dict method
    __neg__ = _math_meth_1_arg(operator.neg)
    __pos__ = _math_meth_1_arg(operator.pos)
    __pow__ = _math_meth_2_args(operator.pow, 0, 1)
    __rshift__ = _math_meth_2_args(operator.rshift)
    __sub__ = _math_meth_2_args(operator.sub)

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
        return self.lazyget(key, prompt_fn, exclude, prompt)

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
        return self.lazysetdefault(key, prompt_fn, exclude, prompt)


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
        for k, v in sorted(self.items(), key=self._WHICH[by],
                           reverse=descending):
            yield (k, v)
