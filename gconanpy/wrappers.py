#!/usr/bin/env python3

"""
Classes that wrap other classes, especially builtins, to add functionality.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-12-31
"""
# Import standard libraries
import argparse
# from collections import UserString  # TODO?
from collections.abc import Callable, Collection, Generator, \
    Hashable, Iterable, Mapping, Sequence
import datetime as dt
from functools import reduce, wraps
from more_itertools import all_equal
import os
import re
import sys
from typing import Any, cast, Concatenate, Literal, NamedTuple, \
    overload, ParamSpec, Self, SupportsIndex, TypeVar

# Import third-party PyPI libraries
import bs4
import pathvalidate

# Import local custom libraries
try:
    from gconanpy.iters import exhaust_wrapper
    from gconanpy.iters.filters import MapSubset
    from gconanpy.meta import bool_pair_to_cases, cached_property, \
        MethodWrappingMeta, name_of, TimeSpec, tuplify
    from gconanpy.meta.typeshed import NonTxtCollection
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from iters import exhaust_wrapper
    from iters.filters import MapSubset
    from meta import bool_pair_to_cases, cached_property, \
        MethodWrappingMeta, name_of, TimeSpec, tuplify
    from meta.typeshed import NonTxtCollection

# Type variables
_P = ParamSpec("_P")


class ToString(str, metaclass=MethodWrappingMeta):
    # Metaclass wraps every str method that returns str
    # to return a ToString instance instead.

    # Filter to call fromIterable in quotate method using the recursive
    # iter_kwargs input parameter without adding a parameter exclusive to
    # fromMapping method (and not fromIterable)
    _ITER_SUBSET = MapSubset(keys_arent="join_on")

    def __add__(self, value: str | None) -> Self:
        """ Append `value` to the end of `self`. Implements `self + value`. \
            Defined explicitly so that `ToString() + str() -> ToString` \
            instead of returning a `str` object.

        :param value: str | None
        :return: ToString, `self` with `value` appended after it; \
            `if not value`, then `return self` unchanged.
        """
        return self if value is None else type(self)(super().__add__(value))

    def __sub__(self, value: str | None) -> Self:
        """ Remove `value` from the end of `self`. Implements `self - value`.
            Defined as a shorter but still intuitive alias for `removesuffix`.

        :param value: str | None
        :return: ToString, `self` without `value` at the end; if `self` \
            doesn't end with `value` or `if not value`, then \
            `return self` unchanged.
        """
        return self if value is None else cast(Self, self.removesuffix(value))

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
            if len(self) else self.that_starts_with(prefix) + suffix

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
        :param format: Mapping[str, Any], `fromIterable` parameters; include \
            these to format the elements while joining them.
        :return: Self, `iterable` converted `ToString`.
        """
        cls = type(self)
        if format:
            stringified = cls.fromIterable([cls.fromAny(el, **format)
                                           for el in iterable])
        else:
            stringified = cls(self.join(cls(el) for el in iterable))
        return stringified

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
        """ Convert an object `ToString`.

        :param an_obj: Any, object to convert `ToString`
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
            different strings to replace them with; by default, will replace
            ":" with "-" to name files.
        :param encoding: str,_description_, defaults to
            `sys.getdefaultencoding()`
        :param errors: str, _description_, defaults to "ignore"
        :param lastly: str to insert after the last `sep` in the returned \
            ToString object `if len(an_obj) > 2`, or None to add no such \
            string; defaults to "and "
        :return: ToString of `an_obj` formatted as specified.
        """
        # If the max_len is too low for anything besides the affixes, then
        # return just the affixes if they fit, else return an empty ToString
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
        """ Convert a `BeautifulSoup` object (from `bs4`) to a `ToString`.

        :param soup: bs4.element.PageElement, or None to get an empty string.
        :param tag: Literal["all", "first", "last"], which HTML document tag \
            to represent as a string: "first" means only the opening tag, \
            "last" means only the closing tag, and "all" means both plus \
            everything in between them.
        :return: ToString representing the `BeautifulSoup` object.
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
        """ Convert a `Callable` object, such as a function or class, into a \
            `ToString` instance.

        :param an_obj: Callable to stringify.
        :param max_len: int, size of the longest possible ToString to return \
            without truncation, or None to never truncate; defaults to None.
        :param args: Iterable[Any], input parameters to represent calling \
            `an_obj` with. `args=[1,2,3]` -> `"an_obj(1, 2, 3)"`.
        :param kwargs: Mapping[str, Any], keyword input parameters to \
            represent calling `an_obj` with. `kwargs={"a": 1, "b": 2}` -> \
            `"an_obj(a=1, b=2)"`.
        :return: ToString representing the `Callable` object `an_obj`.
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
        return cls(stringified).replace_all(replace)

    @classmethod
    def fromIterable(cls, an_obj: Collection, quote: str | None = "'",
                     sep: str = ", ", quote_numbers: bool = False,
                     prefix: str | None = "[", suffix: str | None = "]",
                     max_len: int | None = None, lastly: str = "and ",
                     iter_kwargs: Mapping[str, Any] = {}) -> Self:
        """ Convert a Collection (e.g. a list, tuple, or set) into an \
            instance of the `ToString` class.

        :param an_obj: Collection to convert `ToString`
        :param quote: str to add before and after each element of `an_obj`, \
            or None to insert no quotes; defaults to "'"
        :param sep: str to insert between all of the elements of `an_obj`, \
            or None to insert no such separators; defaults to ", "
        :param quote_numbers: bool, True to insert `quote` before and after \
            each numerical element of `an_obj`; else False to add no \
            quotes to numbers in `an_obj`; defaults to False
        :param prefix: str to insert as the first character of the returned \
            `ToString` object, or None to add no prefix; defaults to "["
        :param suffix: str to insert as the last character of the returned \
            `ToString` object, or None to add no suffix; defaults to "]"
        :param max_len: int, size of the longest possible ToString to return \
            without truncation, or None to never truncate; defaults to None
        :param lastly: str to insert after the last `sep` in the returned \
            `ToString` object `if len(an_obj) > 2`, or None to add no such \
            string; defaults to "and "
        :param iter_kwargs: Mapping[str, Any], keyword input parameters to \
            pass to `quotate` for each element of `an_obj`; defaults to \
            an empty `dict`.
        :return: ToString of all elements in `an_obj`, `quote`-quoted and \
                 `sep`-separated if there are multiple elements, starting \
                 with `prefix` and ending with `suffix`, with `lastly` after \
                 the last `sep` if there are more than 2 elements of `an_obj`.
        """
        if not an_obj:
            string = ""
        elif isinstance(an_obj, str):  # TODO Refactor from LBYL to EAFP?
            string = an_obj
        else:
            list_with_str_els = cls.quotate_all(an_obj, quote, quote_numbers,
                                                max_len, iter_kwargs)
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
    def fromMapping(cls, a_map: Mapping, quote: str | None = "'",
                    quote_numbers: bool = False, quote_keys: bool = True,
                    join_on: str = ": ",
                    prefix: str | None = "{", suffix: str | None = "}",
                    sep: str = ", ", max_len: int | None = None,
                    lastly: str = "and ",
                    iter_kwargs: Mapping[str, Any] = {}) -> Self:
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
        :param iter_kwargs: Mapping[str, Any], keyword input parameters to \
            pass to `quotate` for each key-value pair in `a_map`; defaults to \
            an empty `dict`.
        :return: ToString, _description_
        """
        join_on = cls(join_on)
        pair_strings = list()
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

    @classmethod
    def quotate(cls, an_obj: Any, quote: str | None = "'",
                quote_numbers: bool = False, quote_keys: bool = False,
                **iter_kwargs: Any) -> Self:
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
                    # without_join = cls._ITER_SUBSET.of(iter_kwargs)
                    quoted = cls.fromIterable(
                        an_obj,  # type: ignore  # TODO FIX NonTxtCollection
                        quote, quote_numbers=quote_numbers,
                        # iter_kwargs=iter_kwargs,
                        **cls._ITER_SUBSET.of(iter_kwargs))
                case int() | float():
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
                    kwargs: Mapping[str, Any] = {}) -> list[Self]:
        return [cls.quotate(an_obj, quote, quote_numbers, max_len=max_len,
                            **kwargs) for an_obj in objects]

    def replace_all(self, replacements: Mapping[str, str], count: int = -1,
                    reverse: bool = False) -> Self:
        """ Repeatedly run the `replace` (or `rreplace`) method.

        :param replacements: Mapping[str, str] of (old) substrings to their \
            (new) respective replacement substrings.
        :param count: int, the maximum number of occurrences of each \
            substring to replace. Defaults to -1 (replace all occurrences).
        :param reverse: bool, True to replace the last `count` substrings, \
            starting from the end; else (by default) False to replace the \
            first `count` substrings, starting from the string's beginning.
        :return: ToString after replacing `count` key-substrings with their \
            corresponding value-substrings in `replace`.
        """
        string = self  # cls = type(self)
        replace = ToString.rreplace if reverse else ToString.replace
        for old, new in replacements.items():
            string = replace(cast(Self, string), old, new, count)
        return cast(Self, string)

    def rreplace(self, old: str, new: str, count: SupportsIndex = -1) -> Self:
        """ Return a copy with occurrences of substring old replaced by new.
            Like `str.replace`, but replaces the last `old` occurrences first.

        :param old: str, the substring to replace occurrences of with `new`.
        :param new: str to replace `count` occurrences of `old` with.
        :param count: SupportsIndex, the maximum number of occurrences to \
            replace. Defaults to -1 (replace all occurrences). Include a \
            different number to replace only the LAST `count` occurrences, \
            starting from the end of the string.
        :return: ToString, a copy with its last `count` instances of the \
            `old` substring replaced by a `new` substring.
        """
        return type(self)(new.join(self.rsplit(old, count)))

    def rtruncate(self, max_len: int | None = None, prefix: str = "..."
                  ) -> Self:
        return self if max_len is None or len(self) <= max_len else \
            type(self)(prefix + self[max_len - len(prefix):])

    def that_ends_with(self, suffix: str | None) -> Self:
        """ Append `suffix` to the end of `self` unless it is already there.

        :param suffix: str to append to `self`, or None to do nothing.
        :return: ToString ending with `suffix`.
        """
        return self if not suffix or self.endswith(suffix) else self + suffix

    def that_starts_with(self, prefix: str | None) -> Self:
        """ Prepend `suffix` at index 0 of `self` unless it is already there.

        :param prefix: str to prepend to `self`, or None to do nothing.
        :return: ToString beginning with `prefix`.
        """
        return self if not prefix or self.startswith(prefix) else \
            type(self)(prefix) + self

    def truncate(self, max_len: int | None = None, suffix: str = "..."
                 ) -> Self:
        return self if max_len is None or len(self) <= max_len else \
            type(self)(self[:max_len - len(suffix)] + suffix)

    @cached_property[int]
    def width(self) -> int:
        """ :return: int, this string's maximum line width. """
        return max(len(each_line) for each_line in self.split("\n"))


# Shorter names to export
stringify = ToString.fromAny
stringify_dt = ToString.fromDateTime
stringify_map = ToString.fromMapping
stringify_iter = ToString.fromIterable


class Branches(NamedTuple):
    """ A defined tuple of symbols to visually represent a branching \
        hierarchical tree structure, like a filesystem directory or a \
        document written in a markup language (e.g. HTML, XML, markdown, \
        etc). All symbols should have the same length.

    `I` (vertical line) connects the top to the bottom.
    `L` (end branch) connects the top to the right.
    `T` (split branch) connects the top to the bottom and the right.
    `O` (empty) represents a blank indentation character.
    """
    I: str = "│"
    L: str = "└"
    T: str = "├"
    O: str = " "


class BasicTree(tuple[str, list["BasicTree"]]):
    full: str | tuple[str, str]
    BRANCH = Branches()

    def prettify(self, prefix: ToString = ToString(),
                 branch: Branches = BRANCH) -> ToString:
        pretties = [prefix + self[0]]

        if prefix.endswith(branch.L):
            prefix = cast(ToString, prefix.rreplace(
                branch.L, branch.O, count=1).replace(branch.T, branch.I))

        if self[1]:
            for child in self[1][:-1]:
                pretties.append(child.prettify(prefix + branch.T, branch))
            pretties.append(self[1][-1].prettify(
                cast(ToString, prefix.replace(branch.T, branch.I)
                     ) + branch.L, branch))

        return cast(ToString, ToString("\n").join(pretties))

    def prettify_spaces(self, indents_from_left: int = 0,
                        indent: str = "  ") -> str:
        children = [child.prettify_spaces(indents_from_left + 1,
                                          indent) for child in self[1]]
        pretty = f"{indent * indents_from_left}{self[0]}"
        if children:
            pretty += "\n" + "\n".join(children)
        return pretty

    def walk(self, depth_first: bool = True,
             include_self: bool = True) -> Generator[Self, None, None]:
        if include_self:
            yield self
        if not depth_first:
            for child in self[1]:
                yield cast(Self, child)
        for child in self[1]:
            yield from cast(Self, child).walk(depth_first, depth_first)


class SoupTree(BasicTree):
    full: str | tuple[str, str]

    # def toHTML(self) -> str:  # TODO

    @classmethod
    def from_soup(cls, page_el: bs4.element.PageElement) -> Self:
        ret: tuple[str, list]
        match page_el:
            case bs4.Tag():
                ret = (page_el.name,
                       [cls.from_soup(child) for child in page_el.children])
            case bs4.element.NavigableString():
                ret = ("str", list())
            case _:
                ret = ("", list())
        self = cls(ret)
        self.full = (ToString.fromBeautifulSoup(page_el, "first"),
                     ToString.fromBeautifulSoup(page_el, "last"))
        return self


class WrapFunction:  # WrapFunction(partial):
    """ Function wrapper that also stores some of its input parameters.
        `functools.partial` modified to prepend and/or append parameters. """
    # Instance variables for (g/s)etstate: [func, pre, post, keywords]
    _VarsTypes = tuple[Callable, tuple, tuple, dict | None]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :param args: Iterable[Any], positional input arguments
        :param kwargs: Mapping[str, Any], keyword input arguments
        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input arguments
        """
        return self.func(*self.pre, *args, *self.post,
                         **self.keywords, **kwargs)

    def __init__(self, func: Callable, pre: Any = (),
                 post: Any = (), **keywords: Any) -> None:
        """ Wrap/"freeze" a function with some parameters already defined \
            to call that function with those parameters later.

        Same as `functools.partial`, but `WrapFunction` lets you define \
        positional arguments to pass to the wrapped function before *and* \
        after the positional arguments passed at execution.

        :param func: Callable[[*pre, ..., *post], Any], the function to \
            wrap/"freeze" and then call/execute/"thaw" later.
        :param pre: Iterable of positional arguments to inject BEFORE the \
            `func` function's other positional input parameters; or the \
            first positional argument to `func` (a string or a non-iterable).
        :param post: Iterable of positional arguments to inject AFTER the \
            `func` function's other positional input parameters; or the \
            last positional argument to `func` (a string or a non-iterable).
        :param keywords: Mapping[str, Any] of keyword arguments to call the \
            wrapped/"frozen" `func` function with.
        """
        if not callable(func):
            raise TypeError("the first argument must be callable")

        self.func = func
        self.keywords = keywords
        self.pre = tuplify(pre)
        self.post = tuplify(post)

    def __reduce__(self) -> tuple[type[Self], tuple[Callable], _VarsTypes]:
        return type(self), (self.func, ), (self.func, self.pre, self.post,
                                           self.keywords or None)

    def __repr__(self) -> str:
        """
        :return: str, annotated function header describing this WrapFunction.
        """
        return self.stringified

    def __setstate__(self, state: _VarsTypes) -> None:
        self.func, self.pre, self.post, keywords = state
        self.keywords = keywords if keywords else {}

    def expect(self, output: Any) -> Self:
        """ 
        :param output: Any, expected output returned from inner \
            wrapped/"frozen" function.
        :return: WrapFunction[..., bool] that returns True if the inner \
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.func(*args, **kwargs) == output
        return type(self)(is_as_expected)

    def foreach(self, *objects: Any, **kwargs: Any
                ) -> Generator[Any, None, None]:
        """ Call the wrapped/"frozen" function with its specified parameters \
            on every object in `objects`. Iterate lazily; only call/execute \
            the wrapped function on each object at the moment of retrieval.

        :param objects: Iterable[Any], each positional input argument to \
            call this `WrapFunction` on once
        :param kwargs: Mapping[str, Any], keyword arguments to call this \
            `WrapFunction` with on every object in `objects`
        :yield: Generator[Any, None, None], what the wrapped/"frozen" \
            function returns when given each object in `objects` as an input.
        """
        for an_obj in objects:
            yield self.func(an_obj, **kwargs)

    @cached_property[ToString]
    def stringified(self) -> ToString:
        """
        :return: ToString, representation of this `WrapFunction` instance 
            including all of its pre-defined positional and keyword arguments.
        """
        return ToString.fromCallable(type(self), **vars(self))


# @ClassWrapper(tuple).class_decorator  # TODO?
class Sets[T: Hashable](tuple[set[T], ...]):
    """ Wrapper class to centralize methods comparing/using multiple sets. """
    _R = TypeVar("_R")  # for _zip_sets method

    are_same = all_equal  # Check whether sets have the same elements

    def __add__(self, others: Iterable[set[T]]) -> Self:
        """ Concatenates `others` to these `Sets`.

        Returns `self + value`. Defined to return a `Sets` instance. 

        :param others: Iterable[set[T], ...], other sets to append to this \
            `Sets` tuple
        :return: Self, a `Sets` instance with `others` concatenated to the end
        """
        return type(self)(super().__add__(tuple(others)))

    @overload
    def __getitem__(self, key: SupportsIndex, /) -> set[T]: ...
    @overload
    def __getitem__(self, key: slice, /) -> Self: ...

    def __getitem__(self, key):
        """ Returns `self[key]`. Defined so slicing returns a `Sets` instance.

        :return: slice | set[T], `self[key]`
        """
        gotten = super().__getitem__(key)
        if isinstance(key, slice):  # if isinstance(gotten, tuple):
            gotten = type(self)(gotten)
        return gotten

    def __new__(cls, iterables: Iterable[Iterable[T]] = ()) -> Self:
        """ 
        :param iterables: Iterable[Iterable[T]] to convert into `Sets`
        :return: Self, a tuple of all input `iterables` as `Sets`
        """
        return super().__new__(cls, (set(x) for x in iterables))

    @staticmethod
    def _reduce_set_method(func: Callable[[set[T], Iterable[T]], set[T]]
                           ) -> Callable[..., set[T]]:
        @wraps(func)
        def inner(self) -> set[T]:
            return reduce(func, self) if self else set()

        # Copy the original method's docstring, but update it for Sets class
        doc = getattr(func, "__doc__", None)
        if doc is not None:
            inner.__doc__ = ToString.fromAny(doc).replace_all({
                "two sets": "all `Sets`", "both sets": "all `Sets`"})
        return inner

    @staticmethod
    def _zip_sets(func: Callable[Concatenate[set[T], Iterable[T], _P], _R]
                  ):  # -> Callable[[Self, Sequence[set[T]]], Generator[_R,

        def inner(self: Self, others: Sequence[set[T]], *args,  # : _P.args,
                  **kwargs):  # : _P.kwargs) -> Generator[_R, None, None]:
            """ Element-wise `set` operation.

            :param others: Sequence[set[T]], _description_
            """
            for i in range(min(len(self), len(others))):
                yield func(self[i], others[i], *args, **kwargs)
        return inner

    # Aliases for methods reducing all contained Sets to one output set
    combine = merge = union = _reduce_set_method(set.union)
    intersection = overlap = _reduce_set_method(set.intersection)
    unique = uniques = _reduce_set_method(set.symmetric_difference)

    concat = extend = __add__  # More synonymous method aliases

    # Operations to perform on each set in these Sets and the corresponding
    # set in a different Sequence of sets
    union_each = _zip_sets(set.union)
    update_each = exhaust_wrapper(_zip_sets(set.update))

    def append(self, *others: set[T]) -> Self:
        """ Appends `others` to these `Sets`. Same as `concat`, but accepts \
            an individual `set` instance as an argument.

        :param others: Iterable[set[T], ...], other sets to append to this \
            `Sets` tuple
        :return: Self, a `Sets` instance with `others` concatenated to the end
        """
        return self + others

    def apply(self, func: Callable[Concatenate[set[T], _P], _R],
              *args: _P.args, **kwargs: _P.kwargs
              ) -> Generator[_R, None, None]:
        return (func(s, *args, **kwargs) for s in self)

    def differentiate(self) -> Generator[set[T], None, None]:
        """ Return a copy of the sets without any shared elements. Each will \
            only have its unique items, so they do no overlap/intersect.

        :return: Generator[set[T], None, None], each set with only its \
            unique items
        """
        return (self[i].difference((self[:i] + self[i+1:]).union()
                                   ) for i in range(len(self)))

    def filter(self, func: Callable[[T], Any]
               ) -> Generator[filter, None, None]:
        return (filter(func, s) for s in self)


class Valid:
    """ Tools to validate command-line input arguments. """
    # Type hints for _validate method
    _F = TypeVar("_F")  # Reformatted validated input object
    _T = TypeVar("_T")  # Input object to validate

    # Predefined validator functions (with default parameter values)
    dir_made = WrapFunction(os.makedirs, exist_ok=True)  # Dir exists
    readable = WrapFunction(os.access, mode=os.R_OK)  # Can read existing obj
    writable = WrapFunction(os.access, mode=os.W_OK)  # Can write existing obj

    @overload
    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  err_msg: str,
                  first_ensure: Callable[[_T], Any] | None = None,
                  final_format: Callable[[_T], _F]) -> _F: ...

    @overload
    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  err_msg: str,
                  first_ensure: Callable[[_T], Any] | None = None) -> _T: ...

    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  # conditions: Iterable[Callable] = list(),
                  err_msg: str = "`{}` is invalid.",
                  first_ensure: Callable[[_T], Any] | None = None,
                  final_format: Callable[[_T], _F] | None = None):
        """ Parent/base function used by different type validation functions.

        :param to_validate: _T: Any, object to validate
        :param conditions: Iterable[Callable[[_T], bool]] that each accept \
            `to_validate` and returns True if and only if `to_validate` \
            passes some specific condition, otherwise returning False
        :param final_format: Callable[[_T], _F: Any] that accepts \
            `to_validate` and returns it after fully validating it
        :param err_msg: str to show to user to tell them what is invalid
        :param first_ensure: Callable[[_T], Any] to run on `to_validate` to \
            prepare/ready it for validation
        :raise: argparse.ArgumentTypeError if `to_validate` is somehow invalid
        :return: _T | _F, `to_validate` but fully validated
        """
        try:
            if first_ensure:
                first_ensure(to_validate)
            '''
            for prepare in first_ensure:
                prepare(to_validate)
            '''
            for is_valid in conditions:
                assert is_valid(to_validate)
            return final_format(to_validate) if final_format else to_validate
        except (argparse.ArgumentTypeError, AssertionError, OSError,
                TypeError, ValueError):
            raise argparse.ArgumentTypeError(err_msg.format(to_validate))

    @classmethod
    def output_dir(cls, path: Any) -> str:
        """ Try to make or access a directory for new files at `path`.

        :param path: str, valid (not necessarily real) directory path
        :raise: argparse.ArgumentTypeError if directory path is not writable
        :return: str, validated absolute path to real writable folder
        """
        return cls._validate(path, os.path.isdir, cls.writable,
                             err_msg="Cannot create directory at `{}`",
                             first_ensure=cls.dir_made,  # [cls.dir_made],
                             final_format=os.path.abspath)

    @classmethod
    def readable_dir(cls, path: Any) -> str:
        """ Verify that `path` is a valid directory path.

        :param path: Any, object that should be a valid directory path
        :return: str representing a valid directory path
        """
        return cls._validate(path, os.path.isdir, cls.readable,
                             err_msg="Cannot read directory at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def readable_file(cls, path: Any) -> str:
        """ Use this instead of `argparse.FileType('r')` because the latter \
            leaves an open file handle.

        :param path: Any, object that should be a valid file (or dir) path.
        :raise: argparse.ArgumentTypeError if `path` isn't a path to a valid \
            readable file (or directory).
        :return: str representing a valid file (or directory) path.
        """
        return cls._validate(path, cls.readable,
                             err_msg="Cannot read file at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def whole_number(cls, to_validate: Any) -> int:
        """ Throw argparse exception unless to_validate is a positive integer

        :param to_validate: Any, obj to test whether it is a positive integer
        :return: int, to_validate if it is a positive integer
        """
        return cls._validate(to_validate, lambda x: int(x) >= 0,
                             err_msg="{} is not a positive integer",
                             final_format=int)


class ArgParser(argparse.ArgumentParser):
    """ Extends `argparse.ArgumentParser` to include default values that I \
        tend to re-use. Purely for convenience. """

    def add_new_out_dir_arg(self, name: str, **kwargs: Any) -> None:
        """ Specifies argparse.ArgumentParser.add_argument for a valid path \
            to an output directory that must either exist or be created.

        :param name: str naming the directory to access (and create if needed)
        :param kwargs: Mapping[str, Any], keyword arguments for the method \
            `argparse.ArgumentParser.add_argument`
        """
        if not kwargs.get("default"):
            kwargs["default"] = os.path.join(os.getcwd(), name)
        if not kwargs.get("dest"):
            kwargs["dest"] = name
        if not kwargs.get("help"):
            kwargs["help"] = "Valid path to local directory to save " \
                f"{name} files into. If no directory exists at this path " \
                "yet, then one will be created. By default, this script " \
                "will save output files into a directory at this path: " \
                + kwargs["default"]
        self.add_argument(
            f"-{name[0]}", f"-{name}", f"--{name}", f"--{name}-dir",
            f"--{name}-dir-path", type=Valid.output_dir, **kwargs
        )
