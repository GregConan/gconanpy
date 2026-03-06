#!/usr/bin/env python3

"""
Classes that wrap other classes, especially builtins, to add functionality.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2026-03-05
"""
# Import standard libraries
import argparse
# from collections import UserString  # TODO?
from collections.abc import Callable, Generator, \
    Hashable, Iterable, Sequence
import functools  # from functools import reduce, wraps
from more_itertools import all_equal
import os
from typing import Any, cast, Concatenate, NamedTuple, \
    overload, ParamSpec, Self, SupportsIndex, TypeVar

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
try:
    from gconanpy.iters import exhaust_wrapper
    from gconanpy.meta import cached_property, tuplify
    from gconanpy.strings import FancyString
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from .iters import exhaust_wrapper
    from .meta import cached_property, tuplify
    from .strings import FancyString

# Type variables
_P = ParamSpec("_P")


class Branches(NamedTuple):
    """ A defined tuple of symbols to visually represent a branching
        hierarchical tree structure, like a filesystem directory or a
        document written in a markup language (e.g. HTML, XML, markdown,
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

    def prettify(self, prefix: FancyString = FancyString(),
                 branch: Branches = BRANCH) -> FancyString:
        pretties = [prefix + self[0]]

        if prefix.endswith(branch.L):
            prefix = prefix.rreplace(
                branch.L, branch.O, count=1).replace(branch.T, branch.I)

        if self[1]:
            for child in self[1][:-1]:
                pretties.append(child.prettify(prefix + branch.T, branch))
            pretties.append(self[1][-1].prettify(
                prefix.replace(branch.T, branch.I) + branch.L, branch))

        return FancyString("\n").join(pretties)

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
        self.full = (FancyString.fromBeautifulSoup(page_el, "first"),
                     FancyString.fromBeautifulSoup(page_el, "last"))
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
        :return: Any, the output of calling the wrapped/"frozen" function
            with the specified input arguments
        """
        return self.func(*self.pre, *args, *self.post,
                         **self.keywords, **kwargs)

    def __init__(self, func: Callable, pre: Any = (),
                 post: Any = (), **keywords: Any) -> None:
        """ Wrap/"freeze" a function with some parameters already defined
            to call that function with those parameters later.

        Same as `functools.partial`, but `WrapFunction` lets you define
        positional arguments to pass to the wrapped function before *and*
        after the positional arguments passed at execution.

        :param func: Callable[[*pre, ..., *post], Any], the function to
            wrap/"freeze" and then call/execute/"thaw" later.
        :param pre: Iterable of positional arguments to inject BEFORE the
            `func` function's other positional input parameters; or the
            first positional argument to `func` (a string or a non-iterable).
        :param post: Iterable of positional arguments to inject AFTER the
            `func` function's other positional input parameters; or the
            last positional argument to `func` (a string or a non-iterable).
        :param keywords: Mapping[str, Any] of keyword arguments to call the
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
        :param output: Any, expected output returned from inner
            wrapped/"frozen" function.
        :return: WrapFunction[..., bool] that returns True if the inner
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.func(*args, **kwargs) == output
        return type(self)(is_as_expected)

    def foreach(self, *objects: Any, **kwargs: Any
                ) -> Generator[Any, None, None]:
        """ Call the wrapped/"frozen" function with its specified parameters
            on every object in `objects`. Iterate lazily; only call/execute
            the wrapped function on each object at the moment of retrieval.

        :param objects: Iterable[Any], each positional input argument to
            call this `WrapFunction` on once
        :param kwargs: Mapping[str, Any], keyword arguments to call this
            `WrapFunction` with on every object in `objects`
        :yield: Generator[Any, None, None], what the wrapped/"frozen"
            function returns when given each object in `objects` as an input.
        """
        for an_obj in objects:
            yield self.func(an_obj, **kwargs)

    @cached_property[FancyString]
    def stringified(self) -> FancyString:
        """
        :return: FancyString, representation of this `WrapFunction` instance 
            including all of its pre-defined positional and keyword arguments.
        """
        return FancyString.fromCallable(type(self), **vars(self))


# @ClassWrapper(tuple).class_decorator  # TODO?
class Sets[T: Hashable](tuple[set[T], ...]):
    """ Wrapper class to centralize methods comparing/using multiple sets. """
    _R = TypeVar("_R")  # for _zip_sets method

    are_same = all_equal  # Check whether sets have the same elements

    def __add__(self, others: Iterable[set[T]]) -> Self:
        """ Concatenates `others` to these `Sets`.

        Returns `self + value`. Defined to return a `Sets` instance. 

        :param others: Iterable[set[T], ...], other sets to append to this
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
        @functools.wraps(func)
        def inner(self) -> set[T]:
            return functools.reduce(func, self) if self else set[T]()

        # Copy the original method's docstring, but update it for Sets class
        doc = getattr(func, "__doc__", None)
        if doc is not None:
            inner.__doc__ = FancyString.fromAny(doc).replace_all({
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
        """ Appends `others` to these `Sets`. Same as `concat`, but accepts
            an individual `set` instance as an argument.

        :param others: Iterable[set[T], ...], other sets to append to this
            `Sets` tuple
        :return: Self, a `Sets` instance with `others` concatenated to the end
        """
        return self + others

    def apply(self, func: Callable[Concatenate[set[T], _P], _R],
              *args: _P.args, **kwargs: _P.kwargs
              ) -> Generator[_R, None, None]:
        return (func(s, *args, **kwargs) for s in self)

    def differentiate(self) -> Generator[set[T], None, None]:
        """ Return a copy of the sets without any shared elements. Each will
            only have its unique items, so they do no overlap/intersect.

        :return: Generator[set[T], None, None], each set with only its
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
        :param conditions: Iterable[Callable[[_T], bool]] that each accept
            `to_validate` and returns True if and only if `to_validate`
            passes some specific condition, otherwise returning False
        :param final_format: Callable[[_T], _F: Any] that accepts
            `to_validate` and returns it after fully validating it
        :param err_msg: str to show to user to tell them what is invalid
        :param first_ensure: Callable[[_T], Any] to run on `to_validate` to
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
        """ Use this instead of `argparse.FileType('r')` because the latter
            leaves an open file handle.

        :param path: Any, object that should be a valid file (or dir) path.
        :raise: argparse.ArgumentTypeError if `path` isn't a path to a valid
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
    """ Extends `argparse.ArgumentParser` to include default values that I
        tend to re-use. Purely for convenience. """

    def add_new_out_dir_arg(self, name: str, **kwargs: Any) -> None:
        """ Specifies argparse.ArgumentParser.add_argument for a valid path
            to an output directory that must either exist or be created.

        :param name: str naming the directory to access (and create if needed)
        :param kwargs: Mapping[str, Any], keyword arguments for the method
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
