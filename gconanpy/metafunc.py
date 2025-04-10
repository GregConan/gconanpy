#!/usr/bin/env python3

"""
Functions/classes to manipulate, or be manipulated by, functions/classes.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-04-09
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Hashable, Iterable, Mapping, Sequence
import pdb
from typing import Any, TypeVar


def find_an_attr_in(attrs_of: Any, attr_names: Iterable[str], default:
                    Any = None, method_names: set[str] = set()) -> Any:
    found_attr = default
    ix = 0
    while ix + 1 < len(attr_names) and not hasattr(attrs_of,
                                                   attr_names[ix]):
        ix += 1
    try:
        name = attr_names[ix]
        found_attr = getattr(attrs_of, name, default)
        if name in method_names:
            found_attr = found_attr()
    except (AttributeError, IndexError, TypeError):
        pass
    return found_attr


def has_method(an_obj: Any, method_name: str) -> bool:
    return callable(getattr(an_obj, method_name, None))


def nameof(an_obj: Any) -> str:
    """ Get the `__name__` of an object or of its type/class.

    :param an_obj: Any
    :return: str naming an_obj, usually its type/class name.
    """
    return getattr(an_obj, "__name__", type(an_obj).__name__)


class Trivial(ABC):
    """ Totally redundant/trivial methods to use as callable default \
        values of method parameters in other classes. """
    _K = TypeVar("_K", bound=Hashable)
    _V = TypeVar("_V")

    @staticmethod
    def get_item_of(x: Sequence[_V] | Mapping[_K, _V], i: _K) -> _V:
        """ `x.__getitem__(i)` """
        return x[i]

    @staticmethod
    def is_not_none(x: Any) -> bool: return x is not None

    @staticmethod
    def noop(*_args: Any, **_kwargs: Any) -> None:
        """ Do nothing. """
        pass  # or `...`


class SkipException(BaseException):
    ...


class IgnoreExceptions:
    def __init__(self, *catch: type[BaseException]) -> None:
        self.catch = catch

    def __enter__(self):
        """ Must be explicitly defined here (not only in a superclass) for \
            VSCode to realize that IgnoreExceptions(...) returns an \
            instance of the IgnoreExceptions class.

        :return: IgnoreExceptions, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        return (not self.catch) or (exc_type in self.catch)


class SkipOrNot(IgnoreExceptions):
    def __init__(self, parent: "KeepTryingUntilNoException", *catch) -> None:
        super().__init__(*catch)
        self.parent = parent


class Skip(SkipOrNot):
    def __enter__(self):
        raise SkipException


class DontSkip(SkipOrNot):
    def __exit__(self, exc_type: type[BaseException] | None = None,
                 exc_val: BaseException | None = None, _: Any = None) -> bool:
        if exc_val is None:
            self.parent.is_done = True
        else:
            self.parent.errors.append(exc_val)
        return super(DontSkip, self).__exit__(exc_type)


class KeepTryingUntilNoException:
    def __init__(self, *catch: type[BaseException]) -> None:
        self.catch = catch
        self.errors = list()
        self.is_done = False

    def __call__(self) -> Skip | DontSkip:
        skip_or_not = Skip if self.is_done else DontSkip
        return skip_or_not(self, *self.catch)

    def __enter__(self):
        """ Must be explicitly defined here (not only in a superclass) for \
            VSCode to realize that KeepTryingUntilNoException(...) returns \
            an instance of the KeepTryingUntilNoException class.

        :return: KeepTryingUntilNoException, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        return exc_type is SkipException


def wrap_with_params(call: Callable, *args: Any, **kwargs: Any) -> Callable:
    """
    Define values to pass into a previously-defined function ("call"), and
    return that function object wrapped with its new preset/default values
    :param call: Callable, function to add preset/default parameter values to
    :return: Callable, "call" with preset/default values for the 'args' and
             'kwargs' parameters, so it only accepts one positional parameter
    """
    def wrapped(*fn_args: Any, **fn_kwargs: Any) -> Any:
        fn_kwargs.update(kwargs)
        # print(f"Calling {call.__name__}(*{args}, *{fn_args}, **{fn_kwargs})")
        return call(*args, *fn_args, **fn_kwargs)
    return wrapped
