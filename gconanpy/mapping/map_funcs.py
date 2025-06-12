#!/usr/bin/env python3

"""
Useful/convenient functions to use on dicts. Taken from dicts.py classes
Greg Conan: gregmconan@gmail.com
Created: 2025-06-09
Updated: 2025-06-11
"""
# Import standard libraries
from collections.abc import Callable, Collection, Container, Generator, \
    Hashable, Iterable, Mapping, MutableMapping, Sequence
from configparser import ConfigParser
from typing import Any, TypeVar

# Import local custom libraries
try:
    from metafunc import DATA_ERRORS
    from trivial import always_none
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.metafunc import DATA_ERRORS
    from gconanpy.trivial import always_none

# Constants: type variables
_MM = TypeVar("_MM", bound=MutableMapping)  # For update and setdefaults
_Prompter = Callable[[str], str]  # Prompt function to use as lazy getter
_T = TypeVar("_T")  # For invert
CollisionHandler = None | Callable[[list[_T]], Iterable[_T]]  # For invert
FromMap = TypeVar("FromMap", Mapping, Iterable[tuple[Hashable, Any]], None
                  )  # For update function input parameters


def chain_get(a_dict: Mapping, keys: Sequence[Hashable], default: Any = None,
              exclude: Container = set()) -> Any:
    """ Return the value mapped to the first key if any, else return \
        the value mapped to the second key if any, ... etc. recursively. \
        Return `default` if `a_dict` doesn't contain any of the `keys`.

    :param keys: Sequence[Hashable], keys mapped to the value to return
    :param default: Any, object to return if no `keys` are in `a_dict`
    :param exclude: Container, values to ignore or overwrite. If one \
        of the `keys` is mapped to a value in `exclude`, then skip that \
        key as if `key is not in self`.
    :return: Any, value mapped to the first key (of `keys`) in `a_dict` \
        if any; otherwise `default` if no `keys` are in `a_dict`.
    """
    return getdefault(a_dict, keys[0], chain_get(a_dict, keys[1:], default),
                      exclude) if keys else default


def fromConfigParser(config: ConfigParser) -> dict:
    """
    :param config: ConfigParser to convert into DotDict
    :return: DotDict with the key-value mapping structure of config
    """
    return {section: {k: v for k, v in config.items(section)}
            for section in config.sections()}


def get_or_prompt_for(a_dict: Mapping, key: Hashable, prompt: str,
                      prompt_fn: _Prompter = input,
                      exclude: Container = set()) -> Any:
    """ Return the value mapped to key in a_dict if one already exists; \
        else prompt the user to interactively provide it and return that.

    :param key: str mapped to the value to retrieve
    :param prompt: str to display when prompting the user.
    :param prompt_fn: Callable that interactively prompts the user to \
                        get a string, like `input` or `getpass.getpass`.
    :param exclude: Container, values to ignore or overwrite. If `a_dict` \
        maps `key` to one, prompt the user as if `key is not in a_dict`.
    :return: Any, the value mapped to key if one exists, else the value \
                that the user interactively provided
    """
    return lazyget(a_dict, key, prompt_fn, [prompt], exclude=exclude)


def get_subset_from_lookups(a_dict: Mapping, to_look_up: Mapping[str, str],
                            sep: str = ".", default: Any = None) -> dict:
    """ `a_dict.get_subset_from_lookups({"a": "b/c"}, sep="/")` \
        -> `DotDict({"a": a_dict.b.c})`

    :param to_look_up: Mapping[str, str] of every key to put in the \
        returned DotDict to the path to its value in this DotDict (a_dict)
    :param sep: str, separator between subkeys in to_look_up.values(), \
        defaults to "."
    :param default: Any, value to use map to any keys not found in a_dict; \
        defaults to None
    :return: a_dict.__class__ mapping every key in to_look_up to the value \
        at its mapped path in a_dict
    """
    return {key: lookup(a_dict, path, sep, default)
            for key, path in to_look_up.items()}


def getdefault(a_dict: Mapping, key: Hashable, default: Any = None,
               exclude: Container = set()) -> Any:
    """ Return the value mapped to `key` in `a_dict`, if any; else return \
        `default`. Defined to add `exclude` option to `dict.get`.

    :param key: Hashable, key mapped to the value to return
    :param default: Any, object to return `if a_dict.will_getdefault`, \
        i.e. `if key not in a_dict or a_dict[key] in exclude`
    :param exclude: Container, values to ignore or overwrite. If `a_dict` \
        maps `key` to one, then return True as if `key is not in a_dict`.
    :return: Any, value mapped to `key` in `a_dict` if any, else `default`
    """
    return default if will_getdefault(a_dict, key, exclude) else a_dict[key]


def has_all(a_dict: Mapping, keys: Iterable[Hashable],
            exclude: Collection = set()) -> bool:
    """
    :param keys: Iterable[_K], keys to find in this Defaultionary.
    :param exclude: Collection, values to overlook/ignore such that if \
        `a_dict` maps a key to one of those values, then this function \
        will return False as if `key is not in a_dict`.
    :return: bool, True if every key in `keys` is mapped to a value that \
        is not in `exclude`; else False.
    """
    try:
        next(missing_keys(a_dict, keys, exclude))
        return False
    except StopIteration:
        return True


def invert(a_dict: dict, keep_collisions_in: CollisionHandler = None) -> dict:
    """ Swap keys and values. Inverting {1: 2, 3: 4} returns {2: 1, 4: 3}.

    When 2+ keys are mapped to the same value, then that value will be \
    mapped either to a `keep_collisions_in` container of all of those \
    keys or (by default) to only the most recently-added key.

    :param keep_collisions_in: CollisionHandler, type of container to \
        map a value to when multiple keys were mapped to that value; \
        e.g. `list`, `tuple`, or `set`
    """
    # If we are NOT keeping all keys mapped to the same value, then
    # just keep whichever key was added most recently
    if keep_collisions_in is None:
        inverted = {v: k for k, v in a_dict.items()}

    else:  # If we ARE keeping all keys mapped to the same value, then:
        inverted = dict()  # Avoid conflating keys & values
        collided = set()  # Keep track of which values collide

        # If values don't collide, just swap them with keys
        # TODO Instead, contain every new value so dict has 1 value type?
        for key, value in a_dict.items():
            if value not in inverted:
                inverted[value] = key

            # If 2+ former values (now keys) collide, then map them to a
            # keep_collisions_in container holding all of the former keys
            else:
                new_value = [*inverted[value], key] if value in collided \
                    else [inverted[value], key]
                collided.add(value)
                inverted[value] = keep_collisions_in(new_value)
    return inverted


def lazyget(a_dict: Mapping, key: Hashable,
            get_if_absent: Callable = always_none,
            getter_args: Iterable = list(),
            getter_kwargs: Mapping = dict(),
            exclude: Container = set()) -> Any:
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
    return get_if_absent(*getter_args, **getter_kwargs) if \
        will_getdefault(a_dict, key, exclude) else a_dict[key]


def lazysetdefault(a_dict: MutableMapping, key: Hashable, get_if_absent:
                   Callable = always_none, getter_args: Iterable = list(),
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
    if will_getdefault(a_dict, key, exclude):
        a_dict[key] = get_if_absent(*getter_args, **getter_kwargs)
    return a_dict[key]


def lookup(a_dict: Mapping, path: str, sep: str = ".", default: Any = None) -> Any:
    """ Get the value mapped to a key in nested structure. Adapted from \
        https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

    :param path: str, path to key in nested structure, e.g. "a.b.c"
    :param sep: str, separator between keys in path; defaults to "."
    :param default: Any, value to return if key is not found
    :return: Any, the value mapped to the nested key
    """
    keypath = list(reversed(path.split(sep)))
    retrieved = a_dict
    try:
        while keypath:
            key = keypath.pop()
            try:
                retrieved = retrieved[key]
            except KeyError:
                retrieved = retrieved[int(key)]

    # If value is not found, then return the default value
    except DATA_ERRORS:
        pass
    return default if keypath else retrieved


def missing_keys(a_dict: Mapping, keys: Iterable, exclude: Collection = set()
                 ) -> Generator[Any, None, None]:
    """
    :param keys: Iterable[_K], keys to find in this Defaultionary.
    :param exclude: Collection, values to overlook/ignore such that if \
        `a_dict` maps a key to one of those values, then this function \
        will yield that key as if `key is not in a_dict`.
    :yield: Generator[_K, None, None], all `keys` that either are not in \
        this Defaultionary or are mapped to a value in `exclude`.
    """
    if exclude:
        example_exclude = next(iter(exclude))
        for key in keys:
            if getdefault(a_dict, key, example_exclude, exclude
                          ) is example_exclude:
                yield key
    else:
        for key in keys:
            if key not in a_dict:
                yield key


def setdefault_or_prompt_for(a_dict: MutableMapping, key: Hashable,
                             prompt: str, prompt_fn: _Prompter = input,
                             exclude: Container = set()) -> Any:
    """ Return the value mapped to key in a_dict if one already exists; \
        otherwise prompt the user to interactively provide it, store the \
        provided value by mapping it to key, and return that value.

    :param key: str mapped to the value to retrieve
    :param prompt: str to display when prompting the user.
    :param prompt_fn: Callable that interactively prompts the user to \
                        get a string, like `input` or `getpass.getpass`.
    :param exclude: Container, values to ignore or overwrite. If `a_dict` \
        maps `key` to one, prompt the user as if `key is not in a_dict`.
    :return: Any, the value mapped to key if one exists, else the value \
                that the user interactively provided
    """
    return lazysetdefault(a_dict, key, prompt_fn, [prompt], exclude=exclude)


def setdefaults(a_dict: _MM, exclude: Collection = set(),
                **kwargs: Any) -> _MM:
    """ Fill any missing values in a_dict from kwargs.
        dict.update prefers to overwrite old values with new ones.
        setdefaults is basically dict.update that prefers to keep old values.

    :param exclude: Collection, values to overlook/ignore such that if \
        `a_dict` maps `key` to one of those values, then this function \
        will try to overwrite that value with a value mapped to the \
        same key in `kwargs`, as if `key is not in a_dict`.
    :param kwargs: Mapping[str, Any] of values to add to a_dict if needed.
    """
    for key in missing_keys(a_dict, kwargs.keys(), exclude):
        a_dict[key] = kwargs[key]
    return a_dict


def update(a_dict: _MM, from_map: FromMap = None, **kwargs: Any) -> _MM:
    """ Add or overwrite items in this Mapping from other Mappings.

    :param from_map: Mapping | Iterable[tuple[Hashable, Any] ] | None \
        of key-value pairs to save into this Updationary. Overwrites \
        existing pairs, but can be overwritten by `kwargs`. Defaults to \
        None. Effectively the same as `m` in `dict.update` method. 
    :param copy: bool, True to return an updated copy of this \
        Updationary instead of updating the original; else False to \
        update the original and return None.
    :param kwargs: Mapping[str, Any] of key-value pairs to save into \
        this Updationary. If `kwargs` and `from_map` map the same key to \
        different values, then the value in `kwargs` will be saved.
    :return: None if copy=False; else a dict of the same class as `a_dict`.
    """
    for each_map in from_map, kwargs:  # kwargs can overwrite from_map
        if each_map is not None:
            a_dict.update(each_map)
    return a_dict


def will_getdefault(a_dict: Mapping, key: Hashable, exclude: Container = set()
                    ) -> bool:
    """
    :param key: Hashable
    :param exclude: Container, values to ignore or overwrite. If `a_dict` \
        maps `key` to one, then return True as if `key is not in a_dict`.
    :return: bool, True if `key` is not mapped to a value in `a_dict` or \
        is mapped to something in `exclude`
    """
    return key not in a_dict or a_dict[key] in exclude
