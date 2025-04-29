#!/usr/bin/env python3

"""
Lower-level utility functions and classes primarily to manipulate Sequences.
Overlaps significantly with:
    DCAN-Labs:audit-ABCC/src/utilities.py, \
    DCAN-Labs:abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-04-27
"""
# Import standard libraries
import builtins
from collections.abc import (Callable, Generator, Hashable,
                             Iterable, Mapping, Sequence)
import datetime as dt
import os
import pdb
from pprint import pprint
import re
import sys
from typing import Any, Literal, TypeVar

# Import third-party PyPI libraries
import numpy as np
import pandas as pd
import pathvalidate
import regex

# Constant: TypeVars for...
I = TypeVar("I")  # ...insert_into
S = TypeVar("S")  # ...differentiate_sets & get_key_set

# NOTE All functions/classes below are in alphabetical order.


def as_HTTPS_URL(*parts: str, **url_params: Any) -> str:
    """ Reusable convenience function to build HTTPS URL strings.

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


def differentiate_sets(sets: Iterable[set[S]]) -> list[set[S]]:
    """ Remove all shared/non-unique items from sets until they no longer \
    overlap/intersect at all.

    :param sets: Iterable[set[T]], _description_
    :return: list[set[T]], unique items in each set
    """
    to_return = [None] * len(sets)
    for i in range(len(sets)):
        for other_set in sets[:i] + sets[i+1:]:
            to_return[i] = sets[i] - other_set
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


def get_key_set(a_map: Mapping[S, Any]) -> set[S]:
    return set(a_map.keys())


def insert_into(a_seq: Sequence[I], item: I, at_ix: int) -> list[I]:
    # TODO items: Iterable[T] ?
    return [*a_seq[:at_ix], item, *a_seq[at_ix:]]


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


def nan_rows_in(a_df: pd.DataFrame) -> pd.DataFrame:
    """ 
    :param a_df: pd.DataFrame
    :return: pd.DataFrame only including rows of a_df which contain a NaN
             value in for at least 1 a_df column
    """
    return a_df[a_df.isna().any(axis=1)]


def parentheticals_in(txt: str) -> Generator[regex.Match[str], None, None]:
    """ Get all parentheticals, ignoring nested parentheticals.
    Adapted from https://stackoverflow.com/a/35271017

    :param txt: str, _description_
    :yield: Generator[regex.Match, None, None], _description_
    """
    for parenthetical in regex.finditer(r"\((?:[^)(]*(?R)?)*+\)", txt):
        yield parenthetical


def pprint_val_lens(a_map: Mapping) -> None:
    """ Pretty-print each key in a_map and the length of its mapped value.

    :param a_map: Mapping to pretty-print the lengths of values from
    """
    pprint({k: len(v) for k, v in a_map.items()})


def search_sequence_numpy(arr: np.array, subseq: np.array) -> list[int]:
    """ Find sequence in an array using NumPy only. "Approach #1" of the \
        code at https://stackoverflow.com/a/36535397 with an extra line to \
        mimic `str.find`.

    :param arr: np.array, a 1D array of which some slices equal `subseq`
    :param subseq: np.array, 1D sub-array of `arr` to find `arr`'s indices of
    :return: list[int], each element an index in `arr` where su`bseq begins
    """
    # Store sizes of input array and sequence
    arr_len = arr.size
    seq_len = subseq.size

    # Range of sequence
    r_seq = np.arange(seq_len)

    # Create a 2D array of sliding indices across the entire length of input array.
    # Match up with the input sequence & get the matching starting indices.
    arr_match = (arr[np.arange(arr_len - seq_len + 1)[:, None]
                 + r_seq] == subseq).all(1)

    # Get the range of those indices as final output
    if arr_match.any() > 0:
        all_seq_ixs = np.where(np.convolve(
            arr_match, np.ones((seq_len), dtype=int)) > 0)[0]
        start_indices = [all_seq_ixs[0], all_seq_ixs[-seq_len]]
        # start_indices = [all_seq_ixs[x] for x in range(0, all_seq_ixs.shape[0], seq_len)]
    else:
        start_indices = list()  # No match found
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
        file_name += put_dt_after + stringify(dt.datetime.now())

    if file_ext:  # If a file extension was provided, validate it
        ext = file_ext if file_ext[0] == "." else "." + file_ext

    return os.path.join(dir_path, file_name + ext)


class ToString(str):
    _TIMESPEC = Literal["auto", "hours", "minutes", "seconds", "milliseconds",
                        "microseconds"]  # for datetime.isoformat
    _S = TypeVar("_S")  # for truncate(...) function
    BLANKS: set[str | None] = {None, ""}  # Objects not to show in strings
    Quotator = Callable[[Any], "ToString"]
    NoneType = type(None)

    def __add__(self, value: str) -> "ToString":
        """ Append `value` to the end of `self`. Implements `self + value`. \
            Defined explicitly so that `ToString() + str() -> ToString` \
            instead of returning a `str` object.

        :param value: str
        :return: ToString, `self` with `value` appended after it.
        """
        return self.__class__(f"{self}{value}")

    def enclosed_by(self, affix: str) -> "ToString":
        """
        :param affix: str to prepend and append to this ToString instance
        :return: ToString with `affix` at the beginning and another at the end
        """
        return self.enclosed_in(affix, affix)

    def enclosed_in(self, prefix: str | None, suffix: str | None
                    ) -> "ToString":
        """
        :param prefix: str to prepend to this ToString instance
        :param suffix: str to append to this ToString instance
        :return: ToString with `prefix` at the beginning & `suffix` at the end
        """
        return self.that_starts_with(prefix).that_ends_with(suffix) \
            if len(self) else self.__class__(prefix + suffix)

    @classmethod
    def from_datetime(cls, moment: dt.date | dt.time | dt.datetime,
                      sep: str = "_", timespec: _TIMESPEC = "seconds",
                      replace: Mapping[str, str] = {":": "-"}) -> "ToString":
        """ Return the time formatted according to ISO as a ToString object.

        The full format is 'HH:MM:SS.mmmmmm+zz:zz'. By default, the fractional
        part is omitted if self.microsecond == 0.

        :param moment: dt.date | dt.time | dt.datetime to convert ToString.
        :param sep: str, the separator between date and time; defaults to "_"
        :param timespec: str specifying the number of additional terms of \
            the time to include; defaults to "seconds".
        :param replace: Mapping[str, str] of parts (in the result of calling \
            `moment.isoformat`) to different strings to replace them with; \
            by default, this will replace ":" with "-" (for naming files).
        :return: ToString, _description_
        """
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
                      sep: str = ", ", quote_numbers: bool = False,
                      prefix: str | None = "[", suffix: str | None = "]",
                      max_len: int | None = None, lastly: str = "and "
                      ) -> "ToString":
        """ Convert an Iterable into a ToString object.

        :param an_obj: Iterable to convert ToString
        :param quote: str to add before and after each element of `an_obj`, \
            or None to insert no quotes; defaults to "'"
        :param sep: str to insert between all of the elements of `an_obj`, \
            or None to insert no such separators; defaults to ", "
        :param quote_numbers: bool, True to insert `quote` before and after \
            each numerical element of `an_obj`; else False to add no \
            quotes to numbers in `an_obj`; defaults to False
        :param prefix: str to insert as the first character of the returned \
            ToString object, or None to add no prefix; defaults to "["
        :param suffix: str to insert as the last character of the returned \
            ToString object, or None to add no suffix; defaults to "]"
        :param max_len: int, size of the longest possible ToString to return \
            without truncation, or None to never truncate; defaults to None
        :param lastly: str to insert after the last `sep` in the returned \
            ToString object `if len(an_obj) > 2`, or None to add no such \
            string; defaults to "and "
        :return: ToString of all elements in `an_obj`, `quote`-quoted and \
                 `sep`-separated if there are multiple elements, starting \
                 with `prefix` and ending with `suffix`, with `lastly` after \
                 the last `sep` if there are more than 2 elements of `an_obj`.
        """
        if isinstance(an_obj, str):  # TODO Refactor from LBYL to EAFP?
            string = an_obj
        else:
            list_with_str_els = cls.quotate_all(an_obj, quote,
                                                quote_numbers, max_len)
            if len(an_obj) > 2:
                except_end = (sep + ' ').join(list_with_str_els[:-1])
                string = f"{except_end}{sep} {lastly}{list_with_str_els[-1]}"
            else:
                string = f" {lastly}".join(list_with_str_els)
        self = cls(string)
        if max_len is not None:
            affix_len = sum([len(x) if x else 0 for x in (prefix, suffix)])
            self = self.truncate(max_len - affix_len)
        return self.enclosed_in(prefix, suffix)

    @classmethod
    def from_object(cls, an_obj: Any, max_len: int | None = None,
                    quote: str | None = "'", quote_numbers: bool = False,
                    join_on: str = ": ", sep: str = ",",
                    prefix: str | None = None, suffix: str | None = None,
                    dt_sep: str = "_", timespec: _TIMESPEC = "seconds",
                    replace: Mapping[str, str] = {":": "-"},
                    encoding: str = sys.getdefaultencoding(),
                    errors: str = "ignore", lastly: str = "and "
                    ) -> "ToString":
        """ Convert an object ToString 

        :param an_obj: Any, object to convert ToString
        :param max_len: int, size of the longest possible ToString to return \
            without truncation, or None to never truncate; defaults to None
        :param quote: str to add before and after each element of `an_obj`, \
            or None to insert no quotes; defaults to "'"
        :param quote_numbers: bool, True to insert `quote` before and after \
            each numerical element of `an_obj`; else False to add no \
            quotes to numbers in `an_obj`; defaults to False
        :param join_on: str to insert between the key and value of each \
            key-value pair in `an_obj` if it's a Mapping; defaults to ": "
        :param sep: str to insert between all of the elements of `an_obj`, \
            or None to insert no such separators; defaults to ", "
        :param prefix: str to insert as the first character of the returned \
            ToString object, or None to add no prefix; defaults to None
        :param suffix: str to insert as the last character of the returned \
            ToString object, or None to add no suffix; defaults to None
        :param dt_sep: str, separator between date and time; defaults to "_"
        :param timespec: str specifying the number of additional terms of \
            the time to include; defaults to "seconds".
        :param replace: Mapping[str, str] of parts (in the result of calling \
            `datetime.*.isoformat` on a `datetime`-typed `an_obj`) to \
            different strings to replace them with; by default, will replace ":" \
            with "-" to name files.
        :param encoding: str,_description_, defaults to sys.getdefaultencoding()
        :param errors: str,_description_, defaults to "ignore"
        :param lastly: str to insert after the last `sep` in the returned \
            ToString object `if len(an_obj) > 2`, or None to add no such \
            string; defaults to "and "
        :return: ToString of `an_obj` formatted as specified.
        """
        # TODO Class pattern match? stackoverflow.com/questions/72295812
        match type(an_obj):
            case builtins.bytes | builtins.bytearray:
                stringified = cls(an_obj, encoding=encoding, errors=errors)
            case builtins.dict:  # TODO case Mapping equivalent after builtins
                stringified = cls.from_mapping(an_obj, quote, quote_numbers,
                                               join_on, prefix, suffix, sep,
                                               max_len, lastly)
            case builtins.list | builtins.tuple | builtins.set:  # metafunc.PureIterable:
                stringified = cls.from_iterable(an_obj, quote, sep,
                                                quote_numbers, prefix, suffix,
                                                max_len, lastly)
            case dt.date | dt.time | dt.datetime:
                stringified = cls.from_datetime(an_obj, dt_sep,
                                                timespec, replace)
            case cls.NoneType:
                stringified = cls()
            case _:  # str or other
                stringified = cls(an_obj)
        return stringified

    @classmethod
    def from_mapping(cls, a_map: Mapping, quote: str | None = "'",
                     quote_numbers: bool = False, join_on: str = ": ",
                     prefix: str | None = "{", suffix: str | None = "}",
                     sep: str = ",", max_len: int | None = None,
                     lastly: str = "and ") -> "ToString":
        """
        :param a_map: Mapping to convert ToString
        :param quote: str to add before and after each key-value pair in \
            `a_map`, or None to insert no quotes; defaults to "'"
        :param quote_numbers: bool, True to insert `quote` before and after \
            each numerical key or value in `a_map`; else False to add no \
            quotes to numbers in `a_map`; defaults to False
        :param join_on: str to insert between the key and value of each \
            key-value pair in `a_map`; defaults to ": "
        :param prefix: str to insert as the first character of the returned \
            ToString object, or None to add no prefix; defaults to "{"
        :param suffix: str to insert as the last character of the returned \
            ToString object, or None to add no suffix; defaults to "}"
        :param sep: str to insert between all of the key-value pairs in \
            `a_map`, or None to insert no such separators; defaults to ", "
        :param max_len: int, size of the longest possible ToString to return \
            without truncation, or None to never truncate; defaults to None
        :param lastly: str to insert after the last `sep` in the returned \
            ToString object `if len(a_map) > 2`, or None to add no such \
            string; defaults to "and "
        :return: ToString, _description_
        """
        join_on = cls(join_on)
        quotate = cls.get_quotator(quote, quote_numbers)
        pair_strings = list()
        for k, v in a_map.items():
            v = quotate(v) if max_len is None else \
                quotate(v).truncate(max_len, quotate)
            pair_strings.append(join_on.join(quotate(k), v))
        return cls.from_iterable(pair_strings, None, sep, prefix=prefix,
                                 suffix=suffix, max_len=max_len,
                                 lastly=lastly)

    @classmethod
    def get_quotator(cls, quote: str | None = "'", quote_numbers:
                     bool = False) -> Quotator:
        quotate = cls.quotate_obj if quote_numbers else cls.quotate_number
        return cls.from_object if not quote else lambda x: quotate(x, quote)

    def join(self, *strings: str) -> "ToString":
        """ Concatenate any number of strings. Same as `str.join`, but \
            returns a `ToString` object.

        :return: ToString, all `strings` concatenated together with this \
            ToString (`self`) inserted in between them all.
        """
        return self.__class__(str.join(self, strings))

    @classmethod
    def quotate_all(cls, objects: Iterable, quote: str | None = "'",
                    quote_numbers: bool = False, max_len: int | None = None
                    ) -> list["ToString"]:
        finish = cls.get_quotator(quote, quote_numbers)
        return [finish(obj) if max_len is None else
                finish(obj).truncate(max_len) for obj in objects]

    @classmethod
    def quotate_number(cls, a_num: Any, quote: str = "'") -> "ToString":
        stringified = cls.from_object(a_num)
        return stringified if stringified.isnumeric() \
            else stringified.enclosed_by(quote)

    @classmethod
    def quotate_obj(cls, an_obj: Any, quote: str = "'") -> "ToString":
        """
        :param an_obj: Any, object to convert ToString.
        :param quote: str to add before and after `an_obj`; defaults to "'"
        :return: ToString, `quote + stringify(an_obj) + quote`
        """
        return cls.from_object(an_obj).enclosed_by(quote)

    def that_ends_with(self, suffix: str | None) -> "ToString":
        """ Append `suffix` to the end of `self` unless it is already there.

        :param suffix: str to append to `self`, or None to do nothing.
        :return: ToString ending with `suffix`.
        """
        return self if suffix in self.BLANKS or self.endswith(suffix) \
            else self.__class__(self + suffix)

    def that_starts_with(self, prefix: str | None) -> "ToString":
        """ Prepend `suffix` at index 0 of `self` unless it is already there.

        :param prefix: str to prepend to `self`, or None to do nothing.
        :return: ToString beginning with `prefix`.
        """
        return self if prefix in self.BLANKS or self.startswith(prefix) \
            else self.__class__(prefix + self)

    def truncate(self, max_len: int | None = None,
                 quotate: Quotator | None = None,
                 suffix: str = "...") -> "ToString":
        if max_len is None:
            truncated = self
        else:
            quotated = quotate(self) if quotate else self
            if len(quotated) <= max_len:
                truncated = quotated
            else:
                quote_len = len(quotated) - len(self)
                raw_max_len = max_len - quote_len - len(suffix)
                raw_truncated = truncate(self, max_len=raw_max_len) + suffix
                truncated = self.__class__(quotate(raw_truncated) if quotate
                                           else raw_truncated)
        return truncated


# Shorter name to export
stringify = ToString.from_object


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
