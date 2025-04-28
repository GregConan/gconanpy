#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-04-27
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Generator, Iterable, Mapping
from functools import reduce
import itertools
from typing import Any, Literal, TypeVar

# Constants: TypeVars for...
M = TypeVar("M", bound=Mapping)  # ...combine_maps
T = TypeVar("T")  # ...add_attributes_to

# Purely "internal" errors only involving local data; ignorable in some cases
DATA_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)
# TODO Does this include SysExit and pdb exit? It shouldn't!

# Names of methods not to overwrite when wrapping an object
ESSENTIALS = {f"__{attr}__" for attr in
              ("class", "class_getitem", "delattr", "getattribute",  # "doc",
               "hash", "init", "init_subclass", "new", "reduce",
               "reduce_ex", "setattr", "subclasshook")}


def add_attributes_to(an_obj: T, **attributes: Any) -> T:
    """
    :param an_obj: Any, object to add attributes to
    :return: Any, `an_obj` now with `attributes` added
    """
    for attr_name, attr_value in attributes.items():
        setattr(an_obj, attr_name, attr_value)
    return an_obj


def are_all_equal(comparables: Iterable, equality: str | None = None) -> bool:
    """ `are_all_equal([x, y, z])` means `x == y == z`.
    `are_all_equal({x, y}, "is_like")` means `x.is_like(y) and y.is_like(x)`.

    :param comparables: Iterable of objects to compare.
    :param equality: str naming the method of every item in comparables to \
        call on every other item. `==` (`__eq__`) is the default comparison.
    :return: bool, True if calling the `equality` method attribute of every \
        item in comparables on every other item always returns True; \
        otherwise False.
    """
    are_same = None
    are_both_equal = method(equality) if equality else (lambda x, y: x == y)
    combos_iter = itertools.combinations(comparables, 2)
    while are_same is None:
        next_pair = next(combos_iter, None)
        if next_pair is None:
            are_same = True
        elif not are_both_equal(*next_pair):
            are_same = False
    return are_same


def combine_maps(maps: Iterable[M]) -> M:
    return reduce(lambda x, y: x.update(y) or x, maps)


def combine_sets(sets: Iterable[set]) -> set:
    return reduce(set.union, sets)


def has_method(an_obj: Any, method_name: str) -> bool:
    """
    :param an_obj: Any
    :param method_name: str, name of a method that `an_obj` might have.
    :return: bool, True if `method_name` names a callable attribute \
        (method) of `an_obj`; otherwise False.
    """
    return callable(getattr(an_obj, method_name, None))


def method(method_name: str) -> Callable:
    """ Wrapper to retrieve a specific callable object attribute. 
    `method(method_name)(something, *args, **kwargs)` is the same as \
    `getattr(something, method_name)(*args, **kwargs)`.

    :param method_name: str naming the object method for the returned \
        wrapped function to call
    :return: Callable that runs the named method of its first input argument \
        and passes the rest of its input arguments to the method
    """

    def call_method_of(self, *args, **kwargs):
        """
        :param self: Any, object with a method to call
        :param args: Iterable, positional arguments to call the method with
        :param kwargs: Mapping[str, Any], keyword arguments to call the \
            method with
        :return: Any, the output of calling the method of `self` with the \
            specified `args` and `kwargs` 
        """
        return getattr(self, method_name)(*args, **kwargs)
    return call_method_of


def nameof(an_obj: Any) -> str:
    """ Get the `__name__` of an object or of its type/class.

    :param an_obj: Any
    :return: str naming an_obj, usually its type/class name.
    """
    return getattr(an_obj, "__name__", type(an_obj).__name__)


def name_attributes_of(*objects: Any) -> set[str]:
    attr_names = set()
    for an_obj in objects:
        attr_names.update(dir(an_obj))
    return attr_names


class FrozenFunction(Callable):
    """ Function wrapper that also stores some of its input parameters. """

    # Type variables for inner/wrapped/"frozen" function parameters/args
    Pre = TypeVar("Pre")  # Positional args to inject BEFORE Inner args
    Inner = TypeVar("Inner")  # Positional args passed when executing
    Post = TypeVar("Post")  # Positional args to inject AFTER Inner args
    Kw = TypeVar("Kw")  # Keyword args
    Ret = TypeVar("Ret")  # "Frozen" function's return value
    Caller = Callable[[tuple[Pre, ...], tuple[Inner, ...],
                       tuple[Post, ...]], Ret]  # "Frozen" function itself

    def __call__(self, *args: Inner, **kwargs: Kw) -> Ret:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input parameters
        """
        return self.inner(*args, **kwargs)

    def __init__(self, call: Caller, pre: Iterable[Pre] = list(),
                 post: Iterable[Post] = list(), **kwargs: Kw) -> None:
        """ "Freeze" a function with some parameters already defined to \
            call that function with those parameters later.

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


class FilterAttributes:
    _SELECTOR = Callable[[Any], bool]
    _SELECTORS = list[_SELECTOR]
    _WHICH = Literal["names"] | Literal["values"]

    FilterFunction = Callable[[str, Any], bool]
    selectors: dict[_WHICH, _SELECTORS]

    def __init__(self, if_names: _SELECTORS = list(),
                 if_values: _SELECTORS = list()) -> None:
        """ _summary_ 

        :param if_names: list[Callable[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param if_values: list[Callable[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        """
        self.selectors = dict(names=if_names, values=if_values)

    def add(self, which: _WHICH, func: FrozenFunction.Caller,
            pre: Iterable[FrozenFunction.Pre] = list(),
            post: Iterable[FrozenFunction.Post] = list(),
            **kwargs: FrozenFunction.Kw) -> None:
        self.selectors[which].append(FrozenFunction(func, pre, post,
                                                    **kwargs))

    def build(self) -> FilterFunction:
        """
        :return: Callable[[str, Any], bool] that returns True if the `str` \
            argument passes all of the name filters and the `Any` \
            argument passes all of the value filters, else False
        """
        @staticmethod
        def is_filtered(name: str, value: Any) -> bool:
            passed = True
            for filterable, filters in ((name, self.selectors["names"]),
                                        (value, self.selectors["values"])):
                filterator = iter(filters)
                next_filter = next(filterator, None)
                while passed and next_filter is not None:
                    passed = passed and next_filter(filterable)
                    next_filter = next(filterator, None)
            return passed
        return is_filtered


class AttributesOf:
    """ Select/iterate/copy the attributes of any object. """
    _T = TypeVar("_T")  # Type of object to copy attributes to

    # Filters to choose which attributes to copy or iterate over
    addFilter = FilterAttributes
    METHOD_FILTERS: FilterAttributes.FilterFunction = \
        FilterAttributes(if_values=[callable]).build()

    def __init__(self, what: Any) -> None:
        """ 
        :param what: Any, the object to select/iterate/copy attributes of
        """
        self.names = name_attributes_of(what)  # set(dir(what))
        self.what = what

    def _attr_is_private(self, attr_name: str) -> bool:
        """
        :param attr_name: str naming an object attribute/method
        :return: bool, True if `attr_name` names a private attribute or \
            method (if it starts with '_'); otherwise False
        """
        return attr_name.startswith("_")

    def add_to(self, an_obj: _T, filter_if: FilterAttributes.FilterFunction,
               exclude: bool = False) -> _T:
        """ Copy attributes and their values into `an_obj`.

        :param an_obj: Any, object to add/copy attributes into.
        :param filter_if: Callable[[str, Any], bool] that returns True if \
            the `str` argument passes all of the name filters and \
            the `Any` argument passes all of the value filters, else False
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :return: Any, an_obj with the specified attributes of this object.
        """
        for attr_name in self.select(filter_if, exclude):
            setattr(an_obj, attr_name, getattr(self.what, attr_name))
        return an_obj

    def but_not(self, *others: Any) -> set[str]:
        return set(self.names) - name_attributes_of(others)

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

    def items(self):
        return self.select()

    def methods(self) -> Generator[tuple[str, Callable], None, None]:
        """ Iterate over this object's methods (callable attributes).

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each method of this object.
        """
        return self.select(filter_if=self.METHOD_FILTERS)

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

    def select(self, filter_if: FilterAttributes.FilterFunction,
               exclude: bool = False) -> Generator[tuple[str, Any],
                                                   None, None]:
        """ Iterate over some of this object's attributes. 

        :param filter_if: Callable[[str, Any], bool] that returns True if \
            the `str` argument passes all of the name filters and \
            the `Any` argument passes all of the value filters, else False
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each selected attribute.
        """
        for name in self.names:
            attr = getattr(self.what, name)
            if filter_if(name, attr) is not exclude:
                yield name, attr


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


def parents_of(an_obj: Any) -> tuple[type, ...]:
    return getattr(an_obj, "__mro__", type(an_obj).__mro__)


class Boolable(metaclass=BoolableMeta):
    """ Any object that you can call `bool()` on is a `Boolable`. """


class PureIterableMeta(type):
    EXCLUDES = (str, bytes, Mapping)

    def __instancecheck__(self, an_obj: Any) -> bool:
        return isinstance(an_obj, Iterable) and \
            not isinstance(an_obj, Mapping) and \
            not isinstance(an_obj, str) and \
            not isinstance(an_obj, bytes)

    def __subclasscheck__(self, subclass):
        return not issubclass(subclass, self.EXCLUDES)


class NonIterableMeta(type):

    def _check(self, subclass):
        return not has_method(subclass, "__iter__")

    __subclasscheck__ = _check
    __instancecheck__ = _check


class NonIterable(metaclass=NonIterableMeta):
    """ Any object that isn't an Iterable is a NonIterable. """


class PureIterable(metaclass=PureIterableMeta):
    """ Any Iterable is a PureIterable unless it is a str, bytes,
        or Mapping. """


class SupportsGetItemMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for SupportsGetItem class creation.
    """
    def __instancecheck__(cls, instance: Any) -> bool:
        # TODO try: instance[0]; KeyError: return True; AttributeError: False?
        return has_method(instance, "__getitem__")

    def __subclasscheck__(cls, subclass: type) -> bool:
        return has_method(subclass, "__getitem__")


class SupportsGetItem(metaclass=SupportsGetItemMeta):
    """ Any object with a `__getitem__` method is a `SupportsGetItem`. """


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
    Modify = Callable[[I, tuple[X, ...]], M]
    Ready = Callable[[M, tuple[R, ...]], Boolable]
    Viable = Callable[[M], bool]


class SkipException(BaseException):
    """ Exception raised by ErrCatcher subclasses to skip a block of code. """


class ErrCatcher:
    DEFAULT_CATCH = DATA_ERRORS

    def __init__(self, *catch: type[BaseException]) -> None:
        """
        :param catch: Iterable[type[BaseException]], errors and exceptions \
            to catch and suppress/skip/ignore or handle. If no errors or \
            exceptions are specifically provided, then by default, only the \
            errors and exceptions in the `DEFAULT_CATCH` class variable will \
            be caught.
        """
        self.catch = catch if catch else self.DEFAULT_CATCH


class IgnoreExceptions(ErrCatcher):
    def __enter__(self):
        """ 
        :return: IgnoreExceptions, self.
        """
        return self

    # TODO Does this stop SysExit and pdb exit from propagating? It shouldn't!
    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        """ Exit the runtime context related to this object. The parameters \
            describe the exception that caused the context to be exited. If \
            the context was exited without an exception, all three arguments \
            will be None.

        If an exception is supplied, and the method wishes to suppress the \
        exception (i.e., prevent it from being propagated), it should return \
        a true value. Otherwise, the exception will be processed normally \
        upon exit from this method.

        Note that __exit__() methods should not reraise the passed-in \
        exception; this is the caller’s responsibility.

        Docstring shamelessly stolen from \
        https://docs.python.org/3/reference/datamodel.html#object.__exit__

        :param exc_type: type[BaseException] | None,_description_, defaults to None
        :return: bool, _description_
        """
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
