#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2025-07-15
"""
# Import standard libraries
# from collections import UserString  # TODO?
from collections.abc import Callable, Collection, Generator, Iterable, Mapping
import datetime as dt
import os
import re
import sys
from typing import Any, Literal, NamedTuple
from typing_extensions import Self

# Import third-party PyPI libraries
import bs4
import pathvalidate

# Import local custom libraries
try:
    import mapping
    from meta.classes import ClassWrapper, TimeSpec
    from meta.funcs import bool_pair_to_cases, name_of
    from reg import Regextract
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy import mapping
    from gconanpy.meta.classes import ClassWrapper, TimeSpec
    from gconanpy.meta.funcs import bool_pair_to_cases, name_of
    from gconanpy.reg import Regextract


# Wrap every str method that returns str to return a ToString instance instead
wrapper = ClassWrapper(str)


@wrapper.class_decorator
class ToString(str):
    # Filter to call fromIterable in quotate method using the recursive
    # iter_kwargs input parameter without adding a parameter exclusive to
    # fromMapping method (and not fromIterable)
    _ITER_SUBSET = mapping.Subset(keys="join_on", include_keys=False)

    # Type hint for passing own methods to others as input parameters
    Stringifier = Callable[[Any], Self]

    # TODO Wrap string methods so type checker shows they return a ToString?
    # TODO No, just hint them properly in a .pyi Python stub file?

    def __add__(self, value: str | None) -> Self:
        """ Append `value` to the end of `self`. Implements `self + value`. \
            Defined explicitly so that `ToString() + str() -> ToString` \
            instead of returning a `str` object.

        :param value: str | None
        :return: ToString, `self` with `value` appended after it; \
            `if not value`, then `return self` unchanged.
        """
        return self.__class__(super().__add__(value)) if value else self

    @wrapper.return_as_its_class  # method returns ToString
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
                iter_kwargs: dict[str, Any] = dict()) -> Self:
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
            case dict():
                stringified = cls.fromMapping(
                    an_obj, quote, quote_numbers, quote_keys, join_on, prefix,
                    suffix, sep, max_len, lastly, iter_kwargs)
            case list() | tuple() | set():
                stringified = cls.fromIterable(
                    an_obj, quote, sep, quote_numbers, prefix, suffix,
                    max_len, lastly, iter_kwargs)
            case dt.date() | dt.time() | dt.datetime():
                stringified = cls.fromDateTime(
                    an_obj, dt_sep, timespec, replace).truncate(max_len)
            case type():
                stringified = cls.fromCallable(an_obj, max_len)
            case None:
                stringified = cls()
            case bs4.element.PageElement():
                stringified = cls.fromBeautifulSoup(an_obj)
            case _:  # str or other
                stringified = cls(an_obj)
                if Regextract.is_invalid_py_repr(stringified):
                    stringified = cls.fromCallable(an_obj, max_len)
                stringified = stringified.truncate(max_len)
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
        iter_kwargs: Mapping = dict(prefix="[", suffix="]", lastly="")
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
                     iter_kwargs: Mapping[str, Any] = dict()) -> Self:
        """ Convert a Collection (e.g. a list, tuple, or set) into an \
            instance of the ToString class.

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
                    iter_kwargs: Mapping[str, Any] = dict()) -> Self:
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
        # quotate = cls.get_quotator(quote, quote_numbers, list_kwargs)
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
                case dict():
                    quoted = cls.fromMapping(an_obj, quote, quote_numbers,
                                             quote_keys, **iter_kwargs)
                    # , iter_kwargs=iter_kwargs)
                case list() | tuple() | set():
                    # without_join = cls._ITER_SUBSET.of(iter_kwargs)
                    quoted = cls.fromIterable(
                        an_obj, quote, quote_numbers=quote_numbers,
                        # iter_kwargs=iter_kwargs,
                        **cls._ITER_SUBSET.of(iter_kwargs))
                case int() | float():
                    quoted = cls(an_obj).enclosed_by(quote) \
                        if quote_numbers else cls(an_obj)
                case None:
                    quoted = cls().enclosed_by(quote)
                case _:
                    quoted = cls(an_obj)
                    if Regextract.is_invalid_py_repr(quoted):
                        quoted = cls.fromCallable(an_obj)
                    else:
                        quoted = quoted.enclosed_by(quote)
        return quoted

    @classmethod
    def quotate_all(cls, objects: Iterable, quote: str | None = "'",
                    quote_numbers: bool = False, max_len: int | None = None,
                    kwargs: Mapping[str, Any] = dict()) -> list[Self]:
        return [cls.quotate(an_obj, quote, quote_numbers, max_len=max_len,
                            **kwargs) for an_obj in objects]

    @wrapper.return_as_its_class  # method returns ToString
    def replace_all(self, replacements: Mapping[str, str], count: int = -1,
                    reverse: bool = False) -> str:
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
        string = self  # cls = self.__class__
        replace: Callable[[ToString, str, str, int], ToString] = \
            ToString.rreplace if reverse else \
            ToString.replace  # type: ignore[no-redef]  # TODO
        for old, new in replacements.items():
            string = replace(string, old, new, count)
        return string

    @wrapper.return_as_its_class  # method returns ToString
    def rreplace(self, old: str, new: str, count: int = -1) -> Self:
        """ Return a copy with occurrences of substring old replaced by new.
            Like `str.replace`, but replaces the last `old` occurrences first.

        :param old: str, the substring to replace occurrences of with `new`.
        :param new: str to replace `count` occurrences of `old` with.
        :param count: int, the maximum number of occurrences to replace. \
            Defaults to -1 (replace all occurrences). Include a different \
            number to replace only the LAST `count` occurrences, starting \
            from the end of the string.
        :return: ToString, a copy with its last `count` instances of the \
            `old` substring replaced by a `new` substring.
        """
        return new.join(self.rsplit(old, count))  # type: ignore[no-redef]  # TODO

    def that_ends_with(self, suffix: str | None) -> Self:
        """ Append `suffix` to the end of `self` unless it is already there.

        :param suffix: str to append to `self`, or None to do nothing.
        :return: ToString ending with `suffix`.
        """
        return self if not suffix or self.endswith(suffix) else self + suffix

    @wrapper.return_as_its_class  # method returns ToString
    def that_starts_with(self, prefix: str | None) -> str:
        """ Prepend `suffix` at index 0 of `self` unless it is already there.

        :param prefix: str to prepend to `self`, or None to do nothing.
        :return: ToString beginning with `prefix`.
        """
        return self if not prefix or self.startswith(prefix) else prefix + self

    def truncate(self, max_len: int | None = None, suffix: str = "..."
                 ) -> Self:
        # TODO Use independent truncate() function here again (DRY)?
        return self if max_len is None or len(self) <= max_len else \
            self.__class__(self[:max_len - len(suffix)] + suffix)


class Branches(NamedTuple):
    """ A defined tuple of symbols to visually represent a branching \
        hierarchical tree structure, like a filesystem directory or a \
        document written in a markup language (e.g. HTML, XML, markdown, \
        etc). All symbols should have the same length.

    `I` (vertical line) connects the top to the bottom.
    `L` (end branch) connects the top to the right.
    `T` (split branch) connects the top to the bottom and the right.
    `X` (empty) represents a blank indentation character.
    """
    I: str = "│"
    L: str = "└"
    T: str = "├"
    X: str = " "


class BasicTree(tuple[str, list]):
    full: str | tuple[str, str]
    BRANCH = Branches()

    def prettify(self, prefix: ToString = ToString(),
                 branch: Branches = BRANCH) -> str:
        pretties = [prefix + self[0]]

        if prefix.endswith(branch.L):
            prefix = prefix.rreplace(branch.L, branch.X, count=1
                                     ).replace(branch.T, branch.I)

        if self[1]:
            for child in self[1][:-1]:
                pretties.append(child.prettify(prefix + branch.T, branch))
            pretties.append(self[1][-1].prettify(
                prefix.replace(branch.T, branch.I) + branch.L, branch))

        return "\n".join(pretties)

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
                yield child
        for child in self[1]:
            yield from child.walk(depth_first, depth_first)


# Shorter names to export
stringify = ToString.fromAny
stringify_dt = ToString.fromDateTime
stringify_map = ToString.fromMapping
stringify_iter = ToString.fromIterable
