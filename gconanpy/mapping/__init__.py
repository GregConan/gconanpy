#!/usr/bin/env python3

"""
Useful/convenient classes to work with Python dicts/Mappings.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-07-07
"""
# Import standard libraries
from collections.abc import (Callable, Collection, Container,
                             Generator, Hashable, Mapping)
import itertools
import sys
from typing import Any, overload, SupportsBytes, TypeVar


class Bytesifier:
    """ Class with a method to convert objects into bytes without knowing \
        what type those things are. """
    _T = TypeVar("_T")
    IsOrSupportsBytes = TypeVar("IsOrSupportsBytes", bytes, SupportsBytes)

    DEFAULTS = dict(encoding=sys.getdefaultencoding(), length=1,
                    byteorder="big", signed=False)

    def try_bytesify(self, an_obj: _T, **kwargs) -> bytes | _T:
        try:
            return self.bytesify(an_obj, **kwargs)  # type: ignore
        except TypeError:
            return an_obj

    def bytesify(self, an_obj: IsOrSupportsBytes, **kwargs) -> bytes:
        """
        :param an_obj: IsOrSupportsBytes, something to convert to bytes
        :raises TypeError: if an_obj has no 'to_bytes' or 'encode' method
        :return: bytes, an_obj converted to bytes
        """
        # Get default values for encoder methods' input options
        defaults = self.DEFAULTS.copy()
        defaults.update(kwargs)
        encoding = defaults.pop("encoding")

        match an_obj:
            case bytes():
                bytesified = an_obj
            case int():
                bytesified = int.to_bytes(an_obj, **defaults)
            case str():
                bytesified = str.encode(an_obj, encoding=encoding)
            case _:
                raise TypeError(f"Object {an_obj} cannot be "
                                "converted to bytes")
        return bytesified


class IterableMap:
    """ Base class for a custom object to emulate Mapping iter methods. """
    _KeyType = Hashable | None
    _KeyWalker = Generator[_KeyType, None, None]
    _Walker = Generator[tuple[_KeyType, Any], None, None]

    def __iter__(self) -> _KeyWalker:
        yield from self.keys()

    items: Callable[[], _Walker]  # Must be defined in subclass

    def keys(self) -> _KeyWalker:
        for k, _ in self.items():
            yield k

    def values(self) -> Generator[Any, None, None]:
        for _, v in self.items():
            yield v


class Subset:
    """ Filter object that can take a specific subset from any Mapping. """
    _M = TypeVar("_M", bound=Mapping)  # Type of Mapping to get subset(s) of
    _T = TypeVar("_T", bound=Mapping)  # Type of Mapping to return

    # Function that takes a key-value pair and returns True to include it
    # in the returned Mapping subset or False to exclude it; type(self.filter)
    Filter = Callable[[Hashable, Any], bool]

    def __init__(self, keys: Container[Hashable] = set(),
                 values: Container = set(), include_keys: bool = False,
                 include_values: bool = False) -> None:
        """
        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True for `filter` to return a subset \
            with ONLY the provided `keys`; else False to return a subset \
            with NONE OF the provided `keys`.
        :param include_values: bool, True for `filter` to return a subset \
            with ONLY the provided `values`; else False to return a subset \
            with NONE OF the provided `values`.
        """

        @staticmethod
        def passes_filter(k: Hashable, v: Any) -> bool:
            try:
                return (k in keys) is include_keys \
                    and (v in values) is include_values

            # If v isn't Hashable and values can only contain Hashables,
            except TypeError:  # then v cannot be in values
                return not include_values

        self.filter = passes_filter

    @overload
    def of(self, from_map: Mapping, as_type: type[_T]) -> _T: ...
    @overload
    def of(self, from_map: _M) -> _M: ...

    def of(self, from_map: Mapping, as_type: type | None = None):
        """ Construct an instance of this class by picking a subset of \
            key-value pairs to keep.

        :param from_map: Mapping to return a subset of.
        :param as_type: type[Mapping], type of Mapping to return; or None to \
            return the same type of Mapping as `from_map`.
        :return: Mapping, `from_map` subset including only the specified \
            keys and values
        """
        filtered = {k: v for k, v in from_map.items()
                    if self.filter(k, v)}
        if as_type is None:
            as_type = type(from_map)
        return as_type(filtered)


class Combinations:
    _T = TypeVar("_T")
    _Map = TypeVar("_Map", bound=Mapping)

    @staticmethod
    def of_bools(n: int) -> Generator[tuple[bool, ...], None, None]:
        """
        :param n: int, maximum length of each tuple to yield.
        :yield: Generator[tuple[bool, ...], None, None], all possible \
            combinations of `n` boolean values.
        """
        for conds in itertools.product((True, False), repeat=n):
            yield tuple(conds)

    @classmethod
    def of_map(cls, a_map: _Map) -> Generator[_Map, None, None]:
        """ Given a mapping, yield each possible subset of its item pairs.
        `d={1:1, 2:2}; Combinations.of_map(d)` yields `{1:1}`, `{2:2}`, & `d`.

        :param a_map: _Map, _description_
        :yield: Generator[_Map, None, None], _description_
        """
        for keys in cls.of_seq(a_map):
            yield Subset(keys=keys, include_keys=True).of(a_map)

    @staticmethod
    def of_seq(objects: Collection[_T]) -> itertools.chain[tuple[_T, ...]]:
        """ Return all possible combinations/subsequences of `objects`.
        Adapted from https://stackoverflow.com/a/31474532

        :param objects: Collection[_T]
        :return: itertools.chain[Collection], all `objects` combinations
        """
        return itertools.chain.from_iterable(
            itertools.combinations(objects, i + 1)
            for i in range(len(objects)))


class Traversible:
    """ Base class for recursive iterators that can visit all items in a \
        nested container data structure. """

    def __init__(self) -> None:
        self.traversed: set[int] = set()

    def _will_now_traverse(self, an_obj: Any) -> bool:
        """
        :param an_obj: Any, object to recursively visit while traversing
        :return: bool, False if `an_obj` was already visited, else True
        """
        objID = id(an_obj)
        not_traversed = objID not in self.traversed
        self.traversed.add(objID)
        return not_traversed


class Walk(Traversible, IterableMap):
    """ Recursively iterate over a Mapping and the Mappings nested in it. """
    _Walker = Generator[tuple[Hashable, Mapping], None, None]

    def __init__(self, from_map: Mapping,
                 only_yield_maps: bool = False) -> None:
        """ Initialize iterator that visits every item inside of a Mapping \
            once, including the items in the nested Mappings it contains.

        :param from_map: Mapping to visit every item of.
        :param only_yield_maps: bool, True for this iterator to return \
            key-value pairs only if the value is also a Mapping; else False \
            to return every item iterated over. Defaults to False.
        """
        Traversible.__init__(self)
        self.only_yield_maps = only_yield_maps
        self.root = from_map

    def _walk(self, key: Hashable | None, value: Mapping | Any) -> _Walker:
        # Only visit each item once; mark each as visited after checking
        if self._will_now_traverse(value):

            # Don't yield the initial/root/container/top Mapping itself
            isnt_root = value is not self.root

            try:  # If value is a dict, then visit each of ITS key-value pairs
                for k, v in value.items():
                    yield from self._walk(k, v)
                if isnt_root:  # Don't yield root
                    yield (key, value)

            # Yield non-Mapping items unless otherwise specified
            except AttributeError:
                if isnt_root and not self.only_yield_maps:
                    yield (key, value)

    def items(self) -> _Walker:
        """ Iterate over the key-value pairings in this Mapping and all of \
            nested Mappings recursively. 

        :yield: Iterator[tuple[Hashable | None, Any]], _description_
        """
        yield from self._walk(None, self.root)
