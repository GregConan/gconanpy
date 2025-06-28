#!/usr/bin/env python3

"""
WrapFunction needs its own file to import ToString which imports MethodWrapper
Greg Conan: gregmconan@gmail.com
Created: 2025-06-21
Updated: 2025-06-27
"""
# Import standard libraries
from collections.abc import Callable, Generator, Iterable
from typing import Any
from typing_extensions import Self

# Import local custom libraries
try:
    from ToString import ToString
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.ToString import ToString


class WrapFunction:  # (Callable):
    """ Function wrapper that also stores some of its input parameters. """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input parameters
        """
        return self.inner(*args, **kwargs)

    def __init__(self, call: Callable, pre: Iterable = list(),
                 post: Iterable = list(), **kwargs: Any) -> None:
        """ Wrap/"freeze" a function with some parameters already defined \
            to call that function with those parameters later.

        :param call: Callable[[*pre, ..., *post], Any], the function to \
            wrap/"freeze" and then call/execute/"thaw" later.
        :param pre: Iterable of positional arguments to inject BEFORE the \
            `call` function's other positional input parameters.
        :param post: Iterable of positional arguments to inject AFTER the \
            `call` function's other positional input parameters.
        :param kwargs: Mapping[str, Any] of keyword arguments to call the \
            wrapped/"frozen" `call` function with.
        """
        if pre or post or kwargs:
            def inner(*in_args, **in_kwargs):
                in_kwargs.update(kwargs)
                return call(*pre, *in_args, *post, **in_kwargs)
        else:
            inner = call

        # Put all pre-defined args and kwargs into this instance's str repr
        # TODO Use stringify_map(kwargs) and stringify_iter(call, pre, post) ?
        self.stringified = ToString.represent_class(self.__class__)
        self.inner = inner

    def __repr__(self) -> str:
        """
        :return: str, annotated function header describing this WrapFunction.
        """
        return self.stringified

    def expect(self, output: Any) -> Self:
        """ 
        :param output: Any, expected output returned from inner \
            wrapped/"frozen" function.
        :return: WrapFunction[..., bool] that returns True if the inner \
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.inner(*args, **kwargs) == output
        return self.__class__(is_as_expected)

    def foreach(self, *objects: Any) -> Generator[Any, None, None]:
        """ Call the wrapped/"frozen" function with its specified parameters \
            on every object in `objects`. Iterate lazily; only call/execute \
            the wrapped function on each object at the moment of retrieval.

        :yield: Generator[Any, None, None], what the wrapped/"frozen" \
            function returns when given each object in `objects` as an input.
        """
        for an_obj in objects:
            yield self.inner(an_obj)
