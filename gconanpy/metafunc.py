#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-04-16
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Generator, Hashable, Iterable
# import datetime as dt
# import inspect
# from makefun import create_function, create_wrapper, with_signature, wraps
import pdb
from typing import Any, TypeVar  # Generic, ParamSpec,


# Constants

# Purely "internal" errors only involving local data; ignorable in some cases
DATA_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)

# Names of methods not to overwrite when wrapping an object
ESSENTIALS = {f"__{attr}__" for attr in
              ("class", "class_getitem", "delattr", "getattribute",  # "doc",
               "hash", "init", "init_subclass", "new", "reduce",
               "reduce_ex", "setattr", "subclasshook")}


def has_method(an_obj: Any, method_name: str) -> bool:
    """
    :param an_obj: Any
    :param method_name: str, name of a method that `an_obj` might have.
    :return: bool, True if `method_name` names a callable attribute \
        (method) of `an_obj`; otherwise False.
    """
    return callable(getattr(an_obj, method_name, None))


def nameof(an_obj: Any) -> str:
    """ Get the `__name__` of an object or of its type/class.

    :param an_obj: Any
    :return: str naming an_obj, usually its type/class name.
    """
    return getattr(an_obj, "__name__", type(an_obj).__name__)


class BoolableMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for Boolable class creation.
    """
    def __instancecheck__(cls, instance: Any) -> bool:
        try:
            bool(instance)
            return True
        except (TypeError, ValueError):
            return False

    def __subclasscheck__(cls, subclass: type) -> bool:
        methods = ("__bool__", "__len__")
        return bool(AttributesOf(subclass).first_of(methods, None,
                                                    set(methods)))
        # return find_an_attr_in(subclass, methods, None, set(methods))


class Boolable(metaclass=BoolableMeta):
    """ Any object that you can call `bool()` on is a `Boolable`. """
    ...


class SupportsGetItemMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for SupportsGetItem class creation.
    """
    def __instancecheck__(cls, instance: Any) -> bool:
        return has_method(instance, "__getitem__")

    def __subclasscheck__(cls, subclass: type) -> bool:
        return has_method(subclass, "__getitem__")


class SupportsGetItem(metaclass=SupportsGetItemMeta):
    """ Any object with a `__getitem__` method is a `SupportsGetItem`. """
    ...


class DifferTypes(ABC):
    # TODO Figure out standard way to centralize, reuse, & document TypeVars?
    """ Type vars to specify which dissecators.DifferenceBetween class's \
    methods' input arguments need to be the same type/class as which other(s).

    :param Diff: Any, _description_
    :param ToCompare: Any, _description_
    :param PartName: Hashable, _description_
    :param GetComparator: Callable[[ToCompare], Diff], _description_
    :param GetPartNames: Callable[[ToCompare], Iterable[PartName]], _description_
    :param GetSubcomparator: Callable[[ToCompare, PartName], Diff], _description_
    :return: _type_, _description_
    """
    Diff = TypeVar("Diff")
    ToCompare = TypeVar("ToCompare")
    PartName = TypeVar("ToSubCompare", bound=Hashable)
    GetComparator = TypeVar("Comparator", bound=Callable[[ToCompare], Diff])
    GetPartNames = TypeVar("GetPartNames",
                           bound=Callable[[ToCompare], Iterable[PartName]])
    GetSubcomparator = TypeVar("Subcomparator",
                               bound=Callable[[ToCompare, PartName], Diff])


class FinderTypes(ABC):
    # TODO Figure out standard way to centralize, reuse, & document TypeVars?
    """ Type vars to specify which attributes of finders.py classes' methods' \
    input arguments need to be the same type/class as which other(s).

    :param D: Any, default value to return if nothing was found
    :param I: Any, element in iter_over Iterable[I]
    :param M: Any, `modify(thing: I, ...) -> M` function output
    :param R: Any, `ready_if(..., *args: R)` function extra arguments
    :param X: Any, `modify(..., *args: X)` function extra arguments
    :param Modify: Callable[[I, tuple[X, ...]], M], modify function
    :param Ready: Callable[[M, tuple[R, ...]], bool], ready_if function
    :param Viable: Callable[[M], bool], is_viable function
    """
    D = TypeVar("D")
    I = TypeVar("I")
    M = TypeVar("M")
    R = TypeVar("R")
    X = TypeVar("X")
    Modify = TypeVar("Modify", bound=Callable[[I, tuple[X, ...]], M])
    Ready = TypeVar("Ready", bound=Callable[[M, tuple[R, ...]], Boolable])
    Viable = TypeVar("Viable", bound=Callable[[M], bool])


class SkipException(BaseException):
    ...


class ErrCatcher:
    def __init__(self, *catch: type[BaseException]) -> None:
        self.catch = catch


class IgnoreExceptions(ErrCatcher):
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
    def __init__(self, parent: "KeepTryingUntilNoErrors", *catch) -> None:
        super(SkipOrNot, self).__init__(*catch)
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


class KeepSkippingExceptions(ErrCatcher):
    def __init__(self, catch: Iterable[type[BaseException]] = list(),
                 is_done: bool = False) -> None:
        super(KeepSkippingExceptions, self).__init__(*catch)
        self.errors = list()
        self.is_done = is_done


class KeepTryingUntilNoErrors(KeepSkippingExceptions):
    def __init__(self, *catch: type[BaseException]) -> None:
        super(KeepTryingUntilNoErrors, self).__init__(catch)

    def __call__(self) -> Skip | DontSkip:
        skip_or_not = Skip if self.is_done else DontSkip
        return skip_or_not(self, *self.catch)

    def __enter__(self):
        """ Must be explicitly defined here (not only in a superclass) for \
            VSCode to realize that KeepTryingUntilNoErrors(...) returns an \
            instance of the KeepTryingUntilNoErrors class.

        :return: KeepTryingUntilNoErrors, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        return exc_type is SkipException


class FrozenFunction(Callable):
    """ Function wrapper that also stores some of its input parameters. """

    # Type variables for inner/wrapped/"frozen" function parameters/args
    _Pre = TypeVar("_Pre")  # Positional args to inject before _Inner args
    _Inner = TypeVar("_Inner")  # Positional args passed when executing
    _Post = TypeVar("_Post")  # Positional args to inject after _Inner args
    _Kw = TypeVar("_Kw")  # Keyword args
    _Ret = TypeVar("_Ret")  # "Frozen" function return value
    _Caller = Callable[[tuple[_Pre, ...], tuple[_Inner, ...],
                        tuple[_Post, ...]], _Ret]  # "Frozen" function itself

    def __call__(self, *args: _Inner, **kwargs: _Kw) -> _Ret:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input parameters
        """
        return self.inner(*args, **kwargs)

    def __init__(self, call: _Caller, pre: Iterable[_Pre] = list(),
                 post: Iterable[_Post] = list(), **kwargs: _Kw) -> None:
        """ "Freeze" a function with some parameters already defined to \
            call that function with those parameters later.

        :param call: Callable[[*pre, ..., *post], Any], the function to \
            wrap/"freeze" and then call/execute/"thaw" later.
        :param pre: Iterable of positional arguments to inject BEFORE the \
            `call` function's other positional input parameters.
        :param post: Iterable of positional arguments to inject AFTER the \
            `call` function's other positional input parameters.
        :param annotate: bool, True to preserve all public attributes of the \
            `call` function by copying them to the inner/wrapped/"frozen" one.
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
        kwargstrs = [f"{k}={v}" for k, v in kwargs.items()]
        argstr = ", ".join([*pre, "*args", *post, *kwargstrs])
        self.name = f"{nameof(self)}[{nameof(call)}({argstr}, **kwargs)]"

        self.inner = inner

    def expect(self, output: Any) -> "FrozenFunction":
        """ 
        :param output: Any, expected output returned from inner \
            wrapped/"frozen" function.
        :return: FrozenFunction[..., bool] that returns True if the inner \
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.inner(*args, **kwargs) == output
        return self.__class__(is_as_expected)

    def __repr__(self) -> str:
        """
        :return: str, annotated function header describing this FrozenFunction
        """
        return self.name


class AttributesOf:
    """ Select/iterate/copy the attributes of any object. """
    _T = TypeVar("_T")  # Type of object to copy attributes to

    # Filter to choose which attributes to copy or iterate over
    _SELECTOR = FrozenFunction[[Any], bool]

    def __init__(self, what: Any) -> None:
        """ 
        :param what: Any, the object to select/iterate/copy attributes of
        """
        self.names = set(dir(what))
        self.what = what

    def _attr_is_private(self, attr_name: str) -> bool:
        """
        :param attr_name: str naming an object attribute/method
        :return: bool, True if `attr_name` names a private attribute or \
            method (if it starts with '_'); otherwise False
        """
        return attr_name.startswith("_")

    def add_to(self, an_obj: _T, name_filters: Iterable[_SELECTOR] = list(),
               value_filters: Iterable[_SELECTOR] = list(),
               exclude: bool = False) -> _T:
        """ Copy attributes and their values into `an_obj`.

        :param an_obj: Any, object to add/copy attributes into.
        :param name_filters: Iterable[FrozenFunction[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param value_filters: Iterable[FrozenFunction[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :return: Any, an_obj with the specified attributes of this object.
        """
        for attr_name in self.select(name_filters, value_filters, exclude):
            setattr(an_obj, attr_name, getattr(self.what, attr_name))
        return an_obj

    def first_of(self, attr_names: Iterable[str], default: Any = None,
                 method_names: set[str] = set()) -> Any:
        """
        :param attr_names: Iterable[str], attributes to check this object for.
        :param default: Any, what to return if this object does not have any of \
            the attributes named in `attr_names`.
        :param method_names: set[str], the methods named in `attr_names` to call \
            before returning them.
        :return: Any, `default` if this object has no attribute named in \
            `attr_names`; else the found attribute, executed with no \
            parameters (if in `method_names`)
        """
        found_attr = default
        attrs = self.names.intersection(set(attr_names))
        match len(attrs):
            case 0:
                pass  # found_attr = default
            case 1:
                found_attr = getattr(self.what, attrs.pop())
            case _:
                iter_names = iter(list(attr_names))
                name = next(iter_names, None)
                while found_attr is default and name is not None:
                    if name in self.names:
                        found_attr = getattr(self.what, name)
                    name = next(iter_names, None)
        if name in method_names and callable(found_attr):
            found_attr = found_attr()
        return found_attr

    def methods(self) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over this object's methods (callable attributes).

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each method of this object.
        """
        return self.select(value_filters=[FrozenFunction(callable)])

    def method_names(self) -> list[str]:
        """
        :return: list[str], names of all methods (callable attributes) of \
            this object.
        """
        return [meth_name for meth_name, _ in self.methods()]

    def nested(self, *attribute_names: str) -> Any:
        """ `AttributesOf(an_obj).nested("first", "second", "third")` will \
        return `an_obj.first.second.third` if it exists or None otherwise.

        :param attribute_names: Iterable[str] of attribute names. The first \
                                names an attribute of an_obj; the second \
                                names an attribute of the first; etc. 
        :return: Any, the attribute of an attribute ... of an attribute of an_obj
        """
        attributes = list(attribute_names)  # TODO reversed(attribute_names) ?
        to_return = self.what
        while attributes and to_return is not None:
            to_return = getattr(to_return, attributes.pop(0), None)
        return to_return

    def private(self) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over this object's private attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each private attribute.
        """
        return self.select([self._attr_is_private])

    def public(self) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over this object's public attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each public attribute.
        """
        return self.select([self._attr_is_private], exclude=True)

    def public_names(self) -> list[str]:
        """
        :return: list[str], names of all public attributes of this object.
        """
        return [attr_name for attr_name, _ in self.public()]

    def select(self, name_filters: Iterable[_SELECTOR] = list(),
               value_filters: Iterable[_SELECTOR] = list(), exclude:
               bool = False) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over some of this object's attributes. 

        :param name_filters: Iterable[FrozenFunction[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param value_filters: Iterable[FrozenFunction[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each selected attribute.
        """
        def is_filtered(name: str, value: Any) -> bool:
            return all([nf(name) for nf in name_filters]) and \
                all([vf(value) for vf in value_filters])

        for name in self.names:
            attr = getattr(self.what, name)
            if is_filtered(name, attr) is not exclude:
                yield name, attr
