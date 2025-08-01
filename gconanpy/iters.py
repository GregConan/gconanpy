#!/usr/bin/env python3

"""
Useful/convenient lower-level utility functions and classes primarily to \
    access and manipulate Iterables, especially nested Iterables.
Greg Conan: gregmconan@gmail.com
Created: 2025-07-28
Updated: 2025-07-29
"""
# Import standard libraries
from collections.abc import Callable, Collection, Container, Generator, \
    Hashable, Iterable, Mapping, Sequence
from functools import reduce
import itertools
from more_itertools import all_equal
import random
import string
import sys
from typing import Any, overload, SupportsBytes, TypeVar

# Import local custom libraries
try:
    from meta import method, Traversible, Updatable
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.meta import method, Traversible, Updatable

# Constant: TypeVars for...
I = TypeVar("I", bound=Iterable)  # ...combine
S = TypeVar("S")  # ...differentiate_sets
U = TypeVar("U", bound=Updatable)  # ...merge

# NOTE Functions are in alphabetical order. Classes are in dependency order.


def are_all_equal(comparables: Iterable, eq_meth: str | None = None,
                  reflexive: bool = False) -> bool:
    """ `are_all_equal([a, b, c, d, e])` means `a == b == c == d == e`.

    :param comparables: Iterable of objects to compare.
    :param eq_meth: str naming the method of every item in comparables to \
        call on every other item. `==` (`__eq__`) is the default comparison.
        `are_all_equal((a, b, c), eq_meth="isEqualTo")` means \
        `a.isEqualTo(b) and a.isEqualTo(c) and b.isEqualTo(c)`.
    :param reflexive: bool, True to compare each possible pair of objects in \
        `comparables` forwards and backwards.
        `are_all_equal({x, y}, eq_meth="is_like", reflexive=True)` means \
        `x.is_like(y) and y.is_like(x)`.
    :return: bool, True if calling the `eq_meth` method attribute of every \
        item in comparables on every other item always returns True; \
        otherwise False.
    """
    if not eq_meth:
        result = all_equal(comparables)
    else:
        are_both_equal = method(eq_meth)
        pair_up = itertools.permutations if reflexive \
            else itertools.combinations
        result = True
        for pair in pair_up(comparables, 2):
            if not are_both_equal(*pair):
                result = False
                break
    return result


def combine_lists(lists: Iterable[list]) -> list:
    """
    :param lists: Iterable[list], objects to combine
    :return: list combining all of the `lists` into one
    """
    return list(itertools.chain.from_iterable(lists))


def default_pop(poppable: Any, key: Any = None,
                default: Any = None) -> Any:
    """
    :param poppable: Any object which implements the .pop() method
    :param key: Input parameter for .pop(), or None to call with no parameters
    :param default: Object to return if running .pop() raises an error
    :return: Object popped from poppable.pop(key), if any; otherwise default
    """
    try:
        to_return = poppable.pop() if key is None else poppable.pop(key)
    except (AttributeError, IndexError, KeyError):
        to_return = default
    return to_return


def differentiate_sets(sets: list[set[S]]) -> list[set[S]]:
    """ Remove all shared/non-unique items from sets until they no longer \
    overlap/intersect at all.

    :param sets: Iterable[set[T]], _description_
    :return: list[set[T]], unique items in each set
    """
    to_return = list()
    for i in range(len(sets)):
        for other_set in sets[:i] + sets[i+1:]:
            to_return[i] = sets[i] - other_set
    return to_return


def have_same_elements(*settables: Iterable) -> bool:
    return all_equal(set(an_obj) for an_obj in settables)


def merge(updatables: Iterable[U]) -> U:
    """ Merge dicts, sets, or things of any type with an `update` method.

    :param updatables: Iterable[Updatable], objects to combine
    :return: Updatable combining all of the `updatables` into one
    """
    return reduce(lambda x, y: x.update(y) or x, updatables)


def powers_of_ten(orders_of_magnitude: int = 4) -> list[int]:
    return [10 ** i for i in range(orders_of_magnitude + 1)]


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


class Randoms:
    # Type hint class variables
    _KT = TypeVar("_KT", bound=Hashable)  # for randict method
    _VT = TypeVar("_VT")  # for randict method
    _T = TypeVar("_T")  # for randsublist method

    # Default parameter value class variables
    BIGINT = sys.maxunicode  # Default arbitrary huge integer
    CHARS = tuple(string.printable)  # String characters to randomly pick
    MIN = 1    # Default minimum number of items/tests
    MAX = 100  # Default maximum number of items/tests

    @classmethod
    def randict(cls, keys: Sequence[_KT] = CHARS,
                values: Sequence[_VT] = CHARS,
                min_len: int = MIN, max_len: int = MAX) -> dict[_KT, _VT]:
        return {random.choice(keys): random.choice(values)
                for _ in cls.randrange(min_len, max_len)
                } if keys and values else dict()

    @classmethod
    def randints(cls, min_n: int = MIN, max_n: int = MAX,
                 min_int: int = -BIGINT, max_int: int = BIGINT
                 ) -> Generator[int, None, None]:
        for _ in cls.randrange(min_n, max_n):
            yield random.randint(min_int, max_int)

    @classmethod
    def randintsets(cls, min_n: int = 2, max_n: int = MAX,
                    min_len: int = MIN, max_len: int = MAX,
                    min_int: int = -BIGINT, max_int: int = BIGINT
                    ) -> list[set[int]]:
        return [set(cls.randints(min_len, max_len, min_int, max_int))
                for _ in cls.randrange(min_n, max_n)]

    @staticmethod
    def randrange(min_len: int = MIN, max_len: int = MAX) -> range:
        return range(random.randint(min_len, max_len))

    @staticmethod
    def randsublist(seq: Sequence[_T], min_len: int = 0,
                    max_len: int = 100) -> list[_T]:
        return random.choices(seq, k=random.randint(
            min_len, min(max_len, len(seq))))


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


class SimpleShredder(Traversible):
    SHRED_ERRORS = (AttributeError, TypeError)

    def shred(self, an_obj: Any) -> set:
        """ Recursively collect/save the attributes, items, and/or elements \
            of an_obj regardless of how deeply they are nested. Return only \
            the Hashable data in an_obj, not the Containers they're in.

        :param an_obj: Any, object to return the parts of.
        :return: set of the particular Hashable non-Container data in an_obj
        """
        try:  # If it's a string, then it's not shreddable, so save it
            self.parts.add(an_obj.strip())
        except self.SHRED_ERRORS:

            try:  # If it's a non-str Iterable, then shred it
                iter(an_obj)
                self._shred_iterable(an_obj)

            # Hashable but not Iterable means not shreddable, so save it
            except TypeError:
                self.parts.add(an_obj)
        return self.parts

    def _shred_iterable(self, an_obj: Iterable) -> None:
        """ Save every item in an Iterable regardless of how deeply nested, \
            unless that item is "shreddable" (a non-string data container).

        :param an_obj: Iterable to save the "shreddable" elements of.
        """
        # If we already shredded it, then don't shred it again
        if self._will_now_traverse(an_obj):

            try:  # If it has a __dict__, then shred that
                self._shred_iterable(an_obj.__dict__)
            except self.SHRED_ERRORS:
                pass

            # Shred or save each of an_obj's...
            try:  # ...values if it's a Mapping
                for v in an_obj.values():  # type: ignore
                    self.shred(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not a Mapping
                for element in an_obj:
                    self.shred(element)

    def reset(self) -> None:
        """
        Remove all previously collected parts and their traversal record.
        """
        Traversible.__init__(self)
        self.parts: set = set()

    __init__ = reset


class Combinations:
    _T = TypeVar("_T")
    _Map = TypeVar("_Map", bound=Mapping)

    @classmethod
    def excluding(cls, objects: Collection[_T], exclude: Iterable[_T]
                  ) -> Generator[tuple[_T, ...], None, None]:
        excluset = set(exclude)
        for combo in cls.of_seq(objects):
            if set(combo).isdisjoint(excluset):
                yield combo

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
            yield MapSubset(keys=keys, include_keys=True).of(a_map)

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


class MapWalker(Traversible, IterableMap):
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
