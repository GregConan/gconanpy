#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-21
Updated: 2025-04-28
"""
# Import standard libraries
from collections.abc import Callable, Iterable
import inspect
import re
from typing import Any

# Import third-party PyPI libraries
from makefun import create_function, with_signature

# Import local custom libraries
try:
    from metafunc import (add_attributes_to, AttributesOf,
                          combine_maps, nameof)
    from seq import ToString
except ModuleNotFoundError:
    from gconanpy.metafunc import (add_attributes_to, AttributesOf,
                                   combine_maps, nameof)
    from gconanpy.seq import ToString


Wrapper = Callable[[Callable], Callable]


def all_annotations_of(a_class: type) -> dict[str, type]:
    return combine_maps([getattr(base, "__annotations__", dict())
                         for base in reversed(a_class.__mro__)])


def signature_extends(func: Callable,
                      pre: Iterable[inspect.Parameter] = list(),
                      post: Iterable[inspect.Parameter] = list(),
                      default: Any = None, **kwargs) -> Wrapper:
    for param, attr in dict(
        func_name="name", doc="doc", module_name="module", qualname="qualname"
    ).items():
        kwargs.setdefault(param, getattr(func, f"__{attr}__", default))

    old_params = inspect.signature(func).parameters
    new_sig = inspect.Signature(parameters=[*pre, *old_params.values(), *post])

    return with_signature(new_sig, **kwargs)


def append_default(a_func: Callable) -> Callable:
    def_ret = inspect.Parameter(
        "default_return", default=None, annotation=Any,
        kind=inspect._ParameterKind.POSITIONAL_OR_KEYWORD)

    @signature_extends(a_func, post=[def_ret])
    def wrapper(self, *args, default_return, **kwargs):
        try:
            result = a_func(self, *args, **kwargs)
            return result if result else default_return
        except TypeError:
            return default_return
    return wrapper


def extend(a_class: type, name: str, **wrappers: Wrapper) -> type:
    return type(name, tuple(), {  # TODO Allow for adding wholly new methods
        meth_name: wrappers[meth_name](meth) if meth_name in wrappers
        else meth for meth_name, meth in AttributesOf(a_class).methods()})


def extend1(a_class: type, name: str, wrapper: Wrapper, *methods: str) -> type:
    return extend(a_class, name, **{m: wrapper for m in methods})


def initialize(self: Any, *args: Any, **kwargs: Any) -> None:
    """ Generic __init__ function for `weak_dataclass` to specify by adding \
        a method signature.

    :param self: Any, object with a `__slots__: tuple[str, ...]` attribute \
        naming the `__init__` input arguments.
    """
    for i in range(len(args)):
        kwargs[self.__slots__[i]] = args[i]
    add_attributes_to(self, **kwargs)


def params_for(a_class: type, *args: inspect.Parameter
               ) -> list[inspect.Parameter]:
    POS_OR_KEY = inspect.Parameter.POSITIONAL_OR_KEYWORD
    params = [inspect.Parameter(name="self", kind=POS_OR_KEY,
                                annotation=a_class)]
    withdefaults: list[inspect.Parameter] = list()
    for name, annotation in all_annotations_of(a_class).items():
        pkwargs = dict(name=name, annotation=annotation, kind=POS_OR_KEY)
        if hasattr(a_class, name):
            pkwargs["default"] = getattr(a_class, name)
            withdefaults.append(inspect.Parameter(**pkwargs))
        else:
            params.append(inspect.Parameter(**pkwargs))
    for arg in args:
        if arg.default is arg.empty:
            params.append(arg)
        else:
            withdefaults.append(arg)
    return [*params, *withdefaults]


RegexSearcher = extend1(re.Match, "RegexSearcher", append_default,
                        "groups", "groupdict")


class WeakDataclassBase:

    def __repr__(self) -> str:
        attrs = {x: ToString.from_object(getattr(self, x), max_len=100)
                 for x in self.__slots__}
        attrs_str = ToString.from_mapping(attrs, quote=None, join_on="=",
                                          prefix="(", suffix=")")
        return nameof(self) + attrs_str

    def __eq__(self, other) -> bool:
        return self.__slots__ == other.__slots__ and \
            all([getattr(self, x) == getattr(other, x)
                for x in self.__slots__])


def weak_dataclass(a_class: type, *args: inspect.Parameter) -> type:
    all_params = params_for(a_class, *args)
    new_sig = inspect.Signature(all_params, return_annotation=None)
    WeakDataclass = type(nameof(a_class), (a_class, WeakDataclassBase),
                         dict())
    WeakDataclass.__slots__ = tuple([p.name for p in all_params[1:]])
    WeakDataclass.__init__ = create_function(new_sig, initialize,
                                             func_name="__init__",
                                             qualname="__init__")
    return WeakDataclass
