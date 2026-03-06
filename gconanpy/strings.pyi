#!/usr/bin/env python3

"""
This file forces static type checkers to acknowledge that `FancyString` methods
never return `str` and only return `FancyString`, even inherited `str` methods.
Greg Conan: gregmconan@gmail.com
Created: 2025-11-19
Updated: 2026-03-05
"""
# Import standard libraries
from builtins import _FormatMapMapping, _TranslateTable
from collections.abc import Callable, Collection, Iterable, Mapping
import datetime as dt
import sys
from typing import Any, Literal, Self, SupportsIndex

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
try:
    from gconanpy.meta import cached_property, MethodWrappingMeta, TimeSpec
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from .meta import cached_property, MethodWrappingMeta, TimeSpec

# Different kinds of text cases
StrCase = Literal["camel", "capitalize", "kebab", "lower", "macro",
                  "pascal", "snake", "title", "upper"]


class FancyString(str, metaclass=MethodWrappingMeta):

    def __add__(self, value: str | None) -> Self: ...
    def __sub__(self, value: str | None) -> Self: ...
    def capitalize(self) -> Self: ...
    def casefold(self) -> Self: ...
    def center(self, width: SupportsIndex, fillchar: str = " ", /) -> Self: ...
    def enclosed_by(self, affix: str) -> Self: ...
    def enclosed_in(self, prefix: str | None, suffix: str | None) -> Self: ...
    def expandtabs(self, tabsize: SupportsIndex) -> Self: ...

    @classmethod
    def filepath(cls, dir_path: str, file_name: str, file_ext: str = "",
                 put_date_after: str | None = None, max_len: int | None = None
                 ) -> Self: ...

    def force_join(self, iterable: Iterable, **format: Any) -> Self: ...
    def format(self, *args: object, **kwargs: object) -> Self: ...
    def format_map(self, mapping: _FormatMapMapping, /) -> Self: ...

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
                iter_kwargs: dict[str, Any] = {}) -> Self: ...

    @classmethod
    def fromBeautifulSoup(cls, soup: bs4.element.PageElement | None, tag:
                          Literal["all", "first", "last"] = "all") -> Self: ...

    @classmethod
    def fromCallable(cls, an_obj: Callable, max_len: int | None = None,
                     *args: Any, **kwargs: Any) -> Self: ...

    @classmethod
    def fromDateTime(cls, moment: dt.date | dt.time | dt.datetime,
                     sep: str = "_", timespec: TimeSpec.UNIT = "seconds",
                     replace: Mapping[str, str] = {":": "-"}) -> Self: ...

    @classmethod
    def fromIterable(cls, an_obj: Collection, quote: str | None = "'",
                     sep: str = ", ", quote_numbers: bool = False,
                     prefix: str | None = "[", suffix: str | None = "]",
                     max_len: int | None = None, lastly: str = "and ",
                     iter_kwargs: Mapping[str, Any] = {}) -> Self: ...

    @classmethod
    def fromMapping(cls, a_map: Mapping, quote: str | None = "'",
                    quote_numbers: bool = False, quote_keys: bool = True,
                    join_on: str = ": ",
                    prefix: str | None = "{", suffix: str | None = "}",
                    sep: str = ", ", max_len: int | None = None,
                    lastly: str = "and ",
                    iter_kwargs: Mapping[str, Any] = {}) -> Self: ...

    def is_case(self, str_case: StrCase) -> bool: ...
    def join(self, iterable: Iterable[str], /) -> Self: ...
    def ljust(self, width: SupportsIndex, fillchar: str = " ", /) -> Self: ...
    def lower(self) -> Self: ...
    def lstrip(self, chars: str | None = None, /) -> Self: ...

    @classmethod
    def quotate(cls, an_obj: Any, quote: str | None = "'",
                quote_numbers: bool = False, quote_keys: bool = False,
                **iter_kwargs: Any) -> Self: ...

    @classmethod
    def quotate_all(cls, objects: Iterable, quote: str | None = "'",
                    quote_numbers: bool = False, max_len: int | None = None,
                    kwargs: Mapping[str, Any] = {}) -> list[Self]: ...

    def removeprefix(self, prefix: str, /) -> Self: ...
    def removesuffix(self, suffix: str, /) -> Self: ...

    def replace(self, old: str, new: str, count: SupportsIndex = -1, /
                ) -> Self: ...

    def replace_all(self, replacements: Mapping[str, str], count: int = -1,
                    reverse: bool = False) -> Self: ...

    def rjust(self, width: SupportsIndex, fillchar: str = " ", /) -> Self: ...

    def rreplace(self, old: str, new: str, count: SupportsIndex = -1
                 ) -> Self: ...

    def rstrip(self, chars: str | None = None, /) -> Self: ...

    def rtruncate(self, max_len: int | None = None, prefix: str = "..."
                  ) -> Self: ...

    def strip(self, chars: str | None = None, /) -> Self: ...
    def swapcase(self) -> Self: ...
    def that_ends_with(self, suffix: str | None) -> Self: ...
    def that_starts_with(self, prefix: str | None) -> Self: ...
    def title(self) -> Self: ...
    def to_case(self, str_case: StrCase, sep: str | None = None) -> Self: ...
    def translate(self, table: _TranslateTable, /) -> str: ...
    def truncate(self, max_len: int | None = None, suffix: str = "..."
                 ) -> Self: ...

    def upper(self) -> Self: ...

    @cached_property[int]
    def width(self) -> int: ...
    def zfill(self, width: SupportsIndex, /) -> Self: ...


# Shorter names to export
stringify = FancyString.fromAny
stringify_dt = FancyString.fromDateTime
stringify_map = FancyString.fromMapping
stringify_iter = FancyString.fromIterable
