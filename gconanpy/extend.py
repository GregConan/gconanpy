#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-21
Updated: 2025-07-28
"""
# Import standard libraries
from collections.abc import (Callable, Container, Generator,
                             Iterable, Iterator, Mapping)
import graphlib
import inspect
import re
from types import ModuleType
from typing import Any

# Import third-party PyPI libraries
from makefun import create_function, with_signature

# Import local custom libraries
try:
    import attributes
    from iters import merge
    from meta import HasSlots, name_of, pairs
    from wrappers import ToString
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy import attributes
    from gconanpy.iters import merge
    from gconanpy.meta import HasSlots, name_of, pairs
    from gconanpy.wrappers import ToString


# Function wrapper type variable  # TODO DRY (can't import it from metafunc?)
Wrapper = Callable[[Callable], Callable]


def all_annotations_of(a_class: type) -> dict[str, type]:
    """ 
    :param a_class: type
    :return: dict[str, type], the `__annotations__` of `a_class` and all of \
        its parent (`__mro__`) classes, prioritizing `a_class`'s annotations
    """
    return merge([getattr(base, "__annotations__", dict())
                  for base in reversed(a_class.__mro__)])


def classes_in_module(module: ModuleType) -> Generator[tuple[str, type],
                                                       None, None]:
    """ Iterate over every `class` defined in `module`.

    :param module: ModuleType, a Python module.
    :yield: Generator[tuple[str, type], None, None], name-class pairs for \
        every `class` defined in `module`.
    """
    def is_class_from_module(an_obj: Any) -> bool:
        return inspect.isclass(an_obj) and an_obj.__module__ == name_of(module)
    yield from inspect.getmembers(module, is_class_from_module)


def combine(name: str, classes: Iterable[type], **kwargs: Any) -> type:
    """ Create a new class that inherits from all `classes` specified.

    :param name: str, name of the new class to return.
    :param classes: Iterable[type], every parent/superclass of the returned \
        child/subclass. 
    :return: type, subclass of all specified `classes`.
    """
    return type(name, trim_MRO(make_MRO_for_subclass_of(*classes)), kwargs)


def extend(a_class: type, name: str, wrappers: Mapping[str, Wrapper],
           **new: Any) -> type:
    wrapped = {meth_name: wrappers[meth_name](meth)
               if meth_name in wrappers else meth
               for meth_name, meth in attributes.AttrsOf(a_class).methods()}
    return type(name, tuple(), {**wrapped, **new})


def extend1(a_class: type, name: str, wrapper: Wrapper, *methods: str) -> type:
    return extend(a_class, name, {m: wrapper for m in methods})


def initialize(self: HasSlots, *args: Any, **kwargs: Any) -> None:
    """ Generic `__init__` function for `weak_dataclass` to specify by \
        adding a method signature.

    :param self: HasSlots, object with a `__slots__: tuple[str, ...]` attribute \
        naming the `__init__` input arguments.
    """
    if "__slots__" in kwargs:
        kwargs.pop("__slots__")
    for i in range(len(args)):
        kwargs[self.__slots__[i]] = args[i]
    attributes.add_to(self, **kwargs)


def make_MRO_for_subclass_of(*types: type) -> Iterator[type]:
    """ Get the full properly-sorted method resolution order (MRO) for a new \
        child/subclass of all specified parents/superclasses in `types`.

    :return: Iterator[type] that yields all classes in the correct MRO
    """
    dag_dict = dict()
    for each_class in types:
        # Exclude self (`each_class`) and object class (`object`) from MRO
        dag_dict[each_class] = inspect.getmro(each_class)[1:-1]
    rev_mro = graphlib.TopologicalSorter(dag_dict).static_order()
    return reversed([each_class for each_class in rev_mro])


def module_classes_to_args_dict(module: ModuleType, *suffixes: str,
                                ignore: Container[type] = set()
                                ) -> dict[str, type]:
    classes = dict()
    for class_name, each_class in classes_in_module(module):
        for suffix in suffixes:
            if class_name.endswith(suffix) and each_class not in ignore:
                classes[class_name.removesuffix(suffix).lower()] = each_class
                break
    return classes


def params_for(a_class: type, *args: inspect.Parameter
               ) -> list[inspect.Parameter]:
    POS_OR_KEY = inspect.Parameter.POSITIONAL_OR_KEYWORD
    params = [self_param(self_is=a_class)]
    withdefaults: list[inspect.Parameter] = list()
    for name, annotation in all_annotations_of(a_class).items():
        pkwargs = dict(name=name, annotation=annotation, kind=POS_OR_KEY)
        if hasattr(a_class, name):
            pkwargs["default"] = getattr(a_class, name)
            withdefaults.append(inspect.Parameter(**pkwargs))  # type: ignore
        else:
            params.append(inspect.Parameter(**pkwargs))  # type: ignore
    for arg in args:
        if arg.default is arg.empty:
            params.append(arg)
        else:
            withdefaults.append(arg)
    return [*params, *withdefaults]


def self_param(self_is: type) -> inspect.Parameter:
    return inspect.Parameter(name="self", annotation=self_is,
                             kind=inspect.Parameter.POSITIONAL_ONLY)


def trim_MRO(classes: Iterable[type]) -> tuple[type]:
    """ Get the minimal method resolution order (MRO) for a subclass of all \
        specified `classes`.

    :param classes: Iterable[type], all parents/superclasses of a new \
        child/subclass to determine the minimal MRO of.
    :return: tuple[type], all base classes in a correctly-sorted MRO for a \
        child/subclass of all `classes` specified; tuple (instead of list) \
        to use as 2nd parameter to dynamically define a class using type(...)
    """
    minimal_MRO = list()
    for each_class in classes:
        is_redundant = False
        for needed_class in minimal_MRO:
            if issubclass(needed_class, each_class):
                is_redundant = True
                break
        if not is_redundant:
            minimal_MRO.append(each_class)
    return tuple(minimal_MRO)  # type(...) 2nd parameter must be a tuple


def signature_extends(func: Callable,
                      pre: Iterable[inspect.Parameter] = list(),
                      post: Iterable[inspect.Parameter] = list(),
                      default: Any = None, **kwargs) -> Wrapper:
    """
    :param func: Callable, function or method to extend the signature of
    :param pre: Iterable[inspect.Parameter] of new arguments to prepend to \
        `func`'s signature before its existing input arguments
    :param post: Iterable[inspect.Parameter] of new arguments to append to \
        `func`'s signature after its existing input arguments
    :param default: Any,_description_, defaults to None
    :return: Callable[[Callable], Callable], Wrapper, function decorator to \
        add the specified input arguments to a given method/function `func`
    """
    for param, attr in pairs("doc", "qualname", func_name="name",
                             module_name="module"):
        kwargs.setdefault(param, getattr(func, f"__{attr}__", default))

    old_params = inspect.signature(func).parameters
    new_sig = inspect.Signature(parameters=[*pre, *old_params.values(), *post])

    return with_signature(new_sig, **kwargs)


def append_default(a_func: Callable) -> Callable:
    """ 
    :param a_func: Callable, function or method to extend by appending a new \
        input parameter to its signature called `default_return`, which is \
        the value for `append_default`'s returned function/method to return \
        if `a_func` retunrns something falsy
    :return: Callable, function decorator to add the new `default_return` \
        input parameter to a given function/method `a_func`
    """
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


RegexSearcher = extend1(re.Match, "RegexSearcher", append_default,
                        "groups", "groupdict")


class WeakDataclassBase:
    __slots__: tuple

    def __repr__(self) -> str:
        return ToString.fromCallable(type(self), **{
            x: getattr(self, x) for x in self.__slots__}, max_len=100)

    def __eq__(self, other) -> bool:
        return self.__slots__ == other.__slots__ and \
            all([getattr(self, x) == getattr(other, x)
                for x in self.__slots__])


def weak_dataclass(a_class: type, *args: inspect.Parameter) -> type:
    all_params = params_for(a_class, *args)
    init_sig = inspect.Signature(all_params, return_annotation=None)
    WeakDataclass = type(name_of(a_class), (a_class, WeakDataclassBase),
                         dict())
    WeakDataclass.__slots__ = tuple([p.name for p in all_params[1:]
                                     if p.name != "__slots__"])
    WeakDataclass.__init__ = create_function(init_sig, initialize,
                                             func_name="__init__",
                                             qualname="__init__")
    return WeakDataclass
