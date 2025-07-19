#!/usr/bin/env python3

"""
WrapFunction needs its own file to import ToString which imports MethodWrapper
Greg Conan: gregmconan@gmail.com
Created: 2025-06-21
Updated: 2025-07-15
"""
# Import standard libraries
from collections.abc import Callable, Generator
# from functools import partial
from typing import Any
from typing_extensions import Self

# Import local custom libraries
try:
    from meta.funcs import tuplify
    from ToString import ToString
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.meta.funcs import tuplify
    from gconanpy.ToString import ToString


class WrapFunction:  # WrapFunction(partial):
    """ Function wrapper that also stores some of its input parameters.
        `functools.partial` modified to prepend OR append parameters. """
    _VarsTypes = tuple[Callable, tuple, tuple, dict | None]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input parameters
        """
        return self.func(*self.pre, *args, *self.post,
                         **self.keywords, **kwargs)

    def __init__(self, func: Callable, pre: Any = tuple(),
                 post: Any = tuple(), **keywords: Any) -> None:
        """ Wrap/"freeze" a function with some parameters already defined \
            to call that function with those parameters later.

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
        self.pre = tuplify(pre)
        self.post = tuplify(post)
        self.keywords = keywords

    def __reduce__(self) -> tuple[type, tuple[Callable], _VarsTypes]:
        return type(self), (self.func, ), (self.func, self.pre, self.post,
                                           self.keywords or None)

    def __setstate__(self, state: _VarsTypes) -> None:
        self.func, self.pre, self.post, keywords = state
        self.keywords = keywords if keywords else dict()

    def __repr__(self) -> str:
        """
        :return: str, annotated function header describing this WrapFunction.
        """
        # Put all pre-defined args and kwargs into this instance's str repr
        if not getattr(self, "stringified", None):
            self.stringified = ToString.fromCallable(
                type(self), **self.__dict__)
        return self.stringified

    def expect(self, output: Any) -> Self:
        """ 
        :param output: Any, expected output returned from inner \
            wrapped/"frozen" function.
        :return: WrapFunction[..., bool] that returns True if the inner \
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.func(*args, **kwargs) == output
        return self.__class__(is_as_expected)

    def foreach(self, *objects: Any) -> Generator[Any, None, None]:
        """ Call the wrapped/"frozen" function with its specified parameters \
            on every object in `objects`. Iterate lazily; only call/execute \
            the wrapped function on each object at the moment of retrieval.

        :yield: Generator[Any, None, None], what the wrapped/"frozen" \
            function returns when given each object in `objects` as an input.
        """
        for an_obj in objects:
            yield self.func(an_obj)
