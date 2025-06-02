
"""
Totally redundant/trivial functions to use as callable default \
    values of optional parameters in other classes' methods.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-10
Updated: 2025-06-01
"""
# Import standard libraries
from typing import Any, Literal, TypeVar


T = TypeVar("T")  # For return_self/noop


def always_false(*_: Any, **_kwargs: Any) -> Literal[False]:
    """ :return: False """
    return False


def always_none(*_: Any, **_kwargs: Any) -> None:
    """ Do nothing. Always return None.

    :return: None """
    # pass  # or `...`


def always_true(*_: Any, **_kwargs: Any) -> Literal[True]:
    """ :return: True """
    return True


def call_method_of(an_obj: Any, method_name: str,
                   *args: Any, **kwargs: Any) -> Any:
    """ `an_obj.<method_name>(*args, **kwargs)`

    :param an_obj: Any, object with a method to call
    :param method_name: str naming the method of `an_obj` to call
    :param args: Iterable, positional arguments to call method with
    :param kwargs: Mapping[str, Any], keyword arguments to call method with
    :return: Any, the output of calling the method of `an_obj` with the \
        specified `args` and `kwargs`
    """
    return getattr(an_obj, method_name)(*args, **kwargs)


def is_not_none(x: Any) -> bool:
    return x is not None


def return_self(self: T) -> T:
    """ :return: self """
    return self
