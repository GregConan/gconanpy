#!/usr/bin/env python3

"""
Utility functions and classes to manipulate data using numpy, scipy, & pandas.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-12-04
"""
# Import standard libraries
from collections.abc import Hashable, Iterable, Mapping
from pprint import pprint
import string
from typing import Any, cast, Literal, TypeVar

# Import third-party PyPI libraries
import numpy as np
import pandas as pd

# Import local custom libraries
try:
    from gconanpy.iters import merge
    from gconanpy.meta import tuplify
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from iters import merge
    from meta import tuplify


# Constants, especially for word frequency counting:

# Pandas DataFrame axis
AXIS = Literal[0, 1, "columns", "index", "rows"]

# Characters to strip when parsing words to count word frequencies
IGNORABLES: str = string.punctuation + string.whitespace

# Possible word capitalization cases
WORD_CASE = Literal["title", "upper", "lower", None]

# NOTE All functions/classes below are in alphabetical order.


def compare_word_frequencies(df: pd.DataFrame, words_col: str, group_by: str,
                             min_thresh: int | None = None,
                             strip_chars: str = IGNORABLES,
                             case: WORD_CASE = "lower") -> pd.DataFrame:
    """ Compare word frequencies in one column of a `DataFrame`, grouped by the
        values in another column.

    :param df: pd.DataFrame with columns including `words_col` and `group_by`.
    :param words_col: str naming a `df` column containing text data.
    :param group_by: str naming a `df` column with few unique values. 
    :param min_thresh: int | None, number of occurrences of a word below which
        to exclude that word from the final frequency count; minimum word count
        threshold; or None to exclude no words; defaults to None.
    :param strip_chars: str, all characters to remove from the beginning and 
        ending of each word; defaults to all punctuation and whitespace.
    :param case: Literal["title", "upper", "lower", None], case to return words
        as, or None to treat the same word in different cases as different 
        words; defaults to "lower" (lowercase).
    :return: pd.DataFrame with one column per unique value in the `group_by`
        column of `df` and one row per unique word in every row of the 
        `words_col` column of `df`; each cell contains the frequency of each
        word in the `words_col` column of `df` for the rows with each given
        `group_by` value.
    """
    words = df.groupby(group_by)[words_col].apply(
        count_words_in, case=case, strip_chars=strip_chars).reset_index()
    counts = TransformDF(words, "level_1", group_by, words_col
                         ).transform().fillna(0)
    if min_thresh is not None:
        counts.dropna(inplace=True)
        counts = cast(pd.DataFrame, counts[counts > min_thresh].dropna())
    return to_frequencies(counts, axis=0)


def count_words_in(ser: pd.Series, strip_chars: str = IGNORABLES,
                   case: WORD_CASE = "lower") -> pd.Series:
    """ Count the number of occurrences of each unique word in a `pd.Series`.
        Adapted from https://stackoverflow.com/a/46786277

    :param ser: pd.Series containing only strings and NaNs.
    :param strip_chars: str, all characters to remove from the beginning and 
        ending of each word; defaults to all punctuation and whitespace.
    :param case: Literal["title", "upper", "lower", None], case to return words
        as, or None to treat the same word in different cases as different 
        words; defaults to "lower" (lowercase).
    :return: pd.Series mapping each word in `ser` to the number of times that
        it appears in `ser`.
    """
    words = pd.Series(" ".join(ser.fillna("").str.strip(strip_chars)).split())
    if case is not None:
        words = cast(pd.Series, getattr(words.str, case)())
    return words.value_counts()


def count_uniqs_in_cols(a_df: pd.DataFrame) -> dict[str, int]:
    cols_uniqs = {colname: a_df[colname].value_counts().shape[0]
                  for colname in a_df.columns}
    # pprint_val_lens(cols_uniqs)
    pprint(cols_uniqs)
    return cols_uniqs


def nan_rows_in(a_df: pd.DataFrame) -> pd.DataFrame:
    """
    :param a_df: pd.DataFrame
    :return: pd.DataFrame only including rows of a_df which contain a NaN
             value in for at least 1 a_df column
    """
    return a_df[a_df.isna().any(axis=1)]  # type: ignore


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
        start_indices = []  # No match found
    return start_indices


class TransformDF:
    _T = TypeVar("_T")

    def __init__(self, df: pd.DataFrame, new_index: str, new_cols: str,
                 new_values: str) -> None:
        """ Call `TransformDF(...).transform()` to restructure a `DataFrame`
            using its values.

        :param df: pd.DataFrame whose column names include the provided
            `new_index`, `new_cols`, and `new_values` strings.
        :param new_index: str naming the `df` column containing values which
            will become the output `DataFrame`'s index.
        :param new_cols: str naming the `df` column containing values which 
            will become the output `DataFrame`'s columns.
        :param new_values: str naming the `df` column containing values which 
            will become the output `DataFrame`'s values.
        """
        self.df = df
        self.new_ix = new_index
        self.new_cols = new_cols
        self.new_vals = new_values

    def transform(self) -> pd.DataFrame:
        """ 
        :return: pd.DataFrame, transformed/restructured 
        """
        uniqs = pd.Series(self.df[self.new_ix].unique())
        return pd.DataFrame(merge(uniqs.apply(self._regrouper).tolist())).T

    def _regrouper(self, value: _T) -> dict[_T, dict[Any, Any]]:
        """ Utility method to apply to each value in the new index column of 
            the input `DataFrame`, mapping each new column to its value.

        :param value: _type_, _description_
        :return: dict[Any, Any], _description_
        """
        return {value: dict[Any, Any](self.df[self.df[self.new_ix] == value][[
            self.new_cols, self.new_vals]
        ].values)}  # pyright: ignore[reportAttributeAccessIssue]


def to_frequencies(df: pd.DataFrame, axis: AXIS = "index") -> pd.DataFrame:
    """ Convert a counts table containing only integers into a frequency table 
        containing each column's (or row's) frequencies per that column(/row).

    :param df: pd.DataFrame containing only integers.
    :param axis: Literal[0, 1, "columns", "index", "rows"], which axis of `df`
        to divide every column's (or row's) value by the sum of; defaults to
        "index" to divide every column by its sum, specify `axis="columns"` or
        `axis=1` to instead divide every row by its sum.
    :return: pd.DataFrame, each column's (or row's) frequency percentages.
    """
    return cast(pd.DataFrame, df.apply(lambda ser: ser / ser.sum(), axis=axis))


def try_filter_df(df: pd.DataFrame, filters:
                  Mapping[Hashable, Iterable[Hashable]]) -> pd.DataFrame:
    """
    :param df: pd.DataFrame to filter
    :param col_name: Hashable, name of the column to filter by
    :param acceptable_values: Iterable[Any], values that must appear in \
        the `col_name` column of every row of the returned `DataFrame`, \
        if any such rows exist in this `DataFrame`.
    :return: DataFrame, filtered to only include row(s) with a `col_name` \
        value in `acceptable_values`, if any; else `df` unchanged.
    """
    new_df = prev_df = df
    for col_name, acceptable_values in filters.items():
        # not `match len(new_df.index)` because that'd need a double `break`?
        n_rows = len(new_df.index)
        if n_rows == 1:
            return new_df
        elif n_rows == 0:
            '''
            raise ValueError("Value not found in DataFrame")
            if len(prev_df.index) == 0:
                pdb.set_trace()
                pass
            '''
            new_df = prev_df
        else:
            prev_df = new_df
            new_df = cast(pd.DataFrame, new_df.loc[new_df[col_name].isin(
                tuplify(acceptable_values))
            ])
    if len(new_df.index) > 1:
        for col_name, acceptable_values in filters.items():
            for val in acceptable_values:
                new_df = cast(pd.DataFrame, new_df.loc[
                    new_df[col_name].str.contains(val)])
                if len(new_df.index) == 1:
                    return new_df

    return new_df if len(new_df.index) > 0 else df
