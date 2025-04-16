#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-04-15
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Generator, Hashable, Iterable
# import datetime as dt
# import inspect
# from makefun import create_function, create_wrapper, with_signature, wraps
import pdb
from typing import Any, TypeVar  # Generic, ParamSpec,


# Constants: Names of methods not to overwrite when wrapping an object
ESSENTIALS = {f"__{attr}__" for attr in
              ("class", "class_getitem", "delattr", "getattribute",  # "doc",
               "hash", "init", "init_subclass", "new", "reduce",
               "reduce_ex", "setattr", "subclasshook")}


def find_an_attr_in(attrs_of: Any, attr_names: Iterable[str], default:
                    Any = None, method_names: set[str] = set()) -> Any:
    """
    :param attrs_of: Any, object to find an attribute of.
    :param attr_names: Iterable[str] of attributes to check `attrs_of` for.
    :param default: Any, what to return if `attrs_of` does not have any of \
        the attributes named in `attr_names`.
    :param method_names: set[str], the methods named in `attr_names` to call \
        before returning them.
    :return: Any, an attribute of `attrs_of` (if found) executed with no \
        parameters (if in `method_names`), or `default` if not found.
    """
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


def negate(a_func: Callable[..., bool]) -> Callable[..., bool]:
    """ Invert a boolean function by wrapping it.

    :param a_func: Callable[..., bool]
    :return: Callable[..., bool] returning the exact opposite of `a_func`: \
        `negate(a_func)` returns True if `a_func` returns False, & vice versa.
    """
    def negated_function(*args, **kwargs) -> bool:
        return not a_func(*args, **kwargs)
    return negated_function


def to_class(name: str, an_obj: Any, **kwargs):  # TODO Remove
    return type(name, (type(an_obj), ), kwargs)


def wrap_with_params(call: Callable, *args: Any, **kwargs: Any) -> Callable:
    # TODO Replace this (in cli.py) with FrozenFunction
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


class BoolableMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for Boolable class creation.
    """
    def __instancecheck__(cls, instance):
        try:
            bool(instance)
            return True
        except (TypeError, ValueError):
            return False

    def __subclasscheck__(cls, subclass):
        methods = ("__bool__", "__len__")
        return find_an_attr_in(subclass, methods, None, set(methods))


class Boolable(metaclass=BoolableMeta):
    """ Any object that you can call `bool()` on is a `Boolable`. """
    ...


class SupportsGetItemMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for SupportsGetItem class creation.
    """
    def __instancecheck__(cls, instance):
        return has_method(instance, "__getitem__")

    def __subclasscheck__(cls, subclass):
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
    :param F: Any, `found_if(..., *args: F)` function extra arguments
    :param M: Any, `modify(thing: S, ...) -> M` function output
    :param R: Any, `ready_if(..., *args: R)` function extra arguments
    :param S: Any, element in iter_over Sequence[S]
    :param T: Any, input argument to "whittle down"
    :param X: Any, `modify(..., *args: X)` function extra arguments
    :param W: Any, `whittle(thing: W, ...)` function argument (?)
    :param Found: Callable[[S, tuple[F, ...]], bool], found_if function
    :param Modify: Callable[[S, tuple[X, ...]], M], modify function
    :param Viable: Callable[[M], bool], is_viable function
    """
    D = TypeVar("D")
    F = TypeVar("F")
    I = TypeVar("I")
    M = TypeVar("M")
    R = TypeVar("R")
    T = TypeVar("T")
    X = TypeVar("X")
    Errors = (AttributeError, IndexError, KeyError, TypeError, ValueError)
    Modify = TypeVar("Modify", bound=Callable[[I, tuple[X, ...]], M])
    Ready = TypeVar("Ready", bound=Callable[[M, tuple[R, ...]], Boolable])
    Viable = TypeVar("Viable", bound=Callable[[M], bool])
    Whittler = TypeVar("Whittler", bound=Callable[[T, I, tuple[X, ...]], T])


class CanIgnoreCertainErrors:
    IGNORABLES = (AttributeError, IndexError, KeyError, TypeError, ValueError)


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
                 post: Iterable[_Post] = list(),
                 annotate: bool = False, **kwargs: _Kw) -> None:
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
        if annotate:
            inner = AttributesOf(call).add_to(inner, ESSENTIALS.__contains__,
                                              exclude=True)

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
        self.names = dir(what)
        self.what = what

    def _attr_is_private(self, attr_name: str) -> bool:
        """
        :param attr_name: str naming an object attribute/method
        :return: bool, True if `attr_name` names a private attribute or \
            method (if it starts with '_'); otherwise False
        """
        return attr_name.startswith("_")

    def add_to(self, an_obj: _T, filter_on: _SELECTOR,
               exclude: bool = False) -> _T:
        """ Copy attributes and their values into `an_obj`.

        :param an_obj: Any, object to add/copy attributes into.
        :param filter_on: FrozenFunction[[Any], bool] to run on the name of \
            every attribute of this object, to check whether to add/copy it.
        :param exclude: bool, False to INclude all attributes for which the \
            filter_on function returns True; else False to EXclude them.
        :return: Any, an_obj with the specified attributes of this object.
        """
        for attr_name in self.select(filter_on, exclude):
            setattr(an_obj, attr_name, getattr(self.what, attr_name))
        return an_obj

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
        return self.select(self._attr_is_private)

    def public(self) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over this object's public attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each public attribute.
        """
        return self.select(self._attr_is_private, exclude=True)

    def public_names(self) -> list[str]:
        """
        :return: list[str], names of all public attributes of this object.
        """
        return [attr_name for attr_name, _ in self.public()]

    def select(self, filter_on: _SELECTOR, exclude: bool = False
               ) -> Generator[tuple[str, Any], None, None]:
        """ Iterate over some of this object's attributes. 

        :param filter_on: FrozenFunction[[Any], bool] to run on the name of \
            every attribute of this object, to check whether the returned \
            generator function should include that attribute or skip it
        :param exclude: bool, False to INclude all attributes for which the \
            filter_on function returns True; else False to EXclude them.
        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each selected attribute.
        """
        if exclude:
            filter_on = negate(filter_on)
        for attr_name in self.names:
            if filter_on(attr_name):
                yield attr_name, getattr(self.what, attr_name)
