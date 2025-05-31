#!/usr/bin/env python3

"""
Useful/convenient classes to work with Python dicts/Mappings.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-05-31
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, Mapping
import sys
from typing import Any, SupportsBytes, TypeVar


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


class MapSubset:
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

    def of(self, from_map: _M, as_type: type[_T] | None = None) -> _M | _T:
        """ Construct an instance of this class by picking a subset of \
            key-value pairs to keep.

        :param from_map: Mapping to return a subset of.
        :param as_type: type[Mapping], type of Mapping to return; or None to \
            return the same type of Mapping as `from_map`.
        :return: Mapping, `from_map` subset including only the specified \
            keys and values
        """
        if as_type is None:
            as_type = type(from_map)  # type: ignore
        return as_type({k: v for k, v in from_map.items()
                        if self.filter(k, v)})  # type: ignore


class Traversible:
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


class WalkMap(Traversible):
    _KeyType = Hashable | None
    _KeyWalker = Generator[_KeyType, None, None]
    _Walker = Generator[tuple[_KeyType, Mapping], None, None]

    def __init__(self, a_map: Mapping) -> None:
        self.root = a_map
        self.traversed: set[int] = set()

    def __iter__(self) -> _KeyWalker:
        yield from self.keys()

    def _walk(self, key: _KeyType, value: Mapping | Any,
              yield_non_maps: bool = False) -> _Walker:
        if self._will_now_traverse(value):
            try:
                for k, v in value.items():
                    yield from self._walk(k, v, yield_non_maps)
                yield (key, value)
            except AttributeError:
                if yield_non_maps:
                    yield (key, value)

    def items(self) -> _Walker:
        yield from self._walk(None, self.root)

    def keys(self) -> _KeyWalker:
        for key, _ in self.items():
            yield key

    def values(self) -> Generator[Mapping, None, None]:
        for _, value in self.items():
            yield value
