#!/usr/bin/env python3

"""
Item/attribute accessor functions/classes more broadly usable than builtins.
Expanding Python's built-in accessor (getter/setter/deleter/etc) functions \
    for use on more kinds of objects.
Greg Conan: gregmconan@gmail.com
Created: 2025-09-11
Updated: 2025-11-03
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, \
    Iterable, Mapping, MutableMapping, MutableSequence, Sequence
import operator
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, cast, NamedTuple, overload, ParamSpec, TypeVar

try:
    from gconanpy.meta.typeshed import \
        DATA_ERRORS, SupportsGetItem, SupportsItemAccess
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from meta.typeshed import DATA_ERRORS, SupportsGetItem, SupportsItemAccess

# TypeVars for (g/s)etdefault and Accessor class methods' input parameters
_D = TypeVar("_D")  # "default"
_T = TypeVar("_T")  # "obj" (when returning the same input object)
_KT = TypeVar("_KT", bound=Hashable)  # keys
_P = ParamSpec("_P")  # for Accessor lazy methods
_S = TypeVar("_S", bound=SupportsItemAccess)
_VT = TypeVar("_VT")  # values

# Specify how many input parameters each Accessor input arg function takes
CALL_2ARG = Callable[[Any, Any], Any]
CALL_3ARG = Callable[[Any, Any, Any], Any]


@overload
def getdefault(o: Mapping[_KT, _VT], key: _KT) -> _VT | None: ...
@overload
def getdefault(o: Mapping[_KT, _VT], key: _KT, default: _D) -> _VT | _D: ...
@overload
def getdefault(o: Sequence[_VT], key: int) -> _VT | None: ...
@overload
def getdefault(o: Sequence[_VT], key: int, default: _D) -> _VT | _D: ...


def getdefault(o: SupportsGetItem, key: Hashable, default: Any = None):
    """ Return the value for `key` if `key` is in `o`, else `default`.

    Same as `dict.get`, but can also be used on `MutableSequence`s \
    such as `list`s.

    :param o: SupportsGetItem[_VT: Any], object with a `__getitem__` method
    :param key: _KT: Hashable, key to try to retrieve the mapped value of
    :param default: _D: Any, value to return if `key` isn't in `o`; \
        defaults to None
    :return: _VT | _D, the value `o` maps to `key`, if any; else `default`
    """
    try:
        return o[key]
    except KeyError:
        return default


@overload
def fill_replace(o: MutableMapping[_KT, _VT], fill_with: Any,
                 replace: Container[_VT]) -> None: ...


@overload
def fill_replace(o: MutableSequence[_VT], fill_with: Any,
                 replace: Container[_VT]) -> None: ...


def fill_replace(o: SupportsItemAccess, fill_with, replace) -> None:
    # First, get a generator to yield key-value pairs for a Mapping OR
    # index-value pairs for a Sequence
    try:
        pair_generator = cast(Mapping, o).items()
    except AttributeError:
        pair_generator = enumerate(cast(Sequence, o))

    # Then, iterate the entire object to collect keys/indices to replace.
    # Must iterate BEFORE replacing because items() can't do both at once.
    keys_to_replace = tuple(k for k, v in pair_generator if v in replace)

    # Finally, make all of the replacements.
    for key in keys_to_replace:
        o[key] = fill_with


@overload
def setdefault(o: MutableMapping[_KT, _VT], key: _KT, default: _D
               ) -> _VT | _D: ...


@overload
def setdefault(o: MutableSequence[_VT], key: int, default: _D
               ) -> _VT | _D: ...


def setdefault(o: SupportsItemAccess, key, default=None):
    """ Return the value for key if key is in `o`; else add \
        that key to `o` with the value `default` and return `default`.

    Same as `dict.setdefault`, but can also be used on `MutableSequence`s \
    such as `list`s.

    :param o: SupportsItemAccess[_VT: Any], object with `__getitem__`, \
        `__setitem__`, and `__delitem__` methods
    :param key: _KT: Hashable, key to retrieve (or set) the mapped value of
    :param default: _D: Any, value to map `key` to in `o` if none exists; \
        defaults to None
    :return: _VT | _D, the value that `o` now maps to `key`
    """
    try:
        return o[key]
    except KeyError:
        o[key] = default
        return default


class Accessor[KT, VT](NamedTuple):
    contains: CALL_2ARG    # hasattr or operator.contains
    delete: CALL_2ARG      # delattr or operator.delitem
    get: CALL_2ARG         # getattr or operator.getitem
    set_to: CALL_3ARG      # setattr or operator.setitem
    MissingError: type[BaseException]  # AttributeError or KeyError

    def chain_get(self, obj: Mapping[KT, VT] | Any, keys: Sequence[KT],
                  default: _D = None, exclude: Container[VT] = set()
                  ) -> VT | _D:
        """ Return the value mapped to the first key if any, else return \
            the value mapped to the second key if any, ... etc. recursively. \
            Return `default` if `obj` doesn't contain any of the `keys`.

        :param obj: Mapping[KT: Hashable, VT: Any] | Any
        :param keys: Sequence[KT], keys mapped to the value to return
        :param default: _D: Any, object to return if no `keys` are in `obj`
        :param exclude: Container[VT], values to ignore or overwrite. \
            If one of the `keys` is mapped to a value in `exclude`, then skip \
            that key as if it is not in `obj`.
        :return: KT | _D, value mapped to the first key (of `keys`) in `obj` \
            if any; otherwise `default` if none of the `keys` are in `obj`.
        """
        for key in keys:
            if self.has(obj, key, exclude):
                return self.get(obj, key)
        return default

    def get_or_prompt_for(self, obj: Mapping[KT, VT] | Any, key: KT,
                          prompt: str, prompt_fn: Callable[[str], str] = input,
                          exclude: Container[VT] = set()) -> VT | str:
        """ Return the value mapped to `key` in `obj` if one already exists \
            and is not in `exclude`; else prompt the user to interactively \
            provide it and return that.

        :param obj: Mapping[KT: Hashable, VT: Any] | Any, _description_
        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                            get a string, like `input` or `getpass.getpass`.
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `obj` maps `key` to one, prompt the user as if `key` is not in \
            `obj`.
        :return: Any, the value mapped to key if one exists, else the value \
            that the user interactively provided
        """
        return self.lazyget(obj, key, prompt_fn, exclude, prompt)

    def get_subset_from_lookups(self, obj: Mapping[str, VT] | Any,
                                to_look_up: Mapping[str, str],
                                sep: str = ".", default: _D = None
                                ) -> dict[str, VT | _D]:
        """ `get_subset_from_lookups(obj, {"a": "b/c"}, sep="/")` \
            -> `{"a": obj["b"]["c"]}` or `{"a": obj.b.c}

        :param obj: Mapping[str, _VT: Any] | Any to return a dict subset of
        :param to_look_up: Mapping[str, str] of every key to put in the \
            returned dict to the path to its value in `obj`
        :param sep: str, separator between subkeys in `to_look_up.values()`; \
            defaults to "."
        :param default: _D: Any, value to map to any keys not found in `obj`; \
            defaults to None
        :return: dict[str, _VT | _D] mapping every key in `to_look_up` to the \
            value at its mapped path in `obj`
        """
        return {key: self.lookup(obj, path, sep, default)
                for key, path in to_look_up.items()}

    def getdefault(self, obj: Any, key: KT, value: _D,
                   exclude: Container = set()) -> Any | _D:
        try:  # If obj has the attribute, return it unless its value is excluded
            gotten = self.get(obj, key)
            assert gotten not in exclude

        # If obj lacks the attribute, return the default value
        except (AssertionError, self.MissingError):
            gotten = value

        # `obj.<name> in exclude` raises TypeError if obj.<name> isn't Hashable.
        # In that case, obj.<name> can't be in exclude, so obj has name.
        except TypeError:
            pass

        return gotten

    def has(self, obj: Mapping[KT, VT] | Any, key: KT,
            exclude: Container[VT] = set()) -> bool:
        """ Check whether `key` is in `obj` as an item or attribute. \
            Defined to add `exclude` option.

        :param key: KT: Hashable
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `obj` maps `key` to one, then return False as if `obj` does not \
            contain `key`.
        :return: bool, True if `key` is not mapped to a value in `obj` or \
            is mapped to something in `exclude`
        """
        try:  # If obj has key, return True iff its value doesn't count
            return self.get(obj, key) not in exclude

        except self.MissingError:  # If obj lacks key return False
            return False

        # `self.<name> in exclude` raises TypeError if self.<name> isn't Hashable.
        # In that case, self.<name> can't be in exclude, so obj has name.
        except TypeError:
            return True

    def has_all(self, obj: Mapping[KT, VT] | Any,
                keys: Iterable[KT], exclude: Container[VT] = set()
                ) -> bool:
        """
        :param obj: Mapping[KT, VT] to check whether it contains all `keys`.
        :param keys: Iterable[_K], keys to find in `obj`.
        :param exclude: Container[VT], values to overlook/ignore such that if \
            `obj` maps a key to one of those values, then this function \
            will return False as if `key is not in obj`.
        :return: bool, True if every key in `keys` is mapped to a value that \
            is not in `exclude`; else False.
        """
        try:
            next(self.missing_keys(obj, keys, exclude))
            return False
        except StopIteration:
            return True

    def lazyget(self, obj: Mapping[KT, VT] | Any, key: KT,
                get_if_absent: Callable[_P, _D],
                exclude: Container[VT] = set(),
                *args: _P.args, **kwargs: _P.kwargs) -> VT | _D:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from `LazyButHonestDict.lazyget` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param args: Iterable[Any] of get_if_absent arguments
        :param kwargs: Mapping of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to \
            `key` in `a_dict`) will not be returned; instead returning \
            `get_if_absent(*args, **kwargs)`
        """
        return get_if_absent(*args, **kwargs) if not \
            self.has(obj, key, exclude) else self.get(obj, key)

    def lazysetdefault(self, obj: Mapping[KT, VT] | Any, key: KT,
                       get_if_absent: Callable[_P, _D],
                       exclude: Container[VT] = set(),
                       *args: _P.args, **kwargs: _P.kwargs) -> VT | _D:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param args: Iterable[Any] of get_if_absent arguments
        :param kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: Container of possible values to replace with \
            `get_if_absent(*args, **kwargs)` and return if \
            they are mapped to `key` in `a_dict`
        """
        if not self.has(obj, key, exclude):
            new_value = get_if_absent(*args, **kwargs)
            self.set_to(obj, key, new_value)
            return new_value
        else:
            return self.get(obj, key)

    def lookup(self, obj: Mapping[KT, VT] | Any, path: str,
               sep: str = ".", default: _D = None) -> VT | _D:
        """ Get the value mapped to a key in nested structure. Adapted from \
            https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param obj: Mapping[KT: Hashable, VT: Any] to find a value in
        :param path: str, path to key in nested structure, e.g. "a.b.c"
        :param sep: str, separator between keys in path; defaults to "."
        :param default: Any, value to return if key is not found
        :return: VT | _D, the value mapped to the nested key if any, else default
        """
        keypath = list(reversed(path.split(sep)))
        retrieved = obj
        try:
            while keypath:
                key = keypath.pop()
                try:
                    retrieved = self.get(retrieved, key)
                except KeyError:
                    retrieved = self.get(retrieved, int(key))

        # If value is not found, then return the default value
        except DATA_ERRORS:
            retrieved = default
        return default if keypath else cast(VT, retrieved)

    def missing_keys(self, obj: Mapping[KT, VT] | Any,
                     keys: Iterable[KT], exclude: Container[VT] = set()
                     ) -> Generator[KT, None, None]:
        """
        :param obj: Mapping[KT: Hashable, VT: Any] | Any, _description_
        :param keys: Iterable[KT], keys to find in `obj`
        :param exclude: Container[VT], values to overlook/ignore such that if \
            `obj` maps a key to one of those values, then this function \
            will yield that key as if `key` is not in `obj`.
        :yield: Generator[KT, None, None], all `keys` that either are not in \
            `obj` or are mapped to a value in `exclude`.
        """
        if exclude:
            for key in keys:
                if not self.has(obj, key, exclude):
                    yield key
        else:
            for key in keys:
                if not self.contains(obj, key):
                    yield key

    def setdefault(self, obj: MutableMapping[KT, VT] | Any, key: KT,
                   value: _D, exclude: Container = set()) -> VT | _D:
        """ Return the value for key if key is in `obj`; else add \
            that key to `obj`, set it to value, and return it

        :param key: KT: Hashable to use as a key to map to value
        :param value: _type_, _description_
        """
        gotten = self.getdefault(obj, key, value, exclude)
        if gotten is value:
            self.set_to(obj, key, value)
        return gotten

    def setdefault_or_prompt_for(self, obj: Mapping[KT, VT] | Any, key: KT,
                                 prompt: str, prompt_fn: Callable[[str], str]
                                 = input, exclude: Container[VT] = set()
                                 ) -> VT | str:
        """ Return the value mapped to key in `obj` if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `obj` \
            maps `key` to one, prompt the user as if `key is not in obj`.
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazysetdefault(obj, key, prompt_fn, exclude, prompt)

    def setdefaults(self, obj: MutableMapping[KT, VT] | _T,
                    exclude: Container[VT] = set(),
                    **kwargs: Any) -> MutableMapping[KT, VT] | _T:
        """ Fill any missing values in obj from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param obj: MutableMapping[KT: Hashable, VT: Any] | _T: Any, \
            _description_
        :param exclude: Container[VT], values to overlook/ignore such that \
            if `obj` maps `key` to one of those values, then this function \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key` is not in `obj`.
        :param kwargs: Mapping[str, VT] of values to add to `obj` if needed.
        :return: MutableMapping[KT, VT] | _T
        """
        for key in self.missing_keys(obj, cast(Iterable[KT], kwargs), exclude):
            self.set_to(obj, key, kwargs[cast(str, key)])
        return obj


ACCESS_ITEM = Accessor(
    contains=operator.contains, get=operator.getitem,
    set_to=operator.setitem, delete=operator.delitem,
    MissingError=KeyError)
ACCESS_ATTR = Accessor(contains=hasattr, get=getattr,
                       set_to=setattr, delete=delattr,
                       MissingError=AttributeError)


class Access:
    item = ACCESS_ITEM
    attribute = ACCESS_ATTR


# TODO REMOVE(?) bc it's slightly slower & using it is less concise?
# Change to frozendict so it's a global constant (& maybe faster?)
# https://github.com/Marco-Sulla/python-frozendict/issues/18
ACCESS = {"item": ACCESS_ITEM, "attribute": ACCESS_ATTR}
