
#!/usr/bin/env python3

"""
Lower-level utility classes/functions primarily to manipulate Sequences.
Overlaps significantly with:
    audit-ABCC/src/utilities.py, \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-24
Updated: 2025-03-18
"""
# Import standard libraries
import datetime as dt
import os
import pdb
from pprint import pprint
import re
import sys
from typing import (Any, Generator, Hashable, Iterable,
                    Mapping, Sequence, SupportsBytes)

# Import third-party PyPI libraries
import numpy as np
import pandas as pd
import pathvalidate
import regex


# NOTE All classes and functions below are in alphabetical order.


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


def noop(*_args: Any, **_kwargs: Any) -> None:  # TODO Move somewhere more apt
    """Do nothing. Convenient to use as a default callable function parameter.

    :return: None
    """
    pass  # or `...`


def parentheticals_in(txt: str) -> Generator[regex.Match, None, None]:
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


def setdefaults_of(a_dict: dict, keep_Nones: bool = True, **kwargs: Any
                   ) -> dict:
    """
    dict.update prefers to overwrite old values with new ones.
    setdefaults_of is basically dict.update that prefers to keep old values.

    :param a_dict: dict
    :param keep_Nones: bool, _description_, defaults to True
    :param kwargs: dict[str, Any] of values to add to a_dict if needed
    :return: dict, a_dict that filled any missing values from kwargs 
    """
    if keep_Nones:
        for key, value in kwargs.items():
            a_dict.setdefault(key, value)
    else:
        for key, value in kwargs.items():
            if a_dict.get(key, None) is None:
                a_dict[key] = value
    return a_dict


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


def stringify(an_obj: Any, encoding: str = sys.getdefaultencoding(),
              errors: str = "ignore") -> str:
    """Improved str() function that automatically decodes bytes.

    :param an_obj: Any
    :param encoding: str, _description_, probably "utf-8" by default
    :param errors: str, _description_, defaults to "ignore"
    :return: str, _description_
    """
    try:
        stringified = str(an_obj, encoding=encoding, errors=errors)
    except TypeError:
        stringified = str(an_obj)
    return stringified


def stringify_duck(an_obj: str | SupportsBytes | dt.datetime | list,
                   sep: str = "_", timespec: str = "seconds",
                   encoding: str = sys.getdefaultencoding(),
                   errors: str = "ignore") -> str:
    """
    _summary_ 
    :param an_obj: str | SupportsBytes | dt.datetime | list, _description_
    :param sep: str,_description_, defaults to "_"
    :param timespec: str,_description_, defaults to "seconds"
    :param encoding: str,_description_, defaults to sys.getdefaultencoding()
    :param errors: str,_description_, defaults to "ignore"
    :return: str, _description_
    """  # TODO REFACTOR (INELEGANT)
    if an_obj is None:
        stringified = ""
    elif isinstance(an_obj, str):
        stringified = an_obj
    elif hasattr(an_obj, "isoformat"):  # .strftime("%Y-%m-%d_%H-%M-%S")
        stringified = an_obj.isoformat(sep=sep, timespec=timespec
                                       ).replace(":", "-")
    elif isinstance(an_obj, list):
        list_with_str_els = [stringify_duck(el) for el in an_obj]
        if len(an_obj) > 1:
            stringified = "'{}'".format("', '".join(list_with_str_els))
        else:
            stringified = list_with_str_els[0]
    else:
        try:
            stringified = str(an_obj, encoding=encoding, errors=errors)
        except TypeError:
            stringified = str(an_obj)
    return stringified


def stringify_dt(moment: dt.datetime) -> str:
    """
    :param moment: datetime, a specific moment
    :return: String, that moment in "YYYY-mm-dd_HH-MM-SS" format
    """  # TODO Combine w/ stringify() function?
    return moment.isoformat(sep="_", timespec="seconds"
                            ).replace(":", "-")  # .strftime("%Y-%m-%d_%H-%M-%S")


def stringify_list(a_list: list, quote: str | None = "'",
                   sep: str = ",") -> str:
    """
    :param a_list: List[Any]
    :return: str containing all items in a_list, single-quoted and \
             comma-separated if there are multiple
    """  # TODO Combine w/ stringify() function?
    result = a_list
    if isinstance(a_list, list):  # TODO REFACTOR (INELEGANT)
        list_with_str_els = [stringify(el) for el in a_list]

        match len(a_list):
            case 0:
                result = ""
            case 1:
                result = quote + list_with_str_els[0] + quote \
                    if quote else list_with_str_els[0]
            case 2:
                result = " and ".join(list_with_str_els)
            case _:
                except_end = (sep + " ").join(list_with_str_els[:-1])
                result = f"{except_end}{sep} and {list_with_str_els[-1]}"
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
