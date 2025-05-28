
"""
Totally redundant/trivial functions to use as callable default \
values of optional parameters in other classes' methods.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-10
Updated: 2025-05-27
"""
# Import standard libraries
import abc
from typing import Any, Literal, TypeVar


T = TypeVar("T")  # For return_self/noop


class SupportsGetItem(abc.ABC):
    """ Any object with a `__getitem__` method is a `SupportsGetItem`. """
    @abc.abstractmethod
    def __getitem__(self, name: Any) -> bool:
        ...


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


def equals(x: Any, y: Any) -> bool:
    """ :return: bool, x == y """
    return x == y


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


def get_item_of(maplike: SupportsGetItem, key: Any) -> Any:
    """ `maplike[key]` a.k.a. `maplike.__getitem__(key)` 

    :param maplike: SupportsGetItem
    :param key: Hashable, a key mapped to a value in maplike 
    :return: Any, value mapped to key in maplike
    """
    return maplike[key]


def is_not_none(x: Any) -> bool:
    return x is not None


def return_self(self: T) -> T:
    """ :return: self """
    return self
