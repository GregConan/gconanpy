#!/usr/bin/env python3

"""
Lower-level utility functions and classes primarily to manipulate Sequences.
Overlaps significantly with:
    audit-ABCC/src/utilities.py, \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-03-27
"""
# Import standard libraries
import builtins
import datetime as dt
import itertools
import os
import pdb
from pprint import pprint
import re
import sys
from typing import (Any, Callable, Generator, Hashable, Iterable,
                    Mapping, Sequence, TypeVar)

# Import third-party PyPI libraries
import numpy as np
import pandas as pd
import pathvalidate
import regex

# Constant: TypeVar for chain(...) function
T = TypeVar("T")

# NOTE All functions/classes below are in alphabetical order.


def are_all_equal(comparables: Iterable) -> bool:
    """ `are_all_equal([x, y, z])` means `x == y == z`.

    :param comparables: Iterable of objects to check for equality.
    :return: bool, True if every item in comparables is equal to every
                other item, otherwise False.
    """
    are_equal = True
    looping = True
    combos_iter = itertools.combinations(comparables, 2)
    while looping and are_equal:
        next_pair = next(combos_iter, None)
        if not next_pair:  # is None:
            looping = False
        elif next_pair[0] != next_pair[1]:
            are_equal = False
    return are_equal


def as_HTTPS_URL(*parts: str, **url_params: Any) -> str:
    """Reusable convenience function to build HTTPS URL strings.

    :param parts: Iterable[str] of slash-separated URL path parts
    :param url_params: Mapping[str, Any] of variable names and their values \
                       to pass to the API endpoint as parameters
    :return: str, full HTTPS URL path
    """
    url = f"https://{'/'.join(parts)}"
    if url_params:
        str_params = [f"{k}={v}" for k, v in url_params.items()]
        url += "?" + "&".join(str_params)
    return url


def chain(iterables: Iterable[Iterable[T]]) -> Iterable[T]:
    return [x for x in itertools.chain(*iterables)]


def count_uniqs_in_cols(a_df: pd.DataFrame) -> dict[str, int]:
    cols_uniqs = {colname: a_df[colname].value_counts().shape[0]
                  for colname in a_df.columns}
    # pprint_val_lens(cols_uniqs)
    pprint(cols_uniqs)
    return cols_uniqs


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


def extract_letters_from(a_str: str) -> str:
    return re.sub(r'[^a-zA-Z]', '', a_str)


def extract_parentheticals_from(txt: str) -> list[Any]:
    """ Get all parentheticals, ignoring nested parentheticals.
    Adapted from https://stackoverflow.com/a/35271017

    :param txt: str, _description_
    :return: List[Any], _description_
    """
    return regex.findall(r"\((?:[^()]+|(?R))*+\)", txt)


def find_an_attr_in(attrs_of: Any, attr_names: Iterable[str], default:
                    Any = None, method_names: set[str] = set()) -> Any:
    found_attr = default
    ix = 0
    while ix + 1 < len(attr_names) and not hasattr(attrs_of,
                                                   attr_names[ix]):
        ix += 1
    try:
        name = attr_names[ix]
        found_attr = getattr(attrs_of, name, default)
        if name in method_names:
            found_attr = found_attr()
    except (AttributeError, IndexError, TypeError):
        pass
    return found_attr


# Mostly to use as default value of input parameters in class methods
def is_not_none(x: Any) -> bool: return x is not None


def link_to_markdown(a_string: str, a_URL: str) -> str:
    a_string = a_string.replace('[', '\[').replace(']', '\]')
    return f"[{a_string}]({a_URL})"


def list_to_dict(a_list: list[str], delimiter: str = ": ") -> dict[str, str]:
    a_dict = dict()
    for eachstr in a_list:
        k, v = eachstr.split(delimiter)
        a_dict[k] = v
    return a_dict


def markdown_to_link(md_link_text: str) -> tuple[str, str]:
    md_link_text = md_link_text.strip()
    assert md_link_text[0] == "[" and md_link_text[-1] == ")"
    return md_link_text[1:-1].split("](")


def nameof(an_obj: Any) -> str:
    """ Get the `__name__` of an object or of its type/class.

    :param an_obj: Any
    :return: str naming an_obj, usually its type/class name.
    """
    return getattr(an_obj, "__name__", type(an_obj).__name__)


def nan_rows_in(a_df: pd.DataFrame) -> pd.DataFrame:
    """ 
    :param a_df: pd.DataFrame
    :return: pd.DataFrame only including rows of a_df which contain a NaN
             value in for at least 1 a_df column
    """
    return a_df[a_df.isna().any(axis=1)]


def noop(*_args: Any, **_kwargs: Any) -> None:  # TODO Move somewhere more apt
    """Do nothing. Convenient to use as a default callable function parameter.

    :return: None
    """
    pass  # or `...`


def parentheticals_in(txt: str) -> Generator[regex.Match[str], None, None]:
    """ Get all parentheticals, ignoring nested parentheticals.
    Adapted from https://stackoverflow.com/a/35271017

    :param txt: str, _description_
    :yield: Generator[regex.Match, None, None], _description_
    """
    paren_iter = regex.finditer(r"\((?:[^)(]*(?R)?)*+\)", txt)
    for parenthetical in paren_iter:
        yield parenthetical


def pprint_val_lens(a_map: Mapping) -> None:
    """ Pretty-print each key in a_map and the length of its mapped value.

    :param a_map: Mapping to pretty-print the lengths of values from
    """
    pprint({k: len(v) for k, v in a_map.items()})


def search_sequence_numpy(arr: np.array, subseq: np.array) -> list[int]:
    """
    Find sequence in an array using NumPy only. "Approach #1" of the code at
    https://stackoverflow.com/a/36535397 with an extra line to mimic str.find.
    :param arr: np.array, a 1D array of which some slices are equal to subseq
    :param subseq: np.array, the 1D sub-array of arr to find arr's indices of
    :return: List of integers, each an index in arr where subseq begins
    """
    # Store sizes of input array and sequence
    arr_len = arr.size
    seq_len = subseq.size

    # Range of sequence
    r_seq = np.arange(seq_len)

    # Create a 2D array of sliding indices across the entire length of input array.
    # Match up with the input sequence & get the matching starting indices.
    M = (arr[np.arange(arr_len - seq_len + 1)[:, None]
             + r_seq] == subseq).all(1)

    # Get the range of those indices as final output
    if M.any() > 0:
        all_seq_ixs = np.where(np.convolve(M, np.ones((seq_len),
                                                      dtype=int)) > 0)[0]
        start_indices = [all_seq_ixs[0], all_seq_ixs[-seq_len]]
        # start_indices = [all_seq_ixs[x] for x in range(0, all_seq_ixs.shape[0], seq_len)]
    else:
        start_indices = list()        # No match found
    return start_indices


def seq_startswith(seq: Sequence, prefix: Sequence) -> bool:
    """ Check if prefix is the beginning of seq.

    :param seq: Sequence, _description_
    :param prefix: Sequence, _description_
    :return: bool, True if seq starts with the specified prefix, else False.
    """
    return len(seq) >= len(prefix) and seq[:len(prefix)] == prefix


def startswith(an_obj: Any, prefix: Any) -> bool:
    """ Check if the beginning of an_obj is prefix.
    Type-agnostic extension of str.startswith and bytes.startswith.

    :param an_obj: Any, _description_
    :param prefix: Any, _description_
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


def to_file_path(dir_path: str, file_name: str, file_ext: str = "",
                 put_dt_after: str | None = None,
                 max_len: int | None = 50) -> str:
    """ Save entire HTML source document into local text file for testing

    :param dir_path: str, valid path to directory containing the file
    :param file_name: str, name of the file excluding path and extension
    :param file_ext: str, the file's extension; defaults to empty string
    :param put_dt_after: str | None, include this to automatically generate\
                         the current date and time in ISO format and insert\
                         it into the filename after the specified delimiter.\
                         Exclude this argument to exclude date/time from path.
    :param max_len: int, maximum filename byte length. Truncate the name if\
                    the filename length exceeds this value. None means 255.
    :return: str, the new full file path
    """
    # Remove special characters not covered by pathvalidate.sanitize_filename
    file_name = re.sub(r"[?:\=\.\&\?]*", '', file_name)

    # Remove any characters illegal in file paths/names
    file_name = pathvalidate.sanitize_filename(file_name, max_len=max_len)

    if put_dt_after:
        file_name += put_dt_after + stringify_dt(dt.datetime.now())

    if file_ext:  # If a file extension was provided, validate it
        ext = file_ext if file_ext[0] == "." else "." + file_ext

    return os.path.join(dir_path, file_name + ext)


class ToString(str):
    _S = TypeVar("_S")  # for truncate(...) function
    Quotator = Callable[[Any], "ToString"]
    NoneType = type(None)

    def enclosed_by(self, affix: str):
        return self.that_ends_with(affix).that_starts_with(affix) \
            if len(self) else self.__class__(affix + affix)

    @classmethod
    def from_datetime(cls, moment: dt.date | dt.time | dt.datetime,
                      sep: str = "_", timespec: str = "seconds",
                      replace: Mapping[str, str] = {":": "-"}):
        match type(moment):
            case dt.date:
                stringified = dt.date.isoformat(moment)
            case dt.time:
                stringified = dt.time.isoformat(moment, timespec=timespec)
            case dt.datetime:
                stringified = dt.datetime.isoformat(moment, sep=sep,
                                                    timespec=timespec)
        for to_replace, replace_with in replace.items():
            stringified = stringified.replace(to_replace, replace_with)
        return cls(stringified)

    @classmethod
    def from_iterable(cls, an_obj: Iterable, quote: str | None = "'",
                      sep: str = ",", quote_numbers: bool = False,
                      enclose_in: tuple[str, str] | None = ("[", "]"),
                      max_len: int | None = None):
        """

        :param a_list: list[Any]
        :param quote: str | None,_description_, defaults to "'"
        :param sep: str,_description_, defaults to ","
        :return: ToString of all items in a_list, {quote}-quoted and \
                 {sep}-separated if there are multiple 
        """
        result = an_obj
        if isinstance(an_obj, str):
            if quote:
                result = cls(an_obj).enclosed_by(quote)
        elif isinstance(an_obj, Iterable):  # TODO Refactor from LBYL to EAFP?
            list_with_str_els = cls.quotate(*an_obj, quote, quote_numbers,
                                            max_len)
            if len(an_obj) > 2:
                except_end = (sep + ' ').join(list_with_str_els[:-1])
                result = f"{except_end}{sep} and {list_with_str_els[-1]}"
            else:
                result = " and ".join(list_with_str_els)
            if enclose_in:
                result = f"{enclose_in[0]}{result}{enclose_in[1]}"
        return cls(result)

    @classmethod
    # TODO Make this __init__(self, an_obj) ?
    def from_object(cls, an_obj: Any, max_len: int | None = None):
        """ _summary_

        :param an_obj: None | str | SupportsBytes | dt.datetime | list, _description_
        :param sep: str,_description_, defaults to "_"
        :param timespec: str,_description_, defaults to "seconds"
        :param encoding: str,_description_, defaults to sys.getdefaultencoding()
        :param errors: str,_description_, defaults to "ignore"
        :return: str, _description_
        """  # TODO Class pattern match? stackoverflow.com/questions/72295812
        match type(an_obj):
            case builtins.bytes | builtins.bytearray:
                stringified = cls(an_obj, encoding=sys.getdefaultencoding(),
                                  errors="ignore")
            case builtins.dict:  # TODO case Mapping equivalent after builtins
                stringified = cls.from_mapping(an_obj, max_len=max_len)
            case builtins.list | builtins.set | builtins.tuple:
                stringified = cls.from_iterable(an_obj, max_len=max_len)
            case dt.date | dt.time | dt.datetime:
                stringified = cls.from_datetime(an_obj)
            case cls.NoneType:
                stringified = cls()
            case _:  # str or other
                stringified = cls(an_obj)
        return stringified

    @classmethod
    def from_mapping(cls, a_map: Mapping, quote: str | None = "'",
                     quote_numbers: bool = False, join_on: str = ":",
                     enclose_in: tuple[str, str] | None = ("{", "}"),
                     sep: str = ",", max_len: int | None = None):
        join_on = cls(join_on)
        quotate = cls.get_quotator(quote, quote_numbers)
        mappings = list()
        for k, v in a_map.items():
            v = quotate(v) if max_len is None else \
                cls.from_object(v).truncate(max_len, quotate)
            mappings.append(join_on.join(quotate(k), v))
        return cls.from_iterable(mappings, None, sep, enclose_in=enclose_in)

    @classmethod
    def get_quotator(cls, quote: str | None = "'", quote_numbers:
                     bool = False) -> Quotator:
        quotate = cls.quotate_number if quote_numbers else cls.quotate_obj
        return cls.from_object if not quote else lambda x: quotate(x, quote)

    def join(self, *strings: str):
        return self.__class__(str.join(self, strings))

    @classmethod
    def quotate(cls, *objects: Any, quote: str | None = "'",
                quote_numbers: bool = False, max_len: int | None = None
                ) -> list["ToString"]:
        finish = cls.get_quotator(quote, quote_numbers)
        return [finish(obj) if max_len is None else
                finish(obj).truncate(max_len) for obj in objects]

    @classmethod
    def quotate_number(cls, a_num, quote: str = "'"):
        stringified = cls.from_object(a_num)
        return stringified if stringified.isdigit() else \
            stringified.enclosed_by(quote)

    @classmethod
    def quotate_obj(cls, an_obj: Any, quote: str = "'"):
        return cls.from_object(an_obj).enclosed_by(quote)

    def that_ends_with(self, suffix: str):
        return self if self.endswith(suffix) \
            else self.__class__(self + suffix)

    def that_starts_with(self, prefix: str):
        return self if self.startswith(prefix) \
            else self.__class__(prefix + self)

    def truncate(self, max_len: int, quotate: Quotator | None = None,
                 end_with: str = "..."):
        truncated = self.__class__(self[:max_len] + end_with) \
            if len(self) > max_len else self
        return quotate(truncated) if quotate else truncated


# Shorter names to export
stringify = ToString.from_object
stringify_dt = ToString.from_datetime
stringify_map = ToString.from_mapping
stringify_list = ToString.from_iterable


def truncate(a_seq: Sequence, max_len: int) -> Sequence:
    return a_seq[:max_len] if len(a_seq) > max_len else a_seq


def uniqs_in(listlike: Iterable[Hashable]) -> list[Hashable]:
    """Alphabetize and list the unique elements of an iterable.
    To list non-private local variables' names, call uniqs_in(locals()).

    :param listlike: Iterable[Hashable] to get the unique elements of
    :return: List[Hashable] (sorted) of all unique strings in listlike \
             that don't start with an underscore
    """
    uniqs = [*set([v for v in listlike if not startswith(v, "_")])]
    uniqs.sort()
    return uniqs
