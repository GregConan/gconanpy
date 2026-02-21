#!/usr/bin/env python3

"""
Item/attribute accessor functions/classes more broadly usable than builtins.
Expanding Python's built-in accessor (getter/setter/deleter/etc) functions 
    for use on more kinds of objects.
Greg Conan: gregmconan@gmail.com
Created: 2025-09-11
Updated: 2026-02-20
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, \
    Iterable, Mapping, MutableMapping, MutableSequence, Sequence
import operator
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, cast, NamedTuple, overload, ParamSpec, TypeVar

try:
    from gconanpy.mapping.attrmap import AttrMap
    from gconanpy.meta.typeshed import \
        DATA_ERRORS, SupportsGetItem, SupportsItemAccess
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from mapping.attrmap import AttrMap
    from meta.typeshed import DATA_ERRORS, SupportsGetItem, SupportsItemAccess

# TypeVars for (g/s)etdefault and Accessor class methods' input parameters
_D = TypeVar("_D")  # "default"
_T = TypeVar("_T")  # "obj" (when returning the same input object)
_KT = TypeVar("_KT", bound=Hashable)  # keys
_P = ParamSpec("_P")  # for Accessor lazy methods
_S = TypeVar("_S", bound=SupportsItemAccess)
_VT = TypeVar("_VT")  # values

# Type hint constants
STR2STR = Mapping[str, str]

# Specify how many input parameters each Accessor input arg function takes
CALL_2ARG = Callable[[Any, Any], Any]
CALL_3ARG = Callable[[Any, Any, Any], Any]


@overload
def getdefault(o: Mapping[_KT, _VT], /, key: _KT) -> _VT | None: ...
@overload
def getdefault(o: Mapping[_KT, _VT], /, key: _KT, default: _D) -> _VT | _D: ...
@overload
def getdefault(o: Sequence[_VT], /, key: int) -> _VT | None: ...
@overload
def getdefault(o: Sequence[_VT], /, key: int, default: _D) -> _VT | _D: ...
@overload
def getdefault(o: SupportsGetItem, /, key: Hashable, default: Any) -> Any: ...


def getdefault(o, /, key, default=None):
    """ Return the value for `key` if `key` is in `o`, else `default`.

    Same as `dict.get`, but can also be used on `MutableSequence`s 
    such as `list`s.

    :param o: SupportsGetItem[_VT: Any], object with a `__getitem__` method
    :param key: _KT: Hashable, key to try to retrieve the mapped value of
    :param default: _D: Any, value to return if `key` isn't in `o`; 
        defaults to None
    :return: _VT | _D, the value `o` maps to `key`, if any; else `default`
    """
    try:
        return o[key]
    except KeyError:
        return default


def fill_replace(obj: _S, fill_with: Any, to_replace: Container) -> _S:
    # First, get a generator to yield key-value pairs for a Mapping OR
    # index-value pairs for a Sequence
    try:
        pair_generator = cast(Mapping, obj).items()
    except AttributeError:
        pair_generator = enumerate(cast(Sequence, obj))

    # Then, iterate the entire object to collect keys/indices to replace.
    # Must iterate BEFORE replacing because items() can't do both at once.
    keys_to_replace = tuple(k for k, v in pair_generator if v in to_replace)

    # Finally, make all of the replacements.
    for key in keys_to_replace:
        obj[key] = fill_with
    return obj


@overload
def setdefault(o: MutableMapping[_KT, _VT], /, key: _KT, default: _D = None
               ) -> _VT | _D: ...


@overload
def setdefault(o: MutableSequence[_VT], /, key: int, default: _D = None
               ) -> _VT | _D: ...


@overload
def setdefault(o: SupportsItemAccess, /, key: Any, default: _D = None
               ) -> _D | Any: ...


def setdefault(o, /, key, default=None):
    """ Return the value for key if key is in `o`; else add 
        that key to `o` with the value `default` and return `default`.

    Same as `dict.setdefault`, but can also be used on `MutableSequence`s 
    such as `list`s.

    :param o: SupportsItemAccess[_VT: Any], object with `__getitem__`, 
        `__setitem__`, and `__delitem__` methods
    :param key: _KT: Hashable, key to retrieve (or set) the mapped value of
    :param default: _D: Any, value to map `key` to in `o` if none exists; 
        defaults to None
    :return: _VT | _D, the value that `o` now maps to `key`
    """
    try:
        return o[key]
    except KeyError:
        o[key] = default
        return default


class Accessor(NamedTuple):
    contains: Callable[[Any, Any], bool]    # hasattr or operator.contains
    delete:  Callable[[Any, Any], None]     # delattr or operator.delitem
    get: Callable[[Any, Any], Any]          # getattr or operator.getitem
    set_to: Callable[[Any, Any, Any], Any]  # setattr or operator.setitem
    MissingError: type[BaseException]       # AttributeError or KeyError

    @overload
    def chain_get(self, obj: Mapping[_KT, _VT], /, keys: Sequence[_KT],
                  default: _D = None, exclude: Container[_VT] = set()
                  ) -> _VT | _D: ...

    @overload
    def chain_get(self, obj: Any, /, keys: Sequence[str],
                  default: Any = None, exclude: Container = set()
                  ) -> Any: ...

    def chain_get(self, obj, /, keys, default=None, exclude=set()):
        """ Return the value mapped to the first key if any, else return 
            the value mapped to the second key if any, ... etc. recursively. 
            Return `default` if `obj` doesn't contain any of the `keys`.

        :param obj: Mapping[_KT: Hashable, _VT: Any] | Any
        :param keys: Sequence[_KT], keys mapped to the value to return
        :param default: _D: Any, object to return if no `keys` are in `obj`
        :param exclude: Container[_VT], values to ignore or overwrite. 
            If one of the `keys` is mapped to a value in `exclude`, then skip 
            that key as if it is not in `obj`.
        :return: _KT | _D, value mapped to the first key (of `keys`) in `obj` 
            if any; otherwise `default` if none of the `keys` are in `obj`.
        """
        for key in keys:
            if self.has(obj, key, exclude):
                return self.get(obj, key)
        return default

    @overload
    def get_or_prompt_for(self, obj: Mapping[_KT, _VT], /, key: _KT,
                          prompt: str, prompt_fn: Callable[[str], str] = input,
                          exclude: Container[_VT] = set()) -> _VT | str: ...

    @overload
    def get_or_prompt_for(self, obj: Any, /, key: str,
                          prompt: str, prompt_fn: Callable[[str], str] = input,
                          exclude: Container = set()) -> Any: ...

    def get_or_prompt_for(self, obj, /, key, prompt, prompt_fn=input,
                          exclude=set()):
        """ Return the value mapped to `key` in `obj` if one already exists 
            and is not in `exclude`; else prompt the user to interactively 
            provide it and return that.

        :param obj: Mapping[_KT: Hashable, _VT: Any] | Any, _description_
        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to 
                            get a string, like `input` or `getpass.getpass`.
        :param exclude: Container[_VT], values to ignore or overwrite. If 
            `obj` maps `key` to one, prompt the user as if `key` is not in 
            `obj`.
        :return: Any, the value mapped to key if one exists, else the value 
            that the user interactively provided
        """
        return self.lazyget(obj, key, prompt_fn, exclude, prompt)

    @overload
    def get_subset_from_lookups(self, obj: Mapping[str, _VT], /,
                                to_look_up: STR2STR, sep: str = ".",
                                default: _D = None) -> dict[str, _VT | _D]: ...

    @overload
    def get_subset_from_lookups(self, obj: Any, /,
                                to_look_up: STR2STR, sep: str = ".",
                                default: Any = None) -> dict[str, Any]: ...

    def get_subset_from_lookups(self, obj, /, to_look_up: STR2STR, sep=".",
                                default=None):
        """ `get_subset_from_lookups(obj, {"a": "b/c"}, sep="/")` 
            -> `{"a": obj["b"]["c"]}` or `{"a": obj.b.c}

        :param obj: Mapping[str, _VT: Any] | Any to return a dict subset of
        :param to_look_up: Mapping[str, str] of every key to put in the 
            returned dict to the path to its value in `obj`
        :param sep: str, separator between subkeys in `to_look_up.values()`; 
            defaults to "."
        :param default: _D: Any, value to map to any keys not found in `obj`; 
            defaults to None
        :return: dict[str, _VT | _D] mapping every key in `to_look_up` to the 
            value at its mapped path in `obj`
        """
        return {key: self.lookup(obj, path, sep, default)
                for key, path in to_look_up.items()}

    @overload
    def getdefault(self, obj: Mapping[_KT, _VT], key: _KT, /, value: _D = None,
                   exclude: Container[_VT] = set()) -> _VT | _D: ...

    @overload
    def getdefault(self, obj: Any, key: str, /, value: Any = None,
                   exclude: Container = set()) -> Any: ...

    def getdefault(self, obj, key, /, value=None, exclude=set()):
        # If obj has the attribute, return it unless its value is excluded
        try:
            gotten = self.get(obj, key)
            assert gotten not in exclude

        # If obj lacks the attribute, return the default value
        except (AssertionError, self.MissingError):
            gotten = value

        # `assert gotten not in exclude` raises TypeError if gotten isn't
        # Hashable. In that case, gotten can't be in exclude, so obj has key.
        except TypeError:
            pass

        return gotten

    @overload
    def has(self, obj: Mapping[_KT, _VT], /, key: _KT,
            exclude: Container[_VT] = set()) -> bool: ...

    @overload
    def has(self, obj: Any, /, key: str,
            exclude: Container = set()) -> bool: ...

    def has(self, obj, key, exclude=set()):
        """ Check whether `key` is in `obj` as an item or attribute.
            Defined to add `exclude` option.

        :param key: _KT: Hashable
        :param exclude: Container[_VT], values to ignore or overwrite. If
            `obj` maps `key` to one, then return False as if `obj` does not
            contain `key`.
        :return: bool, True if `key` is not mapped to a value in `obj` or
            is mapped to something in `exclude`
        """
        try:  # If obj has key, return True iff its value doesn't count
            return self.get(obj, key) not in exclude

        except self.MissingError:  # If obj lacks key return False
            return False

        # `self.get(obj, key) not in exclude` raises TypeError if it isn't
        # Hashable. In that case, it can't be in exclude, so obj has key.
        except TypeError:
            return True

    @overload
    def has_all(self, obj: Mapping[_KT, _VT], /, keys: Iterable[_KT],
                exclude: Container[_VT] = set()) -> bool: ...

    @overload
    def has_all(self, obj: Any, /, keys: Iterable[str],
                exclude: Container[str] = set()) -> bool: ...

    def has_all(self, obj, keys, exclude=set()):
        """
        :param obj: Mapping[_KT, _VT] to check whether it contains all `keys`.
        :param keys: Iterable[_K], keys to find in `obj`.
        :param exclude: Container[_VT], values to overlook/ignore such that if
            `obj` maps a key to one of those values, then this function
            will return False as if `key is not in obj`.
        :return: bool, True if every key in `keys` is mapped to a value that
            is not in `exclude`; else False.
        """
        try:
            next(self.missing_keys(obj, keys, exclude))
            return False
        except StopIteration:
            return True

    @overload
    def lazyget(self, obj: Mapping[_KT, _VT], /, key: _KT,
                get_if_absent: Callable[_P, _D],
                exclude: Container[_VT] = set(),
                *args: _P.args, **kwargs: _P.kwargs) -> _VT | _D: ...

    @overload
    def lazyget(self, obj: Any, /, key: str,
                get_if_absent: Callable[_P, Any],
                exclude: Container = set(),
                *args: _P.args, **kwargs: _P.kwargs) -> Any: ...

    def lazyget(self, obj, /, key, get_if_absent: Callable[_P, Any],
                exclude=set(), *args: _P.args, **kwargs: _P.kwargs):
        """ Return the value for key if key is in the dictionary, else
        return the result of calling the `get_if_absent` parameter with args
        & kwargs. Adapted from `LazyButHonestDict.lazyget` from
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param args: Iterable[Any] of get_if_absent arguments
        :param kwargs: Mapping of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to
            `key` in `a_dict`) will not be returned; instead returning
            `get_if_absent(*args, **kwargs)`
        """
        return get_if_absent(*args, **kwargs) if not \
            self.has(obj, key, exclude) else self.get(obj, key)

    @overload
    def lazysetdefault(self, obj: MutableMapping[_KT, _VT], /, key: _KT,
                       get_if_absent: Callable[_P, _D],
                       exclude: Container[_VT] = set(),
                       *args: _P.args, **kwargs: _P.kwargs) -> _VT | _D: ...

    @overload
    def lazysetdefault(self, obj: Any, /, key: str,
                       get_if_absent: Callable[_P, Any],
                       exclude: Container = set(),
                       *args: _P.args, **kwargs: _P.kwargs) -> Any: ...

    def lazysetdefault(self, obj, /, key, get_if_absent: Callable[_P, Any],
                       exclude=set(), *args: _P.args, **kwargs: _P.kwargs):
        """ Return the value for key if key is in the dictionary; else add 
        that key to the dictionary, set its value to the result of calling 
        the `get_if_absent` parameter with args & kwargs, then return that 
        result. Adapted from `LazyButHonestDict.lazysetdefault` from 
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param args: Iterable[Any] of get_if_absent arguments
        :param kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: Container of possible values to replace with 
            `get_if_absent(*args, **kwargs)` and return if 
            they are mapped to `key` in `a_dict`
        """
        if not self.has(obj, key, exclude):
            new_value = get_if_absent(*args, **kwargs)
            self.set_to(obj, key, new_value)
            return new_value
        else:
            return self.get(obj, key)

    @overload
    def lookup(self, obj: Mapping[_KT, _VT], /, path: str, sep: str = ".",
               default: _D = None) -> _VT | _D: ...

    @overload
    def lookup(self, obj: Any, /, path: str, sep: str = ".",
               default: Any = None) -> Any: ...

    def lookup(self, obj, /, path: str, sep: str = ".", default=None):
        """ Get the value mapped to a key in nested structure. Adapted from 
            https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param obj: Mapping[_KT: Hashable, _VT: Any] to find a value in
        :param path: str, path to key in nested structure, e.g. "a.b.c"
        :param sep: str, separator between keys in path; defaults to "."
        :param default: Any, value to return if key is not found
        :return: _VT | _D, the value mapped to the nested key if any, else default
        """
        keypath = list(reversed(path.split(sep)))
        retrieved = obj
        try:
            while keypath:
                key = keypath.pop()
                retrieved = self.get(retrieved, key)

        # If value is not found, then return the default value
        except DATA_ERRORS:
            retrieved = default
        return default if keypath else retrieved

    @overload
    def missing_keys(self, obj: Mapping[_KT, _VT], /, keys: Iterable[_KT],
                     exclude: Container[_VT] = set()
                     ) -> Generator[_KT, None, None]: ...

    @overload
    def missing_keys(self, obj: Any, /, keys: Iterable[str],
                     exclude: Container = set()
                     ) -> Generator[str, None, None]: ...

    def missing_keys(self, obj, /, keys, exclude=set()):
        """
        :param obj: Mapping[_KT: Hashable, _VT: Any] | Any, _description_
        :param keys: Iterable[_KT], keys to find in `obj`
        :param exclude: Container[_VT], values to overlook/ignore such that if 
            `obj` maps a key to one of those values, then this function 
            will yield that key as if `key` is not in `obj`.
        :yield: Generator[_KT, None, None], all `keys` that either are not in 
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

    @overload
    def setdefault(self, obj: MutableMapping[_KT, _VT], /, key: _KT,
                   value: _D = None, exclude: Container[_VT] = set()
                   ) -> _VT | _D: ...

    @overload
    def setdefault(self, obj: Any, /, key: str,
                   value: Any = None, exclude: Container = set()) -> Any: ...

    def setdefault(self, obj, /, key, value=None, exclude=set()):
        """ Return the value for key if key is in `obj`; else add 
            that key to `obj`, set it to value, and return it

        :param key: _KT: Hashable to use as a key to map to value
        :param value: _type_, _description_
        """
        gotten = self.getdefault(obj, key, value, exclude)
        if gotten is value:
            self.set_to(obj, key, value)
        return gotten

    @overload
    def setdefault_or_prompt_for(self, obj: MutableMapping[_KT, _VT], /, key: _KT,
                                 prompt: str, prompt_fn: Callable[[str], str]
                                 = input, exclude: Container[_VT] = set()
                                 ) -> _VT | str: ...

    @overload
    def setdefault_or_prompt_for(self, obj: Any, /, key: str,
                                 prompt: str, prompt_fn: Callable[[str], str]
                                 = input, exclude: Container = set()
                                 ) -> Any: ...

    def setdefault_or_prompt_for(self, obj, /, key, prompt, prompt_fn=input,
                                 exclude=set()):
        """ Return the value mapped to key in `obj` if one already exists; 
            otherwise prompt the user to interactively provide it, store the 
            provided value by mapping it to key, and return that value.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to 
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `obj` 
            maps `key` to one, prompt the user as if `key is not in obj`.
        :return: Any, the value mapped to key if one exists, else the value 
                 that the user interactively provided
        """
        return self.lazysetdefault(obj, key, prompt_fn, exclude, prompt)

    def setdefaults(self, obj: _T, /, exclude: Container = set(),
                    **kwargs: Any) -> _T:
        """ Fill any missing values in obj from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param obj: MutableMapping[_KT: Hashable, _VT: Any] | _T: Any, 
            _description_
        :param exclude: Container[_VT], values to overlook/ignore such that 
            if `obj` maps `key` to one of those values, then this function 
            will try to overwrite that value with a value mapped to the 
            same key in `kwargs`, as if `key` is not in `obj`.
        :param kwargs: Mapping[str, _VT] of values to add to `obj` if needed.
        :return: MutableMapping[_KT, _VT] | _T
        """
        for key in self.missing_keys(obj, kwargs, exclude):
            self.set_to(obj, key, kwargs[key])
        return obj


ACCESS_ITEM = Accessor(
    contains=operator.contains, get=operator.getitem,
    set_to=operator.setitem, delete=operator.delitem,
    MissingError=KeyError)
ACCESS_ATTR = Accessor(contains=hasattr, get=getattr,
                       set_to=setattr, delete=delattr,
                       MissingError=AttributeError)


ACCESS = AttrMap[Accessor](item=ACCESS_ITEM, attribute=ACCESS_ATTR)
