#!/usr/bin/env python3

"""
Utility functions and classes to manipulate numpy/pandas data.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-11-03
"""
# Import standard libraries
from collections.abc import Hashable, Iterable, Mapping
from pprint import pprint
from typing import cast

# Import third-party PyPI libraries
import numpy as np
import pandas as pd

# Import local custom libraries
try:
    from gconanpy.meta import tuplify
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from meta import tuplify

# NOTE All functions/classes below are in alphabetical order.


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


def try_filter_df(df: pd.DataFrame, filters: Mapping[Hashable, Iterable[Hashable]]
                  ) -> pd.DataFrame:
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
