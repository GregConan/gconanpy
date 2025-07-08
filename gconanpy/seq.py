#!/usr/bin/env python3

"""
Lower-level utility functions and classes primarily to manipulate Sequences.
Overlaps with:
    DCAN-Labs:audit-ABCC/src/utilities.py, \
    DCAN-Labs:abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-07-07
"""
# Import standard libraries
from collections.abc import Hashable, Iterable, Mapping, Sequence
from functools import reduce
from pprint import pprint
from typing import Any, get_args, TypeVar
from unittest.mock import MagicMock

# Import third-party PyPI libraries
import numpy as np
import pandas as pd

# Import local custom libraries
try:
    from meta.classes import MutableItemStore, Updatable
    from meta.funcs import tuplify
    from ToString import stringify
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.meta.classes import MutableItemStore, Updatable
    from gconanpy.meta.funcs import tuplify
    from gconanpy.ToString import stringify

# Constant: TypeVars for...
S = TypeVar("S")  # ...differentiate_sets & get_key_set
U = TypeVar("U", bound=Updatable)  # ...merge

# NOTE All functions/classes below are in alphabetical order.


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


def get_key_set(a_map: Mapping[S, Any]) -> set[S]:
    return set(a_map.keys())


class Recursively:
    _KT = Hashable | tuple[Hashable, ...]

    @staticmethod
    def getitem(an_obj: MutableItemStore, key: _KT) -> Any:
        for k in tuplify(key):
            an_obj = an_obj[k]
        return an_obj

    @classmethod
    def getattribute(cls, an_obj: Any, *attr_names: str) -> Any:
        if attr_names:
            return getattr(an_obj, attr_names[0],
                           cls.getattribute(an_obj, *attr_names[1:]))

    @classmethod
    def setitem(cls, an_obj: MutableItemStore, key: _KT, value: Any) -> None:
        keys = tuplify(key)
        if len(keys) == 1:
            an_obj[keys[0]] = value
        else:
            cls.setitem(an_obj[keys[0]], keys[1:], value)


def link_to_markdown(a_string: str, a_URL: str) -> str:
    a_string = a_string.replace("[", r"\[").replace("]", r"\]")
    a_URL = a_URL.replace("(", r"\(").replace(")", r"\)")
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
    md_link_parts = md_link_text[1:-1].split("](")
    return md_link_parts[0], md_link_parts[1]


def merge(updatables: Iterable[U]) -> U:
    """ Merge dicts, sets, or things of any type with an `update` method.

    :param updatables: Iterable[Updatable], objects to combine
    :return: Updatable combining all of the `updatables` into one
    """
    return reduce(lambda x, y: x.update(y) or x, updatables)


def merge_lists(lists: Iterable[list]) -> list:
    """
    :param lists: Iterable[list], objects to combine
    :return: list combining all of the `lists` into one
    """
    return reduce(lambda x, y: x.extend(y) or x, lists)


def nan_rows_in(a_df: pd.DataFrame) -> pd.DataFrame:
    """
    :param a_df: pd.DataFrame
    :return: pd.DataFrame only including rows of a_df which contain a NaN
             value in for at least 1 a_df column
    """
    return a_df[a_df.isna().any(axis=1)]


def powers_of_ten(orders_of_magnitude: int = 4) -> list[int]:
    return [10 ** i for i in range(orders_of_magnitude + 1)]


def pprint_val_lens(a_map: Mapping) -> None:
    """ Pretty-print each key in a_map and the length of its mapped value.

    :param a_map: Mapping to pretty-print the lengths of values from
    """
    pprint({k: len(v) for k, v in a_map.items()})


def search_sequence_numpy(arr: np.ndarray, subseq: np.ndarray) -> list[int]:
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


def truncate(a_seq: Sequence, max_len: int) -> Sequence:
    return a_seq[:max_len] if len(a_seq) > max_len else a_seq


def rtruncate(a_seq: Sequence, max_len: int) -> Sequence:
    return a_seq[-max_len:] if len(a_seq) > max_len else a_seq


def uniqs_in(listlike: Iterable[Hashable]) -> list[Hashable]:
    """Alphabetize and list the unique elements of an iterable.
    To list non-private local variables' names, call uniqs_in(locals()).

    :param listlike: Iterable[Hashable] to get the unique elements of
    :return: List[Hashable] (sorted) of all unique strings in listlike \
             that don't start with an underscore
    """
    uniqs = [*set([v for v in listlike if not startswith(v, "_")])]
    uniqs.sort()  # type: ignore
    return uniqs
