
"""
Totally redundant/trivial methods to use as callable default \
values of optional parameters in other classes' methods.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-10
Updated: 2025-04-10
"""
# Import standard libraries
from typing import Any, Literal

try:
    from metafunc import has_method
except ModuleNotFoundError:
    from gconanpy.metafunc import has_method


class SupportsGetItemMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for SupportsGetItem class creation.
    """
    def __instancecheck__(cls, instance):
        return has_method(instance, "__getitem__")

    def __subclasscheck__(cls, subclass):
        return has_method(subclass, "__getitem__")


class SupportsGetItem(metaclass=SupportsGetItemMeta):
    ...


def always_false(*_: Any, **_kwargs: Any) -> Literal[False]:
    """ :return: False """
    return False


def always_true(*_: Any, **_kwargs: Any) -> Literal[True]:
    """ :return: True """
    return True


def get_item_of(maplike: SupportsGetItem, key: Any) -> Any:
    """ `maplike[key]` a.k.a. `maplike.__getitem__(key)` 

    :param maplike: SupportsGetItem
    :param key: Hashable, a key mapped to a value in maplike 
    :return: Any, value mapped to key in maplike
    """
    return maplike[key]


def is_not_none(x: Any) -> bool:
    return x is not None


def noop(*_: Any, **_kwargs: Any) -> None:
    """ Do nothing. Always return None.

    :return: None """
    pass  # or `...`
