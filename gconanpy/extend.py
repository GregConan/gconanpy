#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-21
Updated: 2025-04-22
"""
# Import standard libraries
from collections.abc import Callable, Iterable, Mapping
import functools
import inspect
import pdb
import re
from typing import Any, TypeVar

# Import third-party PyPI libraries
from makefun import create_function, with_signature

# Import local custom libraries
try:
    from metafunc import AttributesOf, nameof
    from seq import ToString
except ModuleNotFoundError:
    from gconanpy.metafunc import AttributesOf, nameof
    from gconanpy.seq import ToString


M = TypeVar("M", bound=Mapping)
T = TypeVar("T")
ObjType = TypeVar("ObjType", bound=type)
Wrapper = Callable[[Callable], Callable]


def add_attributes_to(an_obj: T, **attributes: Any) -> T:
    for attr_name, attr_value in attributes.items():
        setattr(an_obj, attr_name, attr_value)
    return an_obj


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


def build(obj_class: ObjType = object, obj_args: Iterable = list(),
          obj_kwargs: Mapping[str, Any] = dict(), **attributes: Any
          ) -> ObjType:
    return add_attributes_to(obj_class(*obj_args, **obj_kwargs),
                             **attributes)


def combine_maps(maps: Iterable[M]) -> M:
    return functools.reduce(lambda x, y: x.update(y) or x, maps)


def extend(a_class: type, name: str, **wrappers: Wrapper
           ) -> type:
    return type(name, tuple(), {  # TODO Allow for adding wholly new methods
        meth_name: wrappers[meth_name](meth) if meth_name in wrappers
        else meth for meth_name, meth in AttributesOf(a_class).methods()})


def extend1(a_class: type, name: str, wrapper: Wrapper, *methods: str) -> type:
    return extend(a_class, name, **{m: wrapper for m in methods})


RegexSearcher = extend1(re.Match, "RegexSearcher", append_default,
                        "groups", "groupdict")


def init_wrapper(self, *args, **kwargs) -> None:
    for i in range(len(args)):
        kwargs[self.__slots__[i]] = args[i]
    add_attributes_to(self, **kwargs)


def repr_wrapper(self) -> str:
    attrs = {x: ToString.from_object(getattr(self, x), max_len=100)
             for x in self.__slots__}
    attrs_str = ToString.from_mapping(attrs, quote=None, join_on="=",
                                      enclose_in=("(", ")"))
    return nameof(self) + attrs_str


def eq_wrapper(self, other) -> bool:
    return self.__slots__ == other.__slots__ and \
        all([getattr(self, x) == getattr(other, x)
             for x in self.__slots__])


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


def weak_dataclass(a_class: type, *args: inspect.Parameter,
                   **kwargs) -> type:
    all_params = params_for(a_class, *args)
    new_sig = inspect.Signature(all_params, return_annotation=None)
    a_class.__slots__ = tuple([p.name for p in all_params[1:]])

    # TODO Move *_wrapper into WeakDataclassBase and extend() it
    a_class.__init__ = create_function(new_sig, init_wrapper,
                                       func_name="__init__",
                                       qualname="__init__", **kwargs)
    a_class.__repr__ = create_function("__repr__(self) -> str:",
                                       repr_wrapper, func_name="__repr__")
    a_class.__eq__ = create_function("__eq__(self, other) -> bool",
                                     eq_wrapper, func_name="__eq__")

    return a_class
