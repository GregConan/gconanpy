#!/usr/bin/env python3

"""
Useful/convenient classes to work with Python dicts/Mappings.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-05-12
"""
# Import standard libraries
from collections.abc import Callable, Container, Generator, Hashable, Mapping
from typing import Any, TypeVar


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
            as_type = type(from_map)
        return as_type({k: v for k, v in from_map.items()
                        if self.filter(k, v)})


class Traversible:
    def __init__(self) -> None:
        self.traversed: set[int] = set()

    def _will_traverse(self, an_obj: Any) -> bool:
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
    _Walker = Generator[tuple[_KeyType, Mapping], None, None]

    def __init__(self, a_map: Mapping) -> None:
        self.root = a_map
        self.traversed: set[int] = set()

    def _walk(self, key: _KeyType, value: Mapping | Any) -> _Walker:
        if self._will_traverse(value):
            try:
                for k, v in value.items():
                    yield from self._walk(k, v)
                yield (key, value)
            except AttributeError:
                pass

    def items(self) -> _Walker:
        yield from self._walk(None, self.root)

    def keys(self) -> Generator[_KeyType, None, None]:
        for key, _ in self.items():
            yield key

    def values(self) -> Generator[Mapping, None, None]:
        for _, value in self.items():
            yield value
