#!/usr/bin/env python3

"""
FancyString class wraps builtin str class to add extra string functionality.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2026-03-05
"""
# Import standard libraries
# from collections import UserString  # TODO?
from collections.abc import Callable, Collection, Iterable, Mapping
import datetime as dt
from numbers import Number
import os
import re
import sys
from typing import Any, cast, Literal, ParamSpec, Self, SupportsIndex

# Import third-party PyPI libraries
import bs4
import pathvalidate

# Import local custom libraries
try:
    from gconanpy.meta import bool_pair_to_cases, cached_property, \
        MethodWrappingMeta, name_of, TimeSpec
    from gconanpy.meta.typeshed import NonTxtCollection
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from .meta import bool_pair_to_cases, cached_property, \
        MethodWrappingMeta, name_of, TimeSpec
    from .meta.typeshed import NonTxtCollection

# Type variables
_P = ParamSpec("_P")

# Different kinds of text cases
StrCase = Literal["camel", "capitalize", "kebab", "lower", "macro",
                  "pascal", "snake", "title", "train", "upper"]


class DelimitedCase:
    """ A specific string/text case delimited by a specific character. 

    Represents the following text cases used frequently in code:
    `kebab-case`, `MACRO_CASE`, `snake_case`, and `TRAIN-CASE`. """
    sep: str
    is_case: Callable[[str], bool]
    to_case: Callable[[str], str]

    def __init__(self, sep: str, upper: bool) -> None:
        self.sep = sep
        self.is_case, self.to_case = (str.isupper, str.upper) if upper \
            else (str.islower, str.lower)


# String/text cases for code, each delimited by a specific character:
# kebab (lowercase dash-delimited), macro (uppercase underscore-delimited),
# snake (lowercase underscore-delimited), & train (uppercase dash-delimited)
DELIM_CASES: dict[StrCase, DelimitedCase] = {
    "kebab": DelimitedCase("-", False), "macro": DelimitedCase("_", True),
    "snake": DelimitedCase("_", False), "train": DelimitedCase("-", True)}


class FancyString(str, metaclass=MethodWrappingMeta):
    # The metaclass wraps every str method that returns str so it returns
    # a FancyString instance instead.

    def __add__(self, value: str | None) -> Self:
        """ Append `value` to the end of `self`. Implements `self + value`.
            Defined explicitly so that `FancyString() + str() -> FancyString`
            instead of returning a `str` object.

        :param value: str | None
        :return: FancyString, `self` with `value` appended after it;
            `if not value`, then `return self` unchanged.
        """
        return self if value is None else type(self)(super().__add__(value))

    def __sub__(self, value: str | None) -> Self:
        """ Remove `value` from the end of `self`. Implements `self - value`.
            Defined as a shorter but still intuitive alias for `removesuffix`.

        :param value: str | None
        :return: FancyString, `self` without `value` at the end; if `self`
            doesn't end with `value` or `if not value`, then
            `return self` unchanged.
        """
        return self if value is None else cast(Self, self.removesuffix(value))

    def enclosed_by(self, affix: str) -> Self:
        """
        :param affix: str to prepend and append to this `FancyString` instance
        :return: FancyString starting and ending with `affix`
        """
        return self.enclosed_in(affix, affix)

    def enclosed_in(self, prefix: str | None, suffix: str | None) -> Self:
        """
        :param prefix: str to prepend to this `FancyString` instance
        :param suffix: str to append to this `FancyString` instance
        :return: FancyString starting with `prefix` and ending with `suffix`
        """
        return self.that_starts_with(prefix).that_ends_with(suffix) \
            if len(self) else self.that_starts_with(prefix) + suffix

    @classmethod
    def filepath(cls, dir_path: str, file_name: str, file_ext: str = "",
                 put_date_after: str | None = None, max_len: int | None = None
                 ) -> Self:
        """
        :param dir_path: str, valid path to directory containing the file
        :param file_name: str, name of the file excluding path and extension
        :param file_ext: str, the file's extension; defaults to empty string
        :param put_dt_after: str | None; include this to automatically generate
                            the current date and time in ISO format and insert
                            it into the filename after the specified delimiter.
                            Exclude this to exclude date/time from path.
        :param max_len: int, maximum filename byte length. Truncate the name if
                        the filename length exceeds this value. None means 255.
        :return: str, the new full file path
        """
        # Ensure that file extension starts with a period
        file_ext = cls(file_ext).that_starts_with(".")

        # Remove special characters that pathvalidate.sanitize_filename doesn't
        file_name = re.sub(r"[?:\=\.\&\?]*", '', file_name)

        # Get max file name length by subtracting from max file path length
        if max_len is None:
            max_len = os.pathconf(dir_path, "PC_NAME_MAX")
        else:
            max_len -= len(dir_path) + 1  # +1 for sep char between dir & name
        if put_date_after is not None:

            # Get ISO timestamp to append to file name  # dt.datetime.now()
            put_date_after += cls.fromDateTime(dt.date.today())

        # Make max_len take file extension and datetimestamp into account
            max_len -= len(put_date_after)
        max_len -= len(file_ext)

        # Remove any characters illegal in file paths/names and truncate name
        file_name = pathvalidate.sanitize_filename(file_name, max_len=max_len)

        # Combine directory path and file name
        return cls(os.path.join(dir_path, file_name)

                   # Add datetimestamp and file extension
                   ).that_ends_with(put_date_after).that_ends_with(file_ext)

    def force_join(self, iterable: Iterable, **format: Any) -> Self:
        """ Coerce the elements of `iterable` together into a string.

        :param iterable: Iterable to coercively convert into a string.
        :param format: Mapping[str, Any], `fromIterable` parameters; include
            these to format the elements while joining them.
        :return: Self, `iterable` converted into a `FancyString`.
        """
        cls = type(self)
        if format:
            return cls.fromIterable([cls.fromAny(el, **format)
                                     for el in iterable])
        else:
            return cls(self.join(cls(el) for el in iterable))

    @classmethod
    def fromAny(cls, an_obj: Any, max_len: int | None = None,
                quote: str | None = "'", quote_numbers: bool = False,
                quote_keys: bool = True, join_on: str = ": ",
                sep: str = ", ", prefix: str | None = None,
                suffix: str | None = None, dt_sep: str = "_",
                timespec: TimeSpec.UNIT = "seconds",
                replace: Mapping[str, str] = {":": "-"},
                encoding: str = sys.getdefaultencoding(),
                errors: str = "ignore", lastly: str = "and ",
                iter_kwargs: dict[str, Any] = {}) -> Self:
        """ Convert an object into a `FancyString`.

        :param an_obj: Any, object to convert into a `FancyString`
        :param max_len: int, size of the longest possible FancyString to return
            without truncation, or None to never truncate; defaults to None
        :param quote: str to add before and after each element of `an_obj`,
            or None to insert no quotes; defaults to "'"
        :param quote_numbers: bool, True to insert `quote` before and after
            each numerical element of `an_obj`; else False to add no
            quotes to numbers in `an_obj`; defaults to False
        :param join_on: str to insert between the key and value of each
            key-value pair in `an_obj` if it's a Mapping; defaults to ": "
        :param sep: str to insert between all of the elements of `an_obj`,
            or None to insert no such separators; defaults to ", "
        :param prefix: str to insert as the first character of the returned
            FancyString object, or None to add no prefix; defaults to None
        :param suffix: str to insert as the last character of the returned
            FancyString object, or None to add no suffix; defaults to None
        :param dt_sep: str, separator between date and time; defaults to "_"
        :param timespec: str specifying the number of additional terms of
            the time to include; defaults to "seconds".
        :param replace: Mapping[str, str] of parts (in the result of calling
            `datetime.*.isoformat` on a `datetime`-typed `an_obj`) to
            different strings to replace them with; by default, will replace
            ":" with "-" for adding datetimestamps to file names.
        :param encoding: str,_description_, defaults to
            `sys.getdefaultencoding()`
        :param errors: str, _description_, defaults to "ignore"
        :param lastly: str to insert after the last `sep` in the returned
            FancyString object `if len(an_obj) > 2`, or None to add no such
            string; defaults to "and "
        :return: FancyString of `an_obj` formatted as specified.
        """
        # If the max_len is too low for anything besides the affixes, then
        # return just the affixes if they fit, else return an empty FancyString
        if max_len is not None:
            if prefix:
                max_len -= len(prefix)
            if suffix:
                max_len -= len(suffix)
            if max_len < 0:
                return cls()
            elif max_len == 0:
                return cls().enclosed_in(prefix, suffix)

        match an_obj:  # Stringify!
            case bytes() | bytearray():
                stringified = cls(an_obj, encoding=encoding, errors=errors
                                  ).truncate(max_len)
            case Mapping():
                stringified = cls.fromMapping(
                    an_obj, quote, quote_numbers, quote_keys, join_on, prefix,
                    suffix, sep, max_len, lastly, iter_kwargs)
            case Callable():
                stringified = cls.fromCallable(an_obj, max_len)
            case Collection():
                stringified = cls.fromIterable(
                    an_obj, quote, sep, quote_numbers, prefix, suffix,
                    max_len, lastly, iter_kwargs)
            case dt.date() | dt.time() | dt.datetime():
                stringified = cls.fromDateTime(
                    an_obj, dt_sep, timespec, replace).truncate(max_len)
            case None:
                stringified = cls()
            case bs4.element.PageElement():
                stringified = cls.fromBeautifulSoup(an_obj)
            case _:  # other
                stringified = cls(an_obj).truncate(max_len)
        return stringified

    @classmethod
    def fromBeautifulSoup(cls, soup: bs4.element.PageElement | None, tag:
                          Literal["all", "first", "last"] = "all") -> Self:
        """ Convert a `BeautifulSoup` object (from `bs4`) to a `FancyString`.

        :param soup: bs4.element.PageElement, or None to get an empty string.
        :param tag: Literal["all", "first", "last"], which HTML document tag
            to represent as a string: "first" means only the opening tag,
            "last" means only the closing tag, and "all" means both plus
            everything in between them.
        :return: FancyString representing the `BeautifulSoup` object.
        """
        match soup:
            case bs4.Tag():
                match tag:
                    case "all":
                        stringified = str(soup)
                    case "first":
                        attrs = getattr(soup, "attrs", None)
                        attrstr = " " + cls.fromMapping(
                            attrs, quote_keys=False, join_on="=", prefix=None,
                            suffix=None, sep=" ", lastly="") if attrs else ""
                        stringified = f"<{soup.name}{attrstr}>"
                    case "last":
                        stringified = f"</{soup.name}>"
            case bs4.element.NavigableString():
                stringified = soup.string
            case None:
                stringified = ""
            case _:
                raise TypeError(f"`{soup}` is not a bs4.element.PageElement")
        return cls(stringified)

    @classmethod
    def fromCallable(cls, an_obj: Callable, max_len: int | None = None,
                     *args: Any, **kwargs: Any) -> Self:
        """ Convert a `Callable` object, such as a function or class, into a
            `FancyString` instance.

        :param an_obj: Callable to stringify.
        :param max_len: int, size of the longest possible FancyString to return
            without truncation, or None to never truncate; defaults to None.
        :param args: Iterable[Any], input parameters to represent calling
            `an_obj` with. `args=[1,2,3]` -> `"an_obj(1, 2, 3)"`.
        :param kwargs: Mapping[str, Any], keyword input parameters to
            represent calling `an_obj` with. `kwargs={"a": 1, "b": 2}` ->
            `"an_obj(a=1, b=2)"`.
        :return: FancyString representing the `Callable` object `an_obj`.
        """
        # Put all pre-defined args and kwargs into this instance's str repr
        iter_kwargs = dict(prefix="[", suffix="]", lastly="")
        kwargstrs = cls.fromMapping(kwargs, quote_keys=False, prefix=None,
                                    suffix=None, join_on="=", max_len=max_len,
                                    lastly="", iter_kwargs=iter_kwargs)
        argstrs = cls.fromIterable(args, prefix=None, suffix=None, lastly="")
        match bool_pair_to_cases(argstrs, kwargstrs):
            case 0:  # neither argstrs nor kwargstrs
                stringified = ""
            case 1:  # only argstrs
                stringified = f"({argstrs})"
            case 2:  # only kwargstrs
                stringified = f"({kwargstrs})"
            case 3:  # both argstrs and kwargstrs
                stringified = f"({', '.join((argstrs, kwargstrs))})"
        # TODO instead of using name_of, use Regextract.PY_REPR_TO_NAME
        #      or classgetattr(an_obj, "__qualname__")?
        return cls(f"{name_of(an_obj, '__qualname__')}{stringified}")

    @classmethod
    def fromDateTime(cls, moment: dt.date | dt.time | dt.datetime,
                     sep: str = "_", timespec: TimeSpec.UNIT = "seconds",
                     replace: Mapping[str, str] = {":": "-"}) -> Self:
        """ Return the time formatted according to ISO as a FancyString object.

        The full format is 'HH:MM:SS.mmmmmm+zz:zz'. By default, the fractional
        part is omitted if moment.microsecond == 0.

        :param moment: dt.date | dt.time | dt.datetime to convert to string.
        :param sep: str, the separator between date and time; defaults to "_"
        :param timespec: str specifying the number of additional terms of
            the time to include; defaults to "seconds".
        :param replace: Mapping[str, str] of parts (in the result of calling
            `moment.isoformat`) to different strings to replace them with;
            by default, this will replace ":" with "-" (for naming files).
        :return: FancyString, string representation of `moment`
        """
        match moment:
            case dt.datetime():
                stringified = dt.datetime.isoformat(moment, sep=sep,
                                                    timespec=timespec)
            case dt.date():
                stringified = dt.date.isoformat(moment)
            case dt.time():
                stringified = dt.time.isoformat(moment, timespec=timespec)
        return cls(stringified).replace_all(replace)

    @classmethod
    def fromIterable(cls, an_obj: Collection, quote: str | None = "'",
                     sep: str = ", ", quote_numbers: bool = False,
                     prefix: str | None = "[", suffix: str | None = "]",
                     max_len: int | None = None, lastly: str = "and ",
                     iter_kwargs: Mapping[str, Any] = {}) -> Self:
        """ Convert a Collection (e.g. a list, tuple, or set) into an
            instance of the `FancyString` class.

        :param an_obj: Collection to convert into a `FancyString`
        :param quote: str to add before and after each element of `an_obj`,
            or None to insert no quotes; defaults to "'"
        :param sep: str to insert between all of the elements of `an_obj`,
            or None to insert no such separators; defaults to ", "
        :param quote_numbers: bool, True to insert `quote` before and after
            each numerical element of `an_obj`; else False to add no
            quotes to numbers in `an_obj`; defaults to False
        :param prefix: str to insert as the first character of the returned
            `FancyString` object, or None to add no prefix; defaults to "["
        :param suffix: str to insert as the last character of the returned
            `FancyString` object, or None to add no suffix; defaults to "]"
        :param max_len: int, size of the longest possible FancyString to return
            without truncation, or None to never truncate; defaults to None
        :param lastly: str to insert after the last `sep` in the returned
            `FancyString` object `if len(an_obj) > 2`, or None to add no such
            string; defaults to "and "
        :param iter_kwargs: Mapping[str, Any], keyword input parameters to
            pass to `quotate` for each element of `an_obj`; defaults to
            an empty `dict`.
        :return: FancyString of all elements in `an_obj`, `quote`-quoted and
                 `sep`-separated if there are multiple elements, starting
                 with `prefix` and ending with `suffix`, with `lastly` after
                 the last `sep` if there are more than 2 elements of `an_obj`.
        """
        if not an_obj:
            stringified = ""
        elif isinstance(an_obj, str):  # TODO Refactor from LBYL to EAFP?
            stringified = an_obj
        else:
            list_of_strings = cls.quotate_all(an_obj, quote, quote_numbers,
                                              max_len, iter_kwargs)
            if len(an_obj) > 2:
                except_end = sep.join(list_of_strings[:-1])
                stringified = f"{except_end}{sep}{lastly}{list_of_strings[-1]}"
            elif lastly:
                if lastly.endswith(" "):
                    lastly = cls(lastly).that_starts_with(" ")
                stringified = lastly.join(list_of_strings)
            else:
                stringified = sep.join(list_of_strings)
        self = cls(stringified)
        if max_len is not None:
            affix_len = sum([len(x) if x else 0 for x in (prefix, suffix)])
            self = self.truncate(max_len - affix_len)
        return self.enclosed_in(prefix, suffix)

    @classmethod
    def fromMapping(cls, a_map: Mapping, quote: str | None = "'",
                    quote_numbers: bool = False, quote_keys: bool = True,
                    join_on: str = ": ",
                    prefix: str | None = "{", suffix: str | None = "}",
                    sep: str = ", ", max_len: int | None = None,
                    lastly: str = "and ",
                    iter_kwargs: Mapping[str, Any] = {}) -> Self:
        """
        :param a_map: Mapping to convert into a `FancyString`
        :param quote: str to add before and after each key-value pair in
            `a_map`, or None to insert no quotes; defaults to "'"
        :param quote_numbers: bool, True to insert `quote` before and after
            each numerical key or value in `a_map`; else False to add no
            quotes to numbers in `a_map`; defaults to False
        :param join_on: str to insert between the key and value of each
            key-value pair in `a_map`; defaults to ": "
        :param prefix: str to insert as the first character of the returned
            FancyString object, or None to add no prefix; defaults to "{"
        :param suffix: str to insert as the last character of the returned
            FancyString object, or None to add no suffix; defaults to "}"
        :param sep: str to insert between all of the key-value pairs in
            `a_map`, or None to insert no such separators; defaults to ", "
        :param max_len: int, size of the longest possible FancyString to return
            without truncation, or None to never truncate; defaults to None
        :param lastly: str to insert after the last `sep` in the returned
            FancyString object `if len(a_map) > 2`, or None to add no such
            string; defaults to "and "
        :param iter_kwargs: Mapping[str, Any], keyword input parameters to
            pass to `quotate` for each key-value pair in `a_map`; defaults to
            an empty `dict`.
        :return: FancyString, string representation of `a_map`
        """
        join_on = cls(join_on)
        pair_strings = []
        for k, v in a_map.items():
            k = cls.quotate(k, quote, quote_numbers) if quote_keys else cls(k)
            v = cls.quotate(v, quote, quote_numbers, quote_keys, **iter_kwargs
                            ) if iter_kwargs else \
                cls.quotate(v, quote, quote_numbers, quote_keys,
                            max_len=max_len, join_on=join_on, sep=sep,
                            prefix=prefix, suffix=suffix, lastly=lastly)
            pair_strings.append(join_on.join((k, v)))
        return cls.fromIterable(pair_strings, quote=None, prefix=prefix,
                                suffix=suffix, max_len=max_len, sep=sep,
                                lastly=lastly, iter_kwargs=iter_kwargs)

    def is_case(self, str_case: StrCase) -> bool:
        """ Return True if the string is the specified case, False otherwise.

        "camel": camelCase
        "capitalize": Capitalized case
        "kebab": kebab-case
        "lower": lower case
        "macro": MACRO-CASE
        "pascal": PascalCase
        "snake": snake_case
        "title": Title Case
        "train": TRAIN-CASE
        "upper": UPPER CASE

        :param str_case: Literal['camel', 'capitalize', 'kebab', 'lower',
            'macro', 'pascal', 'snake', 'title', 'train', 'upper']
        :return: bool, True if this string is in the specified case 
            (`str_case`), otherwise False
        """
        try:  # Default methods to check if self is lower, UPPER, or Title case
            return {"lower": self.islower, "title": self.istitle,
                    "upper": self.isupper}[str_case]()
        except KeyError:
            # Handle only remaining default text case: capitalized
            first_char = self[0]
            if str_case == "capitalize":
                return first_char.isupper() and self[1:].islower()

            else:  # Handle code cases: camel, kebab, macro, pascal, & snake

                # Code cases must start with a letter and have no whitespace
                if first_char.isdigit() or len(self.split()) > 1:
                    return False

                try:  # Verify camelCase and PascalCase by checking the first
                    #   letter's case and that all chars are alphanumeric
                    return {"camel": first_char.islower,
                            "pascal": first_char.isupper}[str_case]() \
                        and self.isalnum()
                except KeyError:
                    pass

                # Only snake_case & MACRO_CASE should have underscores
                under_split = self.split("_")
                if str_case not in {"macro", "snake"} and len(under_split) > 1:
                    return False

                # Only kebab-case & TRAIN-CASE should have dashes
                dash_split = self.split("-")
                if str_case not in {"kebab", "train"} and len(dash_split) > 1:
                    return False

                # Verify lowercase (if kebab or snake) else uppercase
                this_case = DELIM_CASES[str_case]
                if not this_case.is_case(self):
                    return False

                # Verify that every word only contains letters and numbers
                for word in self.split(this_case.sep):
                    if not word.isalnum():
                        return False

                return True

    @classmethod
    def quotate(cls, an_obj: Any, quote: str | None = "'",
                quote_numbers: bool = False, quote_keys: bool = False,
                **iter_kwargs: Any) -> Self:
        """ Convert an object (`an_obj`) into a `FancyString` and enclose it
            inside quotation marks (`quote`) if any.

        :param an_obj: Any, object to enclose a string representation of within
            the specified quotation marks
        :param quote: str | None, quotation mark character to prepend and 
            append to `an_obj`, or None to not quotate it; defaults to "'"
        :param quote_numbers: bool, True to enclose numbers in quotation marks,
            else False to convert them to string unchanged; defaults to False
        :param quote_keys: bool, True to enclose `Mapping` keys in quotation
            marks, else False to leave them unchanged; defaults to False
        :param **iter_kwargs: Any, formatting parameters to pass to the
            `FancyString.from*` methods when calling them on each element of
            `an_obj` if `an_obj` is an `Iterable`
        :return: Self, `an_obj` converted into quotated `FancyString`s
        """
        if not quote:
            quoted = cls(an_obj)
        else:
            match an_obj:
                case Mapping():
                    quoted = cls.fromMapping(an_obj, quote, quote_numbers,
                                             quote_keys, **iter_kwargs)
                    # , iter_kwargs=iter_kwargs)
                case Callable():
                    quoted = cls.fromCallable(an_obj)
                case NonTxtCollection():
                    # use the recursive iter_kwargs input parameter without
                    # adding a parameter exclusive to fromMapping method
                    iter_kwargs = {k: v for k, v in iter_kwargs.items()
                                   if k != "join_on"}

                    quoted = cls.fromIterable(
                        an_obj,  # type: ignore  # TODO FIX NonTxtCollection
                        quote, quote_numbers=quote_numbers, **iter_kwargs)
                case Number():
                    quoted = cls(an_obj).enclosed_by(quote) \
                        if quote_numbers else cls(an_obj)
                case None:
                    quoted = cls().enclosed_by(quote)
                case _:
                    quoted = cls(an_obj).enclosed_by(quote)
        return quoted

    @classmethod
    def quotate_all(cls, objects: Iterable, quote: str | None = "'",
                    quote_numbers: bool = False, max_len: int | None = None,
                    iter_kwargs: Mapping[str, Any] = {}) -> list[Self]:
        """ Convert all `objects` into `FancyString`s and enclose each of them
            inside quotation marks (`quote`) if any.

        :param objects: Iterable, objects to enclose string representations of
            within the specified quotation marks
        :param quote: str | None, quotation mark character to prepend and 
            append to each object in `objects`, or None to not quotate them;
            defaults to "'"
        :param quote_numbers: bool, True to enclose numbers in quotation marks,
            else False to convert them to string unchanged; defaults to False
        :param max_len: int | None, maximum number of characters in each string
            representation of each element of `objects`; defaults to None
        :param iter_kwargs: Mapping[str, Any], formatting parameters to pass to
            each `FancyString.from*` method when calling it on each element of
            each object in `objects` if they are `Iterables`
        :return: list[Self], `objects` converted into quotated `FancyString`s
        """
        iter_kwargs = dict(iter_kwargs)
        for k, v in {"quote": quote, "quote_numbers": quote_numbers,
                     "max_len": max_len}.items():
            iter_kwargs.setdefault(k, v)
        return [cls.quotate(an_obj, **iter_kwargs) for an_obj in objects]

    def replace_all(self, replacements: Mapping[str, str], count: int = -1,
                    reverse: bool = False) -> Self:
        """ Repeatedly run the `replace` (or `rreplace`) method.

        :param replacements: Mapping[str, str] of (old) substrings to their
            (new) respective replacement substrings.
        :param count: int, the maximum number of occurrences of each
            substring to replace. Defaults to -1 (replace all occurrences).
        :param reverse: bool, True to replace the last `count` substrings,
            starting from the end; else (by default) False to replace the
            first `count` substrings, starting from the string's beginning.
        :return: FancyString after replacing `count` key-substrings with their
            corresponding value-substrings in `replace`.
        """
        stringified = self  # cls = type(self)
        replace = FancyString.rreplace if reverse else FancyString.replace
        for old, new in replacements.items():
            stringified = replace(cast(Self, stringified), old, new, count)
        return cast(Self, stringified)

    def rreplace(self, old: str, new: str, count: SupportsIndex = -1) -> Self:
        """ Return a copy with occurrences of substring old replaced by new.
            Like `str.replace`, but replaces the last `old` occurrences first.

        :param old: str, the substring to replace occurrences of with `new`.
        :param new: str to replace `count` occurrences of `old` with.
        :param count: SupportsIndex, the maximum number of occurrences to
            replace. Defaults to -1 (replace all occurrences). Include a
            different number to replace only the LAST `count` occurrences,
            starting from the end of the string.
        :return: FancyString, a copy with its last `count` instances of the
            `old` substring replaced by a `new` substring.
        """
        return type(self)(new.join(self.rsplit(old, count)))

    def rtruncate(self, max_len: int | None = None, prefix: str = "..."
                  ) -> Self:
        """ Trim this string, removing all but the LAST `max_len` characters.

        :param max_len: int | None, maximum number of characters to include
            in this string; defaults to None to leave the string unchanged.
        :param prefix: str to add to the beginning of the returned string to
            indicate that it has been truncated; defaults to "..."
        :return: Self, all but the last `max_len` characters of this string
            (replacing the beginning of it with `prefix` if any) if `max_len` 
            is a number smaller than the current length of this string
        """
        return self if max_len is None or len(self) <= max_len else \
            type(self)(prefix + self[max_len - len(prefix):])

    def that_ends_with(self, suffix: str | None) -> Self:
        """ Append `suffix` to the end of `self` unless it is already there.

        :param suffix: str to append to `self`, or None to do nothing.
        :return: FancyString ending with `suffix`.
        """
        return self if not suffix or self.endswith(suffix) else self + suffix

    def that_starts_with(self, prefix: str | None) -> Self:
        """ Prepend `suffix` at index 0 of `self` unless it is already there.

        :param prefix: str to prepend to `self`, or None to do nothing.
        :return: FancyString beginning with `prefix`.
        """
        return self if not prefix or self.startswith(prefix) else \
            type(self)(prefix) + self

    def to_case(self, str_case: StrCase) -> Self:
        """ Convert this `FancyString` to one of the following specific cases:

        "camel": camelCase
        "capitalize": Capitalized case
        "kebab": kebab-case
        "lower": lower case
        "macro": MACRO-CASE
        "pascal": PascalCase
        "snake": snake_case
        "title": Title Case
        "train": TRAIN-CASE
        "upper": UPPER CASE

        :param str_case: Literal['camel', 'capitalize', 'kebab', 'lower',
            'macro', 'pascal', 'snake', 'title', 'train', 'upper']
        :return: Self, this string converted to the specified case (`str_case`)
        """
        try:  # Defaults: Capitalized case, Title Case, lower case, UPPER CASE
            result = {"capitalize": self.capitalize, "lower": self.lower,
                      "title": self.title, "upper": self.upper}[str_case]()

        # Code cases: camelCase, kebab-case, MACRO_CASE, PascalCase, snake_case
        except KeyError:
            # Code cases must start with a letter
            result = self
            while result and not result[0].isalpha():
                result = result[1:]

            # Split words apart to recombine them later, removing all
            # non-alphanumeric characters from the string
            words = re.split(r"\W+", result)

            # Get the new word separator char, if any (underscore or dash)
            this_case = DELIM_CASES.get(str_case, None)

            if this_case:  # then case is kebab, macro, snake, or train
                result = this_case.sep.join(words)  # Concatenate all words
                result = this_case.to_case(result)  # Convert to lower or upper

            else:  # If there's no new separator, then it's either PascalCase
                #    or camelCase, so first capitalize all words
                words = [word.capitalize() for word in words]

                if str_case == "camel":  # then lowercase the first character
                    words[0] = words[0].lower()

                result = "".join(words)  # Concatenate all words

        return type(self)(result)  # Return as a FancyString

    def truncate(self, max_len: int | None = None, suffix: str = "..."
                 ) -> Self:
        """ Trim this string, removing all but the FIRST `max_len` characters.

        :param max_len: int | None, maximum number of characters to include
            in this string; defaults to None to leave the string unchanged.
        :param suffix: str to add to the end of the returned string to indicate
            that it has been truncated; defaults to "..."
        :return: Self, all but the first `max_len` characters of this string
            (replacing the end of it with `suffix` if any) if `max_len` is a
            number smaller than the current length of this string
        """
        return self if max_len is None or len(self) <= max_len else \
            type(self)(self[:max_len - len(suffix)] + suffix)

    @cached_property[int]
    def width(self) -> int:
        """ :return: int, this string's maximum line width. """
        return max(len(each_line) for each_line in self.split("\n"))


# Shorter names to export
stringify = FancyString.fromAny
stringify_dt = FancyString.fromDateTime
stringify_map = FancyString.fromMapping
stringify_iter = FancyString.fromIterable
