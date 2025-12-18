#!/usr/bin/env python3

"""
Useful/convenient lower-level utility functions and classes primarily to \
    access and manipulate Iterables, especially nested Iterables.
Greg Conan: gregmconan@gmail.com
Created: 2025-07-28
Updated: 2025-12-17
"""
# Import standard libraries
import abc
from collections.abc import Callable, Collection, Generator, \
    Hashable, Iterable, Iterator, Mapping, Sequence
import functools
import itertools
from more_itertools import all_equal
import random
import string
import sys
from typing import Any, cast, Literal, overload, ParamSpec, Self, TypeVar

# Import local custom libraries
try:
    from gconanpy.iters.filters import MapSubset
    from gconanpy.meta import divmod_base, method, Traversible, tuplify
    from gconanpy.meta.typeshed import Poppable, Updatable
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from iters.filters import MapSubset
    from meta import divmod_base, method, Traversible, tuplify
    from meta.typeshed import Poppable, Updatable

# TypeVars to define type hints for...
_H = TypeVar("_H", bound=Hashable)      # ...invert & uniqs_in
_Map = TypeVar("_Map", bound=Mapping)   # ...Combinations.of_map
_P = ParamSpec("_P")                    # ...exhaust_wrapper
_Seq = TypeVar("_Seq", bound=Sequence)  # ...seq_*
_T = TypeVar("_T")    # ...*duplicate*, subseq_*, & Combinations.randsublist
_U = TypeVar("_U", bound=Updatable)     # ...merge & update_return
RANDATUM = TypeVar("RANDATUM", bool, bytes, float, int, None, str
                   )  # ...Randoms.randata & Randoms.randatum

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
        return all_equal(comparables)
    else:
        are_both_equal = method(eq_meth)
        pair_up = itertools.permutations if reflexive \
            else itertools.combinations
        for pair in pair_up(comparables, 2):
            if not are_both_equal(*pair):
                return False
        return True


def combine_lists(lists: Iterable[list]) -> list:
    """
    :param lists: Iterable[list], objects to combine
    :return: list combining all of the `lists` into one
    """
    return list(itertools.chain.from_iterable(lists))


def copy_range(a_range: range) -> range:
    """ 
    :param a_range: range
    :return: range, a new copy of `a_range` that has not been iterated yet
    """
    return range(a_range.start, a_range.stop, a_range.step)


def deduplicate_keep_order(parts: Sequence[_T]) -> list[_T]:
    """
    Remove duplicate `parts` without changing the order of `parts`.

    :param parts: Sequence[_T] to remove duplicate elements from
    :return: list[_T], `parts` without duplicate elements
    """
    # Can't just turn into a set and back bc we need to preserve order
    new_parts = [parts[0]]
    for part in parts[1:]:
        if part not in new_parts:
            new_parts.append(part)
    return new_parts


def default_pop(poppable: Poppable, key: Any = None,
                default: Any = None) -> Any:
    """
    :param poppable: Any object which implements the .pop() method
    :param key: Input parameter for .pop(), or None to call with no parameters
    :param default: Object to return if running .pop() raises an error
    :return: Object popped from poppable.pop(key), if any; otherwise default
    """
    try:
        return poppable.pop() if key is None else poppable.pop(key)
    except (AttributeError, IndexError, KeyError):
        return default


def duplicates_in(a_seq: Sequence[_T]) -> list[_T]:
    """ 
    :param a_seq: Sequence[T: Any] to check for duplicate elements
    :return: list[T], everything that appears more than once in `a_seq`
    """
    return [x for x in a_seq if a_seq.count(x) > 1]


def exhaust(itr: Iterator, max_loops: int = sys.maxsize) -> None:
    """ Given an iterator, exhaust it by iterating it until it has \
        no values left to yield. Ignores values yielded.

    :param itr: Iterator, generator function to exhaust
    :param max_loops: int, maximum number of times to try getting the next \
        value from `itr`
    """
    try:
        for _ in range(max_loops):
            next(itr)
    except StopIteration:
        pass


def exhaust_wrapper(gen_func: Callable[_P, Generator],
                    max_loops: int = sys.maxsize) -> Callable[_P, None]:
    """ Given a generator function, wrap it in an redundant inner function \
        that will exhaust it by iterating it until it has no values left to \
        yield and ignores values yielded.

    :param gen_func: Callable[P, Generator], generator function
    :param max_loops: int, maximum number of times to try getting the next \
        value from the `gen_func(...)` when the returned function is called
    """
    @functools.wraps(gen_func)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> None:
        exhaust(gen_func(*args, **kwargs), max_loops)
    return inner


def filter_sequence_generator(ix: int) -> Callable[
    [Callable[_P, Generator[Sequence[_T], None, None]]],
    Callable[_P, Generator[_T, None, None]]
]:
    """ `operator.itemgetter` for `Sequence`s yielded by `Generator`s. \
        Works on `method_descriptor`s.

    Call this with an index and use the returned function as a decorator on \
    a generator function to only yield the specified index of the Sequence \
    yielded by that generator function.

    E.g. `filter_generator(0)(dict.items)` replicates `dict.keys` iteration \
    and `filter_generator(1)(dict.items)` replicates `dict.values` iteration.

    :param ix: int, index of an input generator's yielded Sequence for the \
        returned function to yield
    :return: Callable[[Callable[_P, Generator[Sequence[_T], None, None]]], \
        Callable[_P, Generator[_T, None, None]]], function that accepts a \
        generator function yield Sequences and returns a generator function \
        yielding only the elements at the specified index of those Sequences.
    """
    def outer(func: Callable[_P, Generator[Sequence[_T], None, None]]
              ) -> Callable[_P, Generator[_T, None, None]]:
        @functools.wraps(func)
        def inner(*args: _P.args, **kwargs: _P.kwargs
                  ) -> Generator[_T, None, None]:
            for item in func(*args, **kwargs):
                yield item[ix]
        return inner
    return outer


def has_any(iterable: Iterable, *items: Any) -> bool:
    """
    :param iterable: Iterable to check whether it contains any of the `items`
    :return: bool, True if any item in `items` is in `iterable`; else False
    """
    for item in items:
        if item in iterable:
            return True
    return False


def invert_range(a_range: range) -> range:
    """ Same as `reversed(a_range)`, but returns a freshly copied `range`.

    :param a_range: range
    :return: range, inverted (reversed) copy of `a_range`
    """
    return range(a_range.stop - a_range.step,
                 a_range.start - a_range.step, -a_range.step)


def merge(updatables: Iterable[_U]) -> _U:
    """ Merge dicts, sets, or things of any type with an `update` method.

    Warning: this function modifies the original objects.

    :param updatables: Iterable[Updatable], objects to combine
    :return: Updatable combining all of the `updatables` into one
    """
    # return reduce(lambda x, y: x.update(y) or x, updatables)
    return functools.reduce(update_return, updatables)


def powers_of_ten(orders_of_magnitude: int = 4) -> list[int]:
    """ 
    :param orders_of_magnitude: int, maximum power that 10 will be raised \
        to in the output `list`; defaults to 4
    :return: list[int], 10 raised to the power of 1, then 2, then ..., \
        then `orders_of_magnitude`.
    """
    return [10 ** i for i in range(orders_of_magnitude + 1)]


def seq_startswith(seq: _Seq, prefix: _Seq) -> bool:
    """ Check if prefix is the beginning of seq.

    :param seq: Sequence, _description_
    :param prefix: Sequence, _description_
    :return: bool, True if seq starts with the specified prefix, else False.
    """
    return len(seq) >= len(prefix) and seq[:len(prefix)] == prefix


def seq_truncate(a_seq: _Seq, max_len: int) -> _Seq:
    """ Cut off the end of `a_seq` if it's longer than `max_len`.

    :param a_seq: Sequence[_T: Any]
    :param max_len: int, number of items to include in the output `Sequence`
    :return: Sequence[_T: Any], the FIRST `max_len` items in `a_seq`
    """
    return cast(_Seq, a_seq[:max_len]) if len(a_seq) > max_len else a_seq


def seq_rtruncate(a_seq: _Seq, max_len: int) -> _Seq:
    """  Cut off the beginning of `a_seq` if it's longer than `max_len`.

    :param a_seq: Sequence[_T: Any]
    :param max_len: int, number of items to include in the output `Sequence`
    :return: Sequence[_T: Any], the LAST `max_len` items in `a_seq`
    """
    return cast(_Seq, a_seq[-max_len:]) if len(a_seq) > max_len else a_seq


def subseq_indices(subseq: Sequence[_T], a_seq: Sequence[_T]
                   ) -> Generator[tuple[int, int], None, None]:
    """ Get the start and end indices of one sequence within another.

    For each instance of `subseq` within `a_seq`, get the index within `a_seq`
    where it starts and the index within `a_seq` where it ends.

    :param subseq: Sequence[_T] contained within `a_seq`; `a_seq` subsequence 
    :param a_seq: Sequence[_T] that contains `subseq`
    :yield: Generator[tuple[int, int], None, None], a (Start_Index, End_Index)
        pair for each instance of `subseq` within `a_seq` 
    """
    subseq_len = len(subseq)
    for start_ix in (i for i, el in enumerate[_T](a_seq) if el == subseq[0]):
        end_ix = start_ix + subseq_len
        if a_seq[start_ix:end_ix] == subseq:
            yield (start_ix, end_ix - 1)


def startswith(an_obj: Any, prefix: Any,  # TODO Move to duck.py ?
               stringify: Callable[[Any], str] = str) -> bool:
    """ Check if the beginning of an_obj is prefix.
        Type-agnostic extension of str.startswith and bytes.startswith.

    :param an_obj: Any, _description_
    :param prefix: Any, _description_
    :param stringify: Callable[[Any], str], function to convert any objecct \
        into a string for sequence comparison; defaults to `str`
    :return: bool, True if an_obj starts with the specified prefix, else False
    """
    try:
        try:
            result = an_obj.startswith(prefix)
        except AttributeError:  # then an_obj isn't a str, bytes or BytesArray
            result = seq_startswith(an_obj, prefix)
    except TypeError:  # then an_obj isn't a Sequence or prefix isn't
        result = seq_startswith(stringify(an_obj), stringify(prefix))
    return result


def uniqs_in(listlike: Iterable[_H], stringify: Callable[[Any], str] = str
             ) -> list[_H]:
    """Alphabetize and list the unique elements of an iterable.
        To list non-private local variables' names, call `uniqs_in(locals())`.

    :param listlike: Iterable[Hashable] to get the unique elements of
    :return: list[Hashable] (sorted) of all unique strings in listlike \
             that don't start with an underscore
    """
    uniqs = [*set([v for v in listlike if not startswith(v, "_", stringify)])]
    uniqs.sort()  # pyright: ignore[reportCallIssue]  # TODO?
    return uniqs


def update_return(self: _U, other: _U) -> _U:
    """ Update `self` with values/items from `other`. Used by `merge` function

    :param self: Updatable, object to update with new values
    :param other: Updatable, new values to update `self` with
    :return: Updatable, `self` after updating it with the values from `other`
    """
    return self.update(other) or self


class Randoms:
    """ Various methods using the `random` library to randomly select or \
        generate values. Useful for generating arbitrary test data. """

    # Type hint class variables
    _KT = TypeVar("_KT", bound=Hashable)  # for randict method
    _VT = TypeVar("_VT")  # for randict method

    # Default parameter value class variables
    BIGINT = sys.maxunicode  # Default arbitrary huge integer
    CHARS = tuple(string.printable)  # String characters to randomly pick
    MIN = 1    # Default minimum number of items/tests
    MAX = 100  # Default maximum number of items/tests
    RANDTYPES: tuple[type | None, ...] = RANDATUM.__constraints__

    _TYPES = type | Sequence[type | None]

    @staticmethod
    def _int_or_randint(int_or_pair: int | tuple[int, int]) -> int:
        """ Return or randomly generate an int. Defined for use by methods \
            with parameters to optionally provide OR randomly generate.

        :param int_or_pair: int | tuple[int, int], either the int to return \
            or a (min, max) range to randomly generate an int between.
        :return: int, either the provided int or a randomly generated int \
            within the provided range.
        """
        try:
            pair = cast(tuple[int, int], int_or_pair)
            return random.randint(pair[0], pair[1])
        except TypeError:
            return cast(int, int_or_pair)

    @classmethod
    def randbool(cls, *_) -> bool:
        """ Taken from https://stackoverflow.com/a/6824868 

        Accepts and ignores positional input parameters for more convenient \
        use by `Randoms.randatum`.

        :return: bool, a 50% random chance of either True or False.
        """
        return bool(random.getrandbits(1))

    @classmethod
    def randata(cls, min_val: int = MIN, max_val: int = 10 * MAX,
                min_n: int = MIN, max_n: int = MAX,
                dtypes: type[RANDATUM] | Sequence[type[RANDATUM] | None]
                = RANDTYPES, weights: Sequence[float] | bool | None = True
                ) -> Generator[RANDATUM, None, None]:
        """ Generate a random number of random values of random types.

        :param min_val: int, the lowest `int` or `float` to return, or the \
            length of the shortest `bytes` or `str` to return; defaults to 1
        :param max_val: int, the highest `int` or `float` to return, or the \
            length of the longest `bytes` or `str` to return; defaults to 1000
        :param min_n: int, lowest number of values to return; defaults to 1
        :param max_n: int, highest number of values to return; defaults to 100
        :param dtypes: type[RANDATUM] | Sequence[type[RANDATUM | None] | \
            None], type(s) of object(s)/value(s) to return; defaults to \
            `(bool, bytes, float, int, None, str)`
        :param weights: Sequence[float] | bool | None, Sequence of relative \
            probability weights of returning each type in `types`; or True \
            to weigh `None` as 1, `bool` as 2, and each other type as the \
            `max_val - min_val` range; or False or None to assign \
            equal (no) weight to all types; defaults to True.
        :raises ValueError: if `types` and `weights` are different lengths.
        :yield: Generator[Any, None, None], a random number (between `min_n` \
            and `max_n`) of randomly generated instances of types randomly \
            chosen from the provided `types`
        """
        types_tup: tuple[type[RANDATUM] | None, ...] = tuplify(dtypes)
        if (not weights) or len(types_tup) < 2:
            weights = None  # [1.0] * len(types_tup)
        elif weights is True:
            num_range = float(abs(min_val - max_val))
            default_weights = {bool: 2.0, None: 1.0}
            weights = [default_weights.get(each_type, num_range)
                       for each_type in types_tup]
        elif len(weights) != len(types_tup):
            raise ValueError(f"weights length ({len(weights)}) must match "
                             f"types length ({len(types_tup)})")
        n = random.randint(min_n, max_n)
        for each_type in random.choices(types_tup, weights=weights, k=n):
            yield cast(RANDATUM, cls.randatum(each_type, min_val, max_val))

    @overload
    @classmethod
    def randatum(cls, of_type: None, min_val, max_val) -> None: ...

    @overload
    @classmethod
    def randatum(cls, of_type: type[RANDATUM], min_val: int, max_val: int
                 ) -> RANDATUM: ...

    @classmethod
    def randatum(cls, of_type: type[RANDATUM] | None, min_val=MIN,
                 max_val=10 * MAX):  # x10 for more int/float variation (?)
        """
        :param of_type: type[RANDATUM] | None, type of object to return.
        :param min_val: int, the lowest `int` or `float` to return, or the \
            length of the shortest `bytes` or `str` to return; defaults to 1
        :param max_val: int, the highest `int` or `float` to return, or the \
            length of the longest `bytes` or `str` to return; defaults to 1000
        :return: RANDATUM, an instance `of_type` with random contents.
        """
        if of_type is not None:  # "else return None" is implicit

            try:  # Define dict here bc "cls.xyz" has 1 fewer arg than "xyz"
                ret = {bool: cls.randbool, float: random.uniform,
                       int: random.randint, str: cls.randstr
                       }[of_type](min_val, max_val)
            except KeyError:
                if of_type is bytes:
                    ret = random.randbytes(random.randint(min_val, max_val))
            return cast(RANDATUM, ret)

    @classmethod
    def randict(cls, keys: Sequence[_KT] | None = None,
                values: Sequence[_VT] | None = None,
                min_len: int = MIN, max_len: int = MAX,
                key_types: _TYPES = RANDTYPES,
                value_types: _TYPES = RANDTYPES) -> dict[_KT, _VT]:
        """ 
        :param keys: Sequence[_KT] | None, possible keys to use in the \
            returned dict, or None to use random data; defaults to None.
        :param values: Sequence[_VT] | None, possible values to include in \
            the returned dict, or None to use random data; defaults to None.
        :param min_len: int, length of smallest dict to return, defaults to 1
        :param min_len: int, length of biggest dict to return, defaults to 100
        :param key_types: type | Sequence[type | None], types of random data \
            to use as `keys` if `keys=None`; defaults to `RANDTYPES`
        :param value_types: type | Sequence[type | None], types of random \
            data to use as `values` if `values=None`; defaults to `RANDTYPES`
        :return: dict[_KT, _VT], dict with random size and contents.
        """
        n = random.randint(min_len, max_len)
        keys = cls.randtuple(n, keys, key_types)
        values = cls.randtuple(n, values, value_types)
        return {k: v for k, v in zip(keys, values)}

    @classmethod
    def randints(cls, min_n: int = MIN, max_n: int = MAX,
                 min_int: int = -BIGINT, max_int: int = BIGINT
                 ) -> Generator[int, None, None]:
        for _ in cls.randcount(min_n, max_n):
            yield random.randint(min_int, max_int)

    @classmethod
    def randintsets(cls, min_n: int = 2, max_n: int = MAX,
                    min_len: int = MIN, max_len: int = MAX,
                    min_int: int = -BIGINT, max_int: int = BIGINT
                    ) -> list[set[int]]:
        return [set(cls.randints(min_len, max_len, min_int, max_int))
                for _ in cls.randcount(min_n, max_n)]

    @staticmethod
    def randcount(min_len: int = MIN, max_len: int = MAX) -> range:
        return range(random.randint(min_len, max_len))

    @classmethod
    def randrange(cls, start: int | tuple[int, int] = 0,
                  stop: int | tuple[int, int] = (1, BIGINT),
                  step: int | tuple[int, int] = 1) -> range:
        return range(cls._int_or_randint(start),
                     cls._int_or_randint(stop),
                     cls._int_or_randint(step))

    @classmethod
    def randtuple(cls, length: int, values: Sequence[_VT] | None = None,
                  value_types: _TYPES = RANDTYPES):
        """
        :param length: int, number of items in the tuple to return.
        :param values: Sequence[_VT] | None, items to randomly select from; \
            if none are provided, randomly generate items 
        :param value_types: type | Sequence[type | None], type of items to \
            randomly generate if no `values` are provided; defaults to \
            `(bool, bytes, float, int, None, str)`
        :return: _type_, _description_
        """
        if values:
            ret = random.choices(values, k=length)
        else:
            kwargs: dict[str, Any] = dict(min_n=length, max_n=length)
            if value_types:
                kwargs["dtypes"] = value_types
            ret = cls.randata(**kwargs)
        return tuple(ret)

    @classmethod
    def randtuples(cls, values: Sequence[_VT] | None = None, min_n: int = MIN,
                   max_n: int = MAX, min_len: int = MIN, max_len: int = MAX,
                   same_len: bool = False, unique: bool = False
                   ) -> list[tuple[_VT, ...]]:
        """
        :param values: Sequence[_VT] | None, items to randomly select and \
            place into the returned tuples, or None to include random values \
            of random basic data types \
            `(bool, bytes, float, int, None, str)`; defaults to None
        :param min_n: int, minimum number of tuples to return; defaults to 1
        :param max_n: int, maximum number of tuples to return; defaults to 100
        :param min_len: int, minimum tuple length; defaults to 1
        :param max_len: int, maximum tuple length; defaults to 100
        :param same_len: bool, True to return a list of tuples that all have \
            exactly the same number of items; else False; defaults to False
        :param unique: bool, True to return a list of unique tuples; else \
            False to return a list of tuples potentially including \
            duplicates; defaults to False
        :return: list[tuple[_VT, ...]], list of randomly generated tuples
        """
        tuples = []  # to return

        # Make them all the same length if specified
        tup_len = random.randint(min_len, max_len) if same_len else None
        for _ in cls.randcount(min_n, max_n):

            # Otherwise, vary the length
            if tup_len is None:
                tup_len = random.randint(min_len, max_len)

            # Make them unique if specified
            a_tup = cls.randtuple(tup_len, values)
            while unique and (a_tup in tuples):
                a_tup = cls.randtuple(tup_len, values)

            tuples.append(a_tup)
        return tuples

    @classmethod
    def randstr(cls, min_len: int = MIN, max_len: int = MAX,
                values: Sequence[str] = CHARS) -> str:
        """ 
        :param min_len: int, length of shortest possible string to return; \
            defaults to 1
        :param max_len: int, length of longest possible string to return;
            defaults to 100
        :param values: Sequence[str], possible chars to include in the \
            returned string;, defaults to `string.printable`
        :return: str, string with random length and contents
        """
        return "".join(cls.randsublist(values, min_len, max_len))

    @staticmethod
    def randsublist(seq: Sequence[_T], min_len: int = 0,
                    max_len: int = MAX) -> list[_T]:
        """
        :param seq: Sequence[_T], possible values to randomly select from
        :param min_len: int, length of the shortest possible list to return; \
            defaults to 0
        :param max_len: int, length of the longest possible list to return; \
            defaults to 100
        :return: list[_T], a random number of randomly selected items in `seq`
        """
        return random.choices(seq, k=random.randint(
            min_len, min(max_len, len(seq))))


class ColumnNamer:
    """ Iterator that converts column numbers into their corresponding \
        letter combinations in the manner used by Microsoft Excel.

    Adapted from https://stackoverflow.com/a/48984697 """

    def __init__(self, letters: str = string.ascii_uppercase,
                 start_at: int = 1) -> None:
        """
        :param letters: str, values to pick from to construct column names; \
            defaults to the uppercase alphabet to mimic MS Excel.
        :param start_at: int, starting index / column number; defaults to 1.
        """
        self.letters = letters
        self.ix = self.offset = start_at

        # Numerical base (how many unique digits can represent a number) plus
        # the method to convert integers from that base to base 10 and back
        radix = len(letters)
        self.base = radix
        self._divmod = staticmethod(divmod_base(radix))

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> str:
        ret = self.num2name(self.ix)
        self.ix += 1
        return ret

    def _col_num_base_10(self, col_num: int, remainder: int) -> int:
        return col_num * self.base + remainder + self.offset

    def num2name(self, col_num: int) -> str:
        """
        :param col_num: int, column number/index
        :return: str, the letter combination naming that column
        """
        chars = []
        while col_num > 0:
            col_num, remainder = self._divmod(col_num)
            chars.append(self.letters[remainder - 1])
        return "".join(reversed(chars))

    def name2num(self, col_name: str) -> int:
        """
        :param col_name: str, letter combination naming a column
        :return: int, that column number/index
        """
        return functools.reduce(self._col_num_base_10, map(
            self.letters.index, col_name), 0)

    def reset(self) -> Self:
        return type(self)(self.letters, self.offset)


class SimpleShredder(Traversible):
    """ Iterator to recursively extract data from nested containers. """
    SHRED_ERRORS = (AttributeError, TypeError)

    def __init__(self) -> None:
        """ Reset; clear traversal record by removing all collected parts. """
        Traversible.__init__(self)
        self.parts: set = set()

    def shred(self, an_obj: Any) -> set:
        """ Recursively collect/save the attributes, items, and/or elements \
            of an_obj regardless of how deeply they are nested. Return only \
            the Hashable data in an_obj, not the Containers they're in.

        :param an_obj: Any, object to return the parts of.
        :return: set of the particular Hashable non-Container data in an_obj
        """
        try:  # If it's a string/bytes, then it's not shreddable, so save it
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
                for v in cast(Mapping, an_obj).values():
                    self.shred(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not a Mapping
                for element in an_obj:
                    self.shred(element)

    reset = __init__


class Combinations:

    @classmethod
    def excluding(cls, objects: Collection[_T], exclude: Iterable[_T]
                  ) -> Generator[tuple[_T, ...], None, None]:
        """ Return all possible combinations/subsequences of `objects`, \
            excluding certain objects.

        :param objects: Collection[_T] to get combinations of
        :param exclude: Iterable[_T], objects not to include in combinations
        :yield: Generator[tuple[_T, ...], None, None], all combinations of \
            `objects` excluding the values in `exclude`.
        """
        excluset = set(exclude)
        for combo in cls.of_objects(objects):
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
        :yield: Generator[_Map: Mapping, None, None], _description_
        """
        for keys in cls.of_objects(a_map):
            yield MapSubset(keys_are=keys).of(a_map)

    @staticmethod
    def of_objects(objects: Collection[_T]) -> itertools.chain[tuple[_T, ...]]:
        """ Return all possible combinations/subsequences of `objects`.
        Adapted from https://stackoverflow.com/a/31474532

        :param objects: Collection[_T] to get combinations of
        :return: itertools.chain[Collection], all `objects` combinations
        """
        return itertools.chain.from_iterable(
            itertools.combinations(objects, i + 1)
            for i in range(len(objects)))

    @classmethod
    def of_uniques(cls, objects: Collection[_H], min_n: int = 1,
                   max_n: int | None = None
                   ) -> Generator[tuple[_H, ...], None, None]:
        """ Get every combination of unique `objects`.

        :param objects: Collection[_H: Hashable] to get combinations of
        :param min_n: int, smallest yielded tuple length; defaults to 1
        :param max_n: int | None, largest yielded tuple length; defaults 
            to None, meaning the number of `objects` (its length)
        :yield: Generator[tuple[_H, ...], None, None], each combination of \
            `objects` with no repeated values
        """
        if max_n is None:
            max_n = len(objects)
        for n in range(min_n, max_n + 1):
            for combo in itertools.product(objects, repeat=n):
                if len(set(combo)) == len(combo):
                    yield combo


class IterableMap[KT: Hashable | None, VT: Any](abc.ABC):
    """ Base class for a custom object to emulate `Mapping` iter methods. """

    def __iter__(self) -> Generator[KT, None, None]:
        for k, _ in self.items():
            yield k

    @abc.abstractmethod
    def items(self) -> Generator[tuple[KT, VT], None, None]: ...

    def keys(self) -> Generator[KT, None, None]:
        yield from self

    def values(self) -> Generator[VT, None, None]:
        for _, v in self.items():
            yield v


class MapWalker[KT: Hashable, VT: Any](Traversible, IterableMap[KT, VT]):
    """ Recursively iterate over a Mapping and the Mappings nested in it. """

    def __init__(self, from_map: Mapping[KT, VT],
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

    @overload
    def _walk(self, key: KT | None, value: Mapping[KT, VT] | VT,
              only_yield_maps: Literal[True]
              ) -> Generator[tuple[KT, Mapping[KT, VT]], None, None]: ...

    @overload
    def _walk(self, key: KT | None, value: Mapping[KT, VT] | VT,
              only_yield_maps: None | Literal[False] = False
              ) -> Generator[tuple[KT, VT | Mapping[KT, VT]], None, None]: ...

    def _walk(self, key, value, only_yield_maps: bool | None = None):
        """
        :param key: KT | None, the key mapped to `value` in the parent dict, \
            or None if `value` is the top-level `dict`; first item yielded
        :param value: Mapping[KT, VT] | VT, the `value` mapped to `key` in \
            the parent dict, to recursively walk if it's a Mapping itself;
            second item yielded
        :param only_yield_maps: bool | None, True for this iterator to yield \
            key-value pairs only if the value is also a Mapping; else False \
            to yield every item iterated over. Defaults to None to use the \
            `self.only_yield_maps` variable defined at initialization.
        :yield: Generator[tuple[KT, VT | Mapping[KT, VT]], None, None], \
            first `(key, value)` unless `value` is the root `Mapping`, then \
            every key-value pair in `value` if it's a `Mapping`, and so on \
            recursively iterating over every `Mapping` nested in `value`
        """
        # Only visit each item once; mark each as visited after checking
        if self._will_now_traverse(value):

            # Don't yield the initial/root/container/top Mapping itself
            isnt_root = value is not self.root

            if only_yield_maps is None:
                only_yield_maps = self.only_yield_maps

            try:  # If value is a dict, then visit each of ITS key-value pairs
                for k, v in cast(Mapping, value).items():
                    yield from self._walk(k, v, only_yield_maps)
                if isnt_root:  # Don't yield root
                    yield (cast(KT, key), value)

            # Yield non-Mapping items unless otherwise specified
            except AttributeError:
                if isnt_root and not only_yield_maps:
                    yield (cast(KT, key), value)

    @overload
    def items(self, only_yield_maps: Literal[True]
              ) -> Generator[tuple[KT, Mapping[KT, VT]], None, None]: ...

    @overload
    def items(self, only_yield_maps: None | Literal[False] = None
              ) -> Generator[tuple[KT, VT | Mapping[KT, VT]], None, None]: ...

    def items(self, only_yield_maps: bool | None = None):
        """ 
        :yield: Generator[tuple[KT, VT | Mapping[KT, VT]], None, None], \
            the key-value pairings in this Mapping and all of the nested \
            Mapping values, iterating recursively.
        """
        yield from self._walk(None, self.root)
