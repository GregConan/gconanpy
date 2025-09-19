#!/usr/bin/env python3

"""
Useful/convenient functions for dicts (taken from dicts.py class methods).
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-09-18
"""
# Import standard libraries
from collections import defaultdict
from collections.abc import Callable, Collection, Container, Generator, \
    Hashable, Iterable, Mapping, MutableMapping, Sequence
from configparser import ConfigParser
from operator import itemgetter
from pprint import pprint
from typing import Any, cast, Literal, overload, TypeVar

# Import local custom libraries
try:
    from gconanpy.iters import SimpleShredder
    from gconanpy.meta.typeshed import DATA_ERRORS, SupportsRichComparison
    from gconanpy.trivial import always_none
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from iters import SimpleShredder
    from meta.typeshed import DATA_ERRORS, SupportsRichComparison
    from trivial import always_none

# Constants: type variables
_D = TypeVar("_D")
_KT = TypeVar("_KT", bound=Hashable)
_VT = TypeVar("_VT")

_MM = TypeVar("_MM", bound=MutableMapping)  # For update and setdefaults
_MM_str = TypeVar("_MM_str", bound=MutableMapping[str, Any])
_ValueGetter = Callable[..., _VT]
_Prompter = Callable[[str], _VT]  # Prompt function to use as lazy getter
_T = TypeVar("_T")  # For invert
CollisionHandler = None | Callable[[list[_T]], Iterable[_T]]  # For invert
FromMap = TypeVar("FromMap", Mapping, Iterable[tuple[Hashable, Any]], None
                  )  # For update function input parameters
Sortable = TypeVar("Sortable", bound=SupportsRichComparison)  # For sorted_by


def chain_get(a_map: Mapping[_KT, _VT], keys: Sequence[_KT],
              default: _D = None, exclude: Container[_VT] = set()
              ) -> _VT | _D:
    """ Return the value mapped to the first key if any, else return \
        the value mapped to the second key if any, ... etc. recursively. \
        Return `default` if `a_map` doesn't contain any of the `keys`.

    :param a_map: Mapping[_KT: Hashable, _VT: Any]
    :param keys: Sequence[_KT], keys mapped to the value to return
    :param default: _D: Any, object to return if no `keys` are in `a_map`
    :param exclude: Container[_VT], values to ignore or overwrite. \
        If one of the `keys` is mapped to a value in `exclude`, then skip \
        that key as if `key is not in a_map`.
    :return: _KT | _D, value mapped to the first key (of `keys`) in `a_map` \
        if any; otherwise `default` if none of the `keys` are in `a_map`.
    """
    for key in keys:
        if has(a_map, key, exclude):
            return a_map[key]
    return default


def fromConfigParser(config: ConfigParser) -> dict:
    """
    :param config: ConfigParser to convert into DotDict
    :return: DotDict with the key-value mapping structure of config
    """
    return {section: {k: v for k, v in config.items(section)}
            for section in config.sections()}


def from_strings(strings: Iterable[str], delimiter: str = ": "
                 ) -> dict[str, str]:
    a_dict = dict()
    for eachstr in strings:
        k, v = eachstr.split(delimiter)
        a_dict[k] = v
    return a_dict


def get_or_prompt_for(a_map: Mapping[_KT, _VT], key: _KT, prompt: str,
                      prompt_fn: _Prompter = input,
                      exclude: Container[_VT] = set()) -> _VT | str:
    """ Return the value mapped to key in a_map if one already exists and \
        is not in `exclude`; else prompt the user to interactively provide \
        it and return that.

    :param a_map: Mapping[_KT: Hashable, _VT: Any], _description_
    :param key: str possibly mapped to the value to retrieve
    :param prompt: str to display when prompting the user.
    :param prompt_fn: Callable that interactively prompts the user to \
                        get a string, like `input` or `getpass.getpass`.
    :param exclude: Container[_VT], values to ignore or overwrite. If \
        `a_map` maps `key` to one, prompt the user as if \
        `key is not in a_map`.
    :return: Any, the value mapped to key if one exists, else the value \
                that the user interactively provided
    """
    return lazyget(a_map, key, prompt_fn, [prompt], exclude=exclude)


def get_subset_from_lookups(a_map: Mapping[str, _VT],
                            to_look_up: Mapping[str, str],
                            sep: str = ".", default: _D = None
                            ) -> dict[str, _VT | _D]:
    """ `get_subset_from_lookups(a_map, {"a": "b/c"}, sep="/")` \
        -> `dict({"a": a_map["b"]["c"]})`

    :param a_map: Mapping[str, _VT: Any] to return a subset of
    :param to_look_up: Mapping[str, str] of every key to put in the \
        returned dict to the path to its value in this dict (`a_map`)
    :param sep: str, separator between subkeys in `to_look_up.values()`, \
        defaults to "."
    :param default: _D: Any, value to map to any keys not found in `a_map`; \
        defaults to None
    :return: dict[str, _VT | _D] mapping every key in `to_look_up` to the \
        value at its mapped path in `a_map`
    """
    return {key: lookup(a_map, path, sep, default)
            for key, path in to_look_up.items()}


def getdefault(a_map: Mapping[_KT, _VT], key: _KT, default: _D = None,
               exclude: Container[_VT] = set()) -> _VT | _D:
    """ Return the value mapped to `key` in `a_map`, if any; else return \
        `default`. Defined to add `exclude` option to `dict.get`.

    :param a_map: Mapping[_KT: Hashable, _VT: Any] to try to get a value from
    :param key: _KT, a key that `a_map` might map to the value to return
    :param default: _D: Any, object to return `if not self.has` the key, \
            i.e. `if key not in self or self[key] in exclude`
    :param exclude: Container[_VT], values to ignore or overwrite. If `a_map` \
        maps `key` to one, then return True as if `key is not in a_map`
    :return: _VT | _D, value mapped to `key` in `a_map` if any; else `default`
    """
    return a_map[key] if has(a_map, key, exclude) else default


def has(a_map: Mapping[_KT, _VT], key: _KT,
        exclude: Container[_VT] = set()) -> bool:
    """
    :param a_map: Mapping[_KT: Hashable, _VT: Any] to find `key` in
    :param key: _KT to check `a_map` for
    :param exclude: Container[_VT], values to ignore or overwrite. If \
        `a_map` maps `key` to one, then return False as if \
        `key is not in a_map`.
    :return: bool, True if `key` is mapped to a value in `a_map` and \
        is not mapped to anything in `exclude`.
    """
    try:  # If a_map has the key, return True unless its value doesn't count
        result = a_map[key] not in exclude

    except KeyError:  # If a_map lacks the key, return False
        result = False

    # `self[key] in exclude` raises TypeError if self[key] isn't Hashable.
    # In that case, self[key] can't be in exclude, so self has key.
    except TypeError:
        result = True

    return result


def has_all(a_map: Mapping[_KT, _VT], keys: Iterable[_KT],
            exclude: Container[_VT] = set()) -> bool:
    """
    :param a_map: Mapping[_KT, _VT] to check whether it contains all `keys`.
    :param keys: Iterable[_K], keys to find in `a_map`.
    :param exclude: Container[_VT], values to overlook/ignore such that if \
        `a_map` maps a key to one of those values, then this function \
        will return False as if `key is not in a_map`.
    :return: bool, True if every key in `keys` is mapped to a value that \
        is not in `exclude`; else False.
    """
    try:
        next(missing_keys(a_map, keys, exclude))
        return False
    except StopIteration:
        return True


@overload
def invert(a_map: Mapping[_KT, _VT], keep_keys: Literal[True]
           ) -> dict[_VT, list[_KT]]: ...


@overload
def invert(a_map: Mapping[_KT, _VT], keep_keys: Literal[False, "unpack"]
           ) -> dict[_VT, _KT]: ...


@overload
def invert(a_map: Mapping[_KT, _VT]) -> dict[_VT, _KT]: ...


def invert(a_map: Mapping[_KT, _VT],
           keep_keys: bool | Literal["unpack"] = False):
    """ Swap keys and values. Inverting {1: 2, 3: 4} returns {2: 1, 4: 3}.

    When 2+ keys are mapped to the same value, then that value will be \
    mapped either to a `keep_collisions_in` container of all of those \
    keys or (by default) to only the most recently-added key.

    :param a_dict: dict[_KT, _VT] to invert
    :param keep_keys: True to map each value to a list of the keys that \
        previously were mapped to it, False to only keep the last key mapped \
        to each value, or "unpack" (if every value is iterable) to map each \
        element of each value to a list of the previously-mapped keys.
    """
    # If we are NOT keeping all keys mapped to the same value, then
    # just keep whichever key was added most recently
    if not keep_keys:
        inverted = {v: k for k, v in a_map.items()}

    else:  # If we ARE keeping all keys mapped to the same value, then:
        inverted = defaultdict(list)  # Avoid conflating keys & values

        # "Shred" each iterable value to map each of its elements to each key
        if keep_keys == "unpack":
            shredder = SimpleShredder()
            for key, value in a_map.items():
                for subval in shredder.shred(value):
                    inverted[subval].append(key)
                shredder.reset()
        else:  # If keep_keys=True, then simply keep the keys in a list
            for key, value in a_map.items():
                inverted[value].append(key)

        inverted = dict(inverted)
    return inverted


def keys_mapped_to(a_map: Mapping[_KT, _VT], value: _VT,
                   ) -> Generator[_KT, None, None]:
    """ 
    :param a_map: Mapping[_KT: Hashable, _VT: Any] to yield all keys mapped \
        to `value` from
    :param value: _VT: Any, the value to yield all keys mapped to by `a_map`
    :yield: Generator[_KT, None, None], all keys mapped to `value` in `a_map`
    """
    for k, v in a_map.items():
        if v == value:
            yield k


def lazyget(a_map: Mapping[_KT, _VT], key: _KT,
            get_if_absent: _ValueGetter = always_none,
            getter_args: Iterable = list(),
            getter_kwargs: Mapping = dict(),
            exclude: Container[_VT] = set()) -> _VT:
    """ Adapted from `LazyButHonestDict.lazyget` from \
        https://stackoverflow.com/q/17532929

    :param a_map: Mapping[_KT: Hashable, _VT: Any] to try to get a value from
    :param key: _KT, a key that `a_map` might map to the value to return
    :param get_if_absent: Callable that returns the default value
    :param getter_args: Iterable[Any] of `get_if_absent` arguments
    :param getter_kwargs: Mapping of `get_if_absent` keyword arguments
    :param exclude: Container[_VT] of possible values which (if they are \
        mapped to `key` in `a_map`) will not be returned; instead returning \
        `get_if_absent(*getter_args, **getter_kwargs)`
    :return: _VT, the value that `a_map` maps to `key`, if that value isn't \
            in `exclude`; else `return get_if_absent(*args, **kwargs)`
    """
    return a_map[key] if has(a_map, key, exclude) else \
        get_if_absent(*getter_args, **getter_kwargs)


def lazysetdefault(a_map: MutableMapping[_KT, _VT], key: _KT,
                   get_if_absent: _ValueGetter = always_none,
                   getter_args: Iterable = list(),
                   getter_kwargs: Mapping = dict(),
                   exclude: Container[_VT] = set()) -> _VT:
    """ Return the value for key if key is in `a_map` and not in \
        `exclude`; else add that key to `a_map`, set its value to \
        `get_if_absent(*args, **kwargs)`, and then return that.

    Adapted from `LazyButHonestDict.lazysetdefault` from \
    https://stackoverflow.com/q/17532929

    :param a_map: MutableMapping[_KT: Hashable, _VT: Any], _description_
    :param key: _KT to use as a dict key to map to value
    :param get_if_absent: Callable, function to set & return default value
    :param getter_args: Iterable[Any] of get_if_absent arguments
    :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
    :param exclude: Container[_VT] of possible values to replace with \
        `get_if_absent(*getter_args, **getter_kwargs)` and return if \
        they are mapped to `key` in `a_map` but not in `exclude`
    """
    if not has(a_map, key, exclude):
        a_map[key] = get_if_absent(*getter_args, **getter_kwargs)
    return a_map[key]


def lookup(a_map: Mapping[_KT, _VT], path: str, sep: str = ".",
           default: _D = None) -> _VT | _D:
    """ Get the value mapped to a key in nested structure. Adapted from \
        https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

    :param a_map: Mapping[_KT: Hashable, _VT: Any] to find a value in
    :param path: str, path to key in nested structure, e.g. "a.b.c"
    :param sep: str, separator between keys in path; defaults to "."
    :param default: Any, value to return if key is not found
    :return: _VT | _D, the value mapped to the nested key if any, else default
    """
    keypath = list(reversed(path.split(sep)))
    retrieved = a_map
    try:
        while keypath:
            key = keypath.pop()
            try:
                retrieved = cast(Mapping[str, _VT], retrieved)[key]
            except KeyError:
                retrieved = cast(Mapping[int, _VT], retrieved)[int(key)]

    # If value is not found, then return the default value
    except DATA_ERRORS:
        retrieved = default
    return default if keypath else cast(_VT, retrieved)


def missing_keys(a_map: Mapping[_KT, _VT], keys: Iterable[_KT],
                 exclude: Container[_VT] = set()
                 ) -> Generator[_KT, None, None]:
    """
    :param a_map: Mapping[_KT: Hashable, _VT: Any], _description_
    :param keys: Iterable[_KT], keys to find in `a_map`
    :param exclude: Container[_VT], values to overlook/ignore such that if \
        `a_map` maps a key to one of those values, then this function \
        will yield that key as if `key is not in a_map`.
    :yield: Generator[_KT, None, None], all `keys` that either are not in \
        `a_map` or are mapped to a value in `exclude`.
    """
    if exclude:
        for key in keys:
            if not has(a_map, key, exclude):
                yield key
    else:
        for key in keys:
            if key not in a_map:
                yield key


def overlap_pct(**collections: Collection[Hashable]
                ) -> dict[str, dict[str, float]]:
    overlaps = dict()
    for collname, collns in collections.items():
        overlaps[collname] = dict()
        for othername, othercollns in collections.items():
            overlaps[collname][othername] = \
                len(collns) / len(set(collns) | set(othercollns))
    return overlaps


def pprint_val_lens(a_map: Mapping) -> None:
    """ Pretty-print each key in a_map and the length of its mapped value.

    :param a_map: Mapping to pretty-print the lengths of values from
    """
    pprint({k: len(v) for k, v in a_map.items()})


def rename_keys(a_map: _MM_str, **renamings: str) -> _MM_str:
    """
    :param a_map: MutableMapping[str, Any] with keys to rename
    :param renamings: Mapping[str, str] of old keys to their replacements
    :return: MutableMapping[str, Any], `a_map` after replacing its keys in \
        `renamings` with the respective values in `renamings`
    """
    for old_name, new_name in renamings.items():
        a_map[new_name] = a_map.pop(old_name)
    return a_map


def setdefault_or_prompt_for(a_map: MutableMapping[_KT, _VT], key: _KT,
                             prompt: str, prompt_fn: _Prompter = input,
                             exclude: Container[_VT] = set()) -> _VT | str:
    """ Return the value mapped to key in a_map if one already exists; \
        otherwise prompt the user to interactively provide it, store the \
        provided value by mapping it to key, and return that value.

    :param a_map: MutableMapping[KT: Hashable, VT: Any], _description_
    :param key: _KT possibly mapped to the value to retrieve
    :param prompt: str to display when prompting the user.
    :param prompt_fn: Callable that interactively prompts the user to \
                        get a string, like `input` or `getpass.getpass`.
    :param exclude: Container[_VT], values to ignore or overwrite. If \
        `a_map` maps `key` to one, prompt the user as if `key is not in a_map`
    :return: _VT | str, the value mapped to key if one exists, else the \
            string value that the user interactively provided
    """
    return lazysetdefault(a_map, key, prompt_fn, [prompt], exclude=exclude)


def setdefaults(a_map: _MM, exclude: Container = set(),
                **kwargs: Any) -> _MM:
    """ Fill any missing values in a_map from kwargs.
        dict.update prefers to overwrite old values with new ones.
        setdefaults is basically dict.update that prefers to keep old values.

    :param a_map: _MM: MutableMapping[KT: Hashable, VT: Any], _description_
    :param exclude: Container[VT], values to overlook/ignore such that if \
        `a_map` maps `key` to one of those values, then this function \
        will try to overwrite that value with a value mapped to the \
        same key in `kwargs`, as if `key is not in a_map`.
    :param kwargs: Mapping[str, VT] of values to add to a_map if needed.
    """
    for key in missing_keys(a_map, kwargs, exclude):
        a_map[key] = kwargs[key]
    return a_map


@overload
def sorted_by(a_map: Mapping[_KT, Sortable], by: Literal["keys"],
              descending: bool) -> Generator[tuple[_KT, Sortable]]: ...


@overload
def sorted_by(a_map: Mapping[Sortable, _VT], by: Literal["values"],
              descending: bool) -> Generator[tuple[Sortable, _VT]]: ...


def sorted_by(a_map: Mapping, by: Literal["keys", "values"],
              descending: bool = False) -> Generator[tuple, None, None]:
    """ Adapted from https://stackoverflow.com/a/50569360

    :param a_map: Mapping[_KT, _VT] to yield every key-value pairing from
    :param by: Literal["keys", "values"], "keys" to yield key-value \
        pairings sorted by keys; else "values" to sort them by values
    :param descending: bool, True to yield the key-value pairings with \
        the largest ones first; else False to yield the smallest first; \
        defaults to False
    :yield: Generator[tuple[_KT, _VT], None, None], each key-value pairing \
        in this Sortionary as a tuple, sorted `by` keys or values in \
        ascending or `descending` order
    """
    match by:
        case "keys":
            for k in sorted(a_map, reverse=descending):
                yield (k, a_map[k])
        case "values":
            for k, v in sorted(a_map.items(), key=itemgetter(1),
                               reverse=descending):
                yield (k, v)


def update(a_map: _MM, from_map: FromMap = None, **kwargs: Any) -> _MM:
    """ Add or overwrite items in a MutableMapping from other Mappings.

    :param a_map: _MM: MutableMapping[KT: Hashable, VT: Any], _description_
    :param from_map: Mapping | Iterable[tuple[KT, VT] ] | None \
        of key-value pairs to save into `a_map`. Overwrites existing \
        pairs. `from_map` can be overwritten by `kwargs`. Defaults to \
        None. Effectively the same as `m` in `dict.update` method. 
    :param kwargs: Mapping[str, VT] of key-value pairs to save into `a_map`. \
        If `kwargs` and `from_map` map the same key to different values, \
        then the value in `kwargs` will be saved.
    :return: _MM, `a_map` updated to include the key-value mappings \
        in `kwargs` and in `from_map`
    """
    for each_map in from_map, kwargs:
        if each_map is not None:
            a_map.update(each_map)
    return a_map
