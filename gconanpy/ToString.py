#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-05-04
"""
# Import standard libraries
from collections.abc import Callable, Iterable, Mapping
import datetime as dt
import os
import re
import sys
from typing import Any, Literal, TypeVar

# Import third-party PyPI libraries
import pathvalidate


class ToString(str):
    _S = TypeVar("_S")  # for truncate(...) function
    _TIMESPEC = Literal["auto", "hours", "minutes", "seconds", "milliseconds",
                        "microseconds"]  # for datetime.isoformat
    BLANKS: set[str | None] = {None, ""}  # Objects not to show in strings
    Quotator = Callable[[Any], "ToString"]

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

    def ends(self, other: str) -> bool:
        """ `x.ends(y)` is `y.endswith(x)`.

        :param other: str, _description_
        :return: bool, True if other ends with self; else False
        """
        return other.endswith(self)

    @classmethod
    def filepath(cls, dir_path: str, file_name: str, file_ext: str = "",
                 put_dt_after: str | None = None, max_len: int | None = 255
                 ) -> "ToString":
        """
        :param dir_path: str, valid path to directory containing the file
        :param file_name: str, name of the file excluding path and extension
        :param file_ext: str, the file's extension; defaults to empty string
        :param put_dt_after: str | None; include this to automatically generate \
                            the current date and time in ISO format and insert \
                            it into the filename after the specified delimiter. \
                            Exclude this argument to exclude date/time from path.
        :param max_len: int, maximum filename byte length. Truncate the name if \
                        the filename length exceeds this value. None means 255.
        :return: str, the new full file path
        """
        # Remove special characters not covered by pathvalidate.sanitize_filename
        file_name = re.sub(r"[?:\=\.\&\?]*", '', file_name)

        if put_dt_after is not None:  # Get ISO timestamp to append to file name
            put_dt_after += cls.from_datetime(dt.datetime.now())

        # Get max file name length by subtracting from max file path length
            max_len -= len(put_dt_after)
        max_len -= len(dir_path)
        max_len -= len(file_ext)

        # Remove any characters illegal in file paths/names and truncate name
        file_name = pathvalidate.sanitize_filename(file_name, max_len=max_len)

        # Combine directory path and file name
        return cls(os.path.join(dir_path, file_name)

                   # Add datetimestamp and file extension
                   ).that_ends_with(put_dt_after).that_ends_with(file_ext)

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
        match moment:
            case dt.datetime():
                stringified = dt.datetime.isoformat(moment, sep=sep,
                                                    timespec=timespec)
            case dt.date():
                stringified = dt.date.isoformat(moment)
            case dt.time():
                stringified = dt.time.isoformat(moment, timespec=timespec)
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
        """  # Class pattern match: stackoverflow.com/questions/72295812
        match an_obj:
            case bytes() | bytearray():
                stringified = cls(an_obj, encoding=encoding, errors=errors)
            case dict():
                stringified = cls.from_mapping(an_obj, quote, quote_numbers,
                                               join_on, prefix, suffix, sep,
                                               max_len, lastly)
            case list() | tuple() | set():
                stringified = cls.from_iterable(an_obj, quote, sep,
                                                quote_numbers, prefix, suffix,
                                                max_len, lastly)
            case dt.date() | dt.time() | dt.datetime():
                stringified = cls.from_datetime(an_obj, dt_sep,
                                                timespec, replace)
            case None:
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

    def starts(self, other: str) -> bool:
        """ `x.starts(y)` is `y.startswith(x)`.

        :param other: str, _description_
        :return: bool, True if other starts with self; else False
        """
        return other.startswith(self)

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

                # TODO Use independent truncate() function here again (DRY)?
                raw_truncated = (self[:raw_max_len] if len(self) > raw_max_len
                                 else self) + suffix

                truncated = self.__class__(quotate(raw_truncated) if quotate
                                           else raw_truncated)
        return truncated


# Shorter names to export
stringify = ToString.from_object
stringify_dt = ToString.from_datetime
stringify_map = ToString.from_mapping
stringify_seq = ToString.from_iterable
