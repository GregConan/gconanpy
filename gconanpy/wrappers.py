#!/usr/bin/env python3

"""
Classes that wrap other classes, especially builtins, to add functionality.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-04
Updated: 2026-04-08
"""
# Import standard libraries
from collections.abc import Callable, Generator, \
    Hashable, Iterable, Sequence
import functools  # from functools import reduce, wraps
from more_itertools import all_equal
from typing import Any, cast, Concatenate, NamedTuple, \
    overload, ParamSpec, Self, SupportsIndex, TypeVar

# Import third-party PyPI libraries
import bs4
import html_to_markdown as html2md

# Import local custom libraries
try:
    from gconanpy.iters import exhaust_wrapper
    from gconanpy.meta import cached_property, tuplify
    from gconanpy.reg import compress, Regextract
    from gconanpy.strings import FancyString
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from .iters import exhaust_wrapper
    from .meta import cached_property, tuplify
    from .reg import compress, Regextract
    from .strings import FancyString

# Type variables
_P = ParamSpec("_P")
_R = TypeVar("_R")


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
class ObjecTuple[T](tuple[T, ...]):
    """ Wrapper class to centralize methods operating on multiple objects. """
    are_same = all_equal  # Check whether iterables have the same elements

    def __add__(self, others: Iterable[T]) -> Self:
        """ Concatenates `others` to the end of this `ObjecTuple`.

        Returns `self + value`. Defined to return an `ObjecTuple` instance. 

        :param others: Iterable[T], other iterables to append to
            this `ObjecTuple`.
        :return: Self, an `ObjecTuple` instance with `others` added to the end.
        """
        return type(self)(super().__add__(tuple[T, ...](others)))

    @overload
    def __getitem__(self, key: SupportsIndex, /) -> T: ...
    @overload
    def __getitem__(self, key: slice, /) -> Self: ...

    def __getitem__(self, key):
        """ Returns `self[key]`.

        Defined explicitly so that slicing returns an instance of this class.

        :return: slice | T, `self[key]`
        """
        gotten = super().__getitem__(key)
        if isinstance(key, slice):  # if isinstance(gotten, tuple):
            gotten = type(self)(gotten)
        return gotten

    def append(self, *others: T) -> Self:
        """ Appends `others` to these objects. Same as `concat`, but accepts
            an individual object instance as an argument.

        :param others: Iterable[T], other objects to append to this ObjecTuple
        :return: Self, an `ObjecTuple` with `others` concatenated to the end
        """
        return self + others

    def apply(self, func: Callable[Concatenate[T, _P], _R],
              *args: _P.args, **kwargs: _P.kwargs
              ) -> Generator[_R, None, None]:
        return (func(s, *args, **kwargs) for s in self)

    concat = extend = __add__  # Synonymous method aliases


# @ClassWrapper(tuple).class_decorator  # TODO?
class IterTuple[T: Iterable](ObjecTuple[T]):
    """ Wrapper class to centralize methods comparing/using 
        multiple iterables. """

    def filter_on(self, func: Callable[[T], Any]
                  ) -> Generator[filter, None, None]:
        return (filter(func, s) for s in self)


class Sets[T: Hashable](IterTuple[set[T]]):
    """ Wrapper class to centralize methods comparing/using multiple sets. """

    def __new__(cls, iterables: Iterable[Iterable[T]] = ()) -> Self:
        """ 
        :param iterables: Iterable[Iterable[T]] to convert into `Sets`
        :return: Self, a tuple of all input `iterables` as `Sets`
        """
        return super().__new__(cls, (set[T](x) for x in iterables))

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

    # Operations to perform on each set in these Sets and the corresponding
    # set in a different Sequence of sets
    union_each = _zip_sets(set.union)
    update_each = exhaust_wrapper(_zip_sets(set.update))

    def differentiate(self) -> Generator[set[T], None, None]:
        """ Return a copy of the sets without any shared elements. Each will
            only have its unique items, so they do no overlap/intersect.

        :return: Generator[set[T], None, None], each set with only its
            unique items
        """
        return (self[i].difference((self[:i] + self[i+1:]).union()
                                   ) for i in range(len(self)))
