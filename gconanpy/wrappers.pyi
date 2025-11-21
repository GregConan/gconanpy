#!/usr/bin/env python3

"""
This file forces static type checkers to acknowledge that `ToString` methods
never return `str` and only return `ToString`, even inherited methods.
Greg Conan: gregmconan@gmail.com
Created: 2025-11-19
Updated: 2025-11-19
"""
# Import standard libraries
import argparse
from collections.abc import Callable, Collection, Generator, \
    Hashable, Iterable, Mapping
import datetime as dt
import sys
from typing import Any, Concatenate, Literal, NamedTuple, \
    overload, ParamSpec, Protocol, Self, SupportsIndex, TypeVar

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
try:
    from gconanpy.iters import exhaust_wrapper
    from gconanpy.meta import MethodWrappingMeta, TimeSpec
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from iters import exhaust_wrapper
    from meta import MethodWrappingMeta, TimeSpec

# Type variables
_P = ParamSpec("_P")


class _FormatMapMapping(Protocol):
    # Copied verbatim from builtins.pyi for ToString's str methods
    def __getitem__(self, key: str, /) -> Any: ...


class _TranslateTable(Protocol):
    # Copied verbatim from builtins.pyi for ToString's str methods
    def __getitem__(self, key: int, /) -> str | int | None: ...


class ToString(str, metaclass=MethodWrappingMeta):

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
    def translate(self, table: _TranslateTable, /) -> str: ...
    def truncate(self, max_len: int | None = None, suffix: str = "..."
                 ) -> Self: ...

    def upper(self) -> Self: ...
    def zfill(self, width: SupportsIndex, /) -> Self: ...


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
    BRANCH = Branches()

    def prettify(self, prefix: ToString = ToString(),
                 branch: Branches = BRANCH) -> ToString: ...

    def prettify_spaces(self, indents_from_left: int = 0,
                        indent: str = "  ") -> str: ...

    def walk(self, depth_first: bool = True, include_self: bool = True
             ) -> Generator[Self, None, None]: ...


class SoupTree(BasicTree):

    @classmethod
    def from_soup(cls, page_el: bs4.element.PageElement) -> Self: ...


class WrapFunction:
    # Instance variables for (g/s)etstate: [func, pre, post, keywords]
    _VarsTypes = tuple[Callable, tuple, tuple, dict | None]

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    def __init__(self, func: Callable, pre: Any = (),
                 post: Any = (), **keywords: Any) -> None: ...

    def __reduce__(self) -> tuple[type[Self], tuple[Callable], _VarsTypes]: ...

    def __repr__(self) -> str: ...

    def __setstate__(self, state: _VarsTypes) -> None: ...

    def expect(self, output: Any) -> Self: ...

    def foreach(self, *objects: Any, **kwargs: Any
                ) -> Generator[Any, None, None]: ...


class Sets[T: Hashable](tuple[set[T], ...]):
    _R = TypeVar("_R")  # for _zip_sets method

    def __add__(self, others: Iterable[set[T]]) -> Self: ...

    @overload
    def __getitem__(self, key: SupportsIndex, /) -> set[T]: ...
    @overload
    def __getitem__(self, key: slice, /) -> Self: ...

    def __getitem__(self, key): ...

    def __new__(cls, iterables: Iterable[Iterable[T]] = ()) -> Self: ...

    @staticmethod
    def _reduce_set_method(func: Callable[[set[T], Iterable[T]], set[T]]
                           ) -> Callable[..., set[T]]: ...

    @staticmethod
    def _zip_sets(func: Callable[Concatenate[set[T], Iterable[T], _P], _R]
                  ):  # -> Callable[[Self, Sequence[set[T]]], Generator[_R,
        ...

    # Aliases for methods reducing all contained Sets to one output set
    combine = merge = union = _reduce_set_method(set.union)
    intersection = overlap = _reduce_set_method(set.intersection)
    unique = uniques = _reduce_set_method(set.symmetric_difference)

    concat = extend = __add__  # More synonymous method aliases

    # Operations to perform on each set in these Sets and the corresponding
    # set in a different Sequence of sets
    union_each = _zip_sets(set.union)
    update_each = exhaust_wrapper(_zip_sets(set.update))

    def append(self, *others: set[T]) -> Self: ...

    def apply(self, func: Callable[Concatenate[set[T], _P], _R],
              *args: _P.args, **kwargs: _P.kwargs
              ) -> Generator[_R, None, None]: ...

    def differentiate(self) -> Generator[set[T], None, None]: ...

    def filter(self, func: Callable[[T], Any]
               ) -> Generator[filter, None, None]: ...


class Valid:
    # Type hints for _validate method
    _F = TypeVar("_F")  # Reformatted validated input object
    _T = TypeVar("_T")  # Input object to validate

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
                  err_msg: str = "`{}` is invalid.",
                  first_ensure: Callable[[_T], Any] | None = None,
                  final_format: Callable[[_T], _F] | None = None): ...

    @classmethod
    def output_dir(cls, path: Any) -> str: ...

    @classmethod
    def readable_dir(cls, path: Any) -> str: ...

    @classmethod
    def readable_file(cls, path: Any) -> str: ...

    @classmethod
    def whole_number(cls, to_validate: Any) -> int: ...


class ArgParser(argparse.ArgumentParser):
    def add_new_out_dir_arg(self, name: str, **kwargs: Any) -> None: ...
