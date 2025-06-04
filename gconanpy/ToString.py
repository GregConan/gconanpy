#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-06-03
"""
# Import standard libraries
from collections.abc import Callable, Collection, Iterable, Mapping
import datetime as dt
import os
import re
import sys
from typing import Any, Literal, TypeVar
from typing_extensions import Self

# Import third-party PyPI libraries
import pathvalidate

# Import local custom libraries
try:
    from metafunc import MethodWrapper
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.metafunc import MethodWrapper


class ToString(str):
    _S = TypeVar("_S")  # for truncate(...) function
    _TIMESPEC = Literal["auto", "hours", "minutes", "seconds", "milliseconds",
                        "microseconds"]  # for datetime.isoformat
    Stringifier = Callable[[Any], Self]

    # Wrap string methods so they return a ToString instance
    # TODO Wrap these methods programmatically, not 1 at a time manually
    # capitalize = MethodWrapper.return_as_its_class(str.capitalize)  # TODO
    # expandtabs = MethodWrapper.return_as_its_class(str.expandtabs)  # TODO
    join = MethodWrapper.return_as_its_class(str.join)
    ljust = MethodWrapper.return_as_its_class(str.ljust)
    # lower = MethodWrapper.return_as_its_class(str.lower)  # TODO
    removeprefix = MethodWrapper.return_as_its_class(str.removeprefix)
    removesuffix = MethodWrapper.return_as_its_class(str.removesuffix)
    replace = MethodWrapper.return_as_its_class(str.replace)
    rjust = MethodWrapper.return_as_its_class(str.rjust)
    # swapcase = MethodWrapper.return_as_its_class(str.swapcase)  # TODO
    # title = MethodWrapper.return_as_its_class(str.title)  # TODO
    translate = MethodWrapper.return_as_its_class(str.translate)
    # upper = MethodWrapper.return_as_its_class(str.upper)  # TODO

    @MethodWrapper.return_as_its_class  # method returns ToString
    def __add__(self, value: str | None) -> str:
        """ Append `value` to the end of `self`. Implements `self + value`. \
            Defined explicitly so that `ToString() + str() -> ToString` \
            instead of returning a `str` object.

        :param value: str | None
        :return: ToString, `self` with `value` appended after it; \
            `if not value`, then `return self` unchanged.
        """
        return super().__add__(value) if value else self

    @MethodWrapper.return_as_its_class  # method returns ToString
    def __sub__(self, value: str | None) -> str:
        """ Remove `value` from the end of `self`. Implements `self - value`. 
            Defined as a shorter but still intuitive alias for `removesuffix`.

        :param value: str | None
        :return: ToString, `self` without `value` at the end; if `self` \
            doesn't end with `value` or `if not value`, then \
            `return self` unchanged.
        """
        return super().removesuffix(value) if value else self

    def enclosed_by(self, affix: str) -> Self:
        """
        :param affix: str to prepend and append to this ToString instance
        :return: ToString with `affix` at the beginning and another at the end
        """
        return self.enclosed_in(affix, affix)

    def enclosed_in(self, prefix: str | None, suffix: str | None) -> Self:
        """
        :param prefix: str to prepend to this ToString instance
        :param suffix: str to append to this ToString instance
        :return: ToString with `prefix` at the beginning & `suffix` at the end
        """
        return self.that_starts_with(prefix).that_ends_with(suffix) \
            if len(self) else self.__class__(prefix) + suffix

    @classmethod
    def filepath(cls, dir_path: str, file_name: str, file_ext: str = "",
                 put_date_after: str | None = None, max_len: int | None = None
                 ) -> Self:
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
        # Ensure that file extension starts with a period
        file_ext = cls(file_ext).that_starts_with(".")

        # Remove special characters not covered by pathvalidate.sanitize_filename
        file_name = re.sub(r"[?:\=\.\&\?]*", '', file_name)

        # Get max file name length by subtracting from max file path length
        if max_len is None:
            max_len = os.pathconf(dir_path, "PC_NAME_MAX")
        else:
            max_len -= len(dir_path) + 1  # +1 for sep char between dir & name
        if put_date_after is not None:

            # Get ISO timestamp to append to file name  # dt.datetime.now()
            put_date_after += cls.from_datetime(dt.date.today())

        # Make max_len take file extension and datetimestamp into account
            max_len -= len(put_date_after)
        max_len -= len(file_ext)

        # Remove any characters illegal in file paths/names and truncate name
        file_name = pathvalidate.sanitize_filename(file_name, max_len=max_len)

        # Combine directory path and file name
        return cls(os.path.join(dir_path, file_name)

                   # Add datetimestamp and file extension
                   ).that_ends_with(put_date_after).that_ends_with(file_ext)

    @classmethod
    def from_datetime(cls, moment: dt.date | dt.time | dt.datetime,
                      sep: str = "_", timespec: _TIMESPEC = "seconds",
                      replace: Mapping[str, str] = {":": "-"}) -> Self:
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
        return cls(stringified).replacements(replace)

    @classmethod
    def from_iterable(cls, an_obj: Collection, quote: str | None = "'",
                      sep: str = ", ", quote_numbers: bool = False,
                      prefix: str | None = "[", suffix: str | None = "]",
                      max_len: int | None = None, lastly: str = "and "
                      ) -> Self:
        """ Convert an Iterable into a ToString object.

        :param an_obj: Collection to convert ToString
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
                except_end = sep.join(list_with_str_els[:-1])
                string = f"{except_end}{sep}{lastly}{list_with_str_els[-1]}"
            elif lastly:
                if lastly.endswith(" "):
                    lastly = cls(lastly).that_starts_with(" ")
                string = lastly.join(list_with_str_els)
            else:
                string = sep.join(list_with_str_els)
        self = cls(string)
        if max_len is not None:
            affix_len = sum([len(x) if x else 0 for x in (prefix, suffix)])
            self = self.truncate(max_len - affix_len)
        return self.enclosed_in(prefix, suffix)

    @classmethod
    def from_object(cls, an_obj: Any, max_len: int | None = None,
                    quote: str | None = "'", quote_numbers: bool = False,
                    quote_keys: bool = True, join_on: str = ": ",
                    sep: str = ", ", prefix: str | None = None,
                    suffix: str | None = None,
                    dt_sep: str = "_", timespec: _TIMESPEC = "seconds",
                    replace: Mapping[str, str] = {":": "-"},
                    encoding: str = sys.getdefaultencoding(),
                    errors: str = "ignore", lastly: str = "and ") -> Self:
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
                                               quote_keys, join_on, prefix, suffix,
                                               sep, max_len, lastly)
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
                     quote_numbers: bool = False, quote_keys: bool = True,
                     join_on: str = ": ",
                     prefix: str | None = "{", suffix: str | None = "}",
                     sep: str = ", ", max_len: int | None = None,
                     lastly: str = "and ") -> Self:
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
            k = quotate(k) if quote_keys else k
            v = quotate(v).truncate(max_len, quotate)
            pair_strings.append(join_on.join((k, v)))
        return cls.from_iterable(pair_strings, quote=None, prefix=prefix,
                                 suffix=suffix, max_len=max_len, sep=sep,
                                 lastly=lastly)

    @classmethod
    def get_quotator(cls, quote: str | None = "'",
                     quote_numbers: bool = False) -> Stringifier:
        quotate = cls.quotate_obj if quote_numbers else cls.quotate_number
        return cls.from_object if not quote else lambda x: quotate(x, quote)

    @MethodWrapper.return_as_its_class
    def replacements(self, replace: Mapping[str, str], count: int = -1) -> str:
        string = self  # cls = self.__class__
        for old, new in replace.items():
            string = string.replace(old, new, count)
        return string

    @classmethod
    def quotate_all(cls, objects: Iterable, quote: str | None = "'",
                    quote_numbers: bool = False, max_len: int | None = None
                    ) -> list[Self]:
        finish = cls.get_quotator(quote, quote_numbers)
        return [finish(obj).truncate(max_len) for obj in objects]

    @classmethod
    def quotate_number(cls, a_num: Any, quote: str = "'") -> Self:
        stringified = cls.from_object(a_num)
        return stringified if stringified.isnumeric() \
            else stringified.enclosed_by(quote)

    @classmethod
    def quotate_obj(cls, an_obj: Any, quote: str = "'") -> Self:
        """
        :param an_obj: Any, object to convert ToString.
        :param quote: str to add before and after `an_obj`; defaults to "'"
        :return: ToString, `quote + stringify(an_obj) + quote`
        """
        return cls.from_object(an_obj).enclosed_by(quote)

    def that_ends_with(self, suffix: str | None) -> Self:
        """ Append `suffix` to the end of `self` unless it is already there.

        :param suffix: str to append to `self`, or None to do nothing.
        :return: ToString ending with `suffix`.
        """
        return self if not suffix or self.endswith(suffix) else self + suffix

    @MethodWrapper.return_as_its_class  # method returns ToString
    def that_starts_with(self, prefix: str | None) -> str:
        """ Prepend `suffix` at index 0 of `self` unless it is already there.

        :param prefix: str to prepend to `self`, or None to do nothing.
        :return: ToString beginning with `prefix`.
        """
        return self if not prefix or self.startswith(prefix) else prefix + self

    def truncate(self, max_len: int | None = None,
                 quotate: Stringifier | None = None,
                 suffix: str = "...") -> Self:
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
stringify_iter = ToString.from_iterable
