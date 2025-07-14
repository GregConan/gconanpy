#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-07-13
"""
# Import standard libraries
import abc
from collections.abc import Callable, Collection, Iterable, Mapping
from functools import wraps
# from operator import attrgetter, methodcaller  # TODO?
from typing import (Any, Concatenate, get_args, Literal,
                    ParamSpec, Protocol, runtime_checkable, TypeVar)
from typing_extensions import Self

# Import local custom libraries
try:
    from ..mapping.map_funcs import lazysetdefault
    from .funcs import DATA_ERRORS, has_method, make_metaclass, \
        metaclass_hasmethod, metaclass_issubclass, name_type_class
    from ..reg import DunderParser
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.meta.funcs import DATA_ERRORS, has_method, make_metaclass, \
        metaclass_hasmethod, metaclass_issubclass, name_type_class
    from gconanpy.reg import DunderParser


class ClassWrapper:
    # MethodWrapper type hint vars for return_as_* methods
    _P = ParamSpec("_P")  # _P means (*args, **kwargs)
    _T = TypeVar("_T")  # _T means self.__class__ means type(self)
    UnwrappedMethod = Callable[Concatenate[_T, _P], Any]
    WrappedMethod = Callable[Concatenate[_T, _P], _T]

    # New type hint variables for other ClassWrapper methods
    _Super = TypeVar("_Super")
    _S = TypeVar("_S")
    ASSIGNED = ("__doc__", "__name__", "__text_signature__")

    def __init__(self, superclass: type[_Super]) -> None:
        self.superclass = superclass
        self.attr_names = dir(superclass)

    def _wrap_method_of(self, subclass: type[_S], func: Callable):
        @wraps(func, assigned=self.ASSIGNED)
        def inner(*args, **kwargs):
            result = func(*args, **kwargs)
            return result if not isinstance(result, self.superclass) \
                else subclass(result)  # type: ignore

        # setattr(inner, "__objclass__", subclass)
        setattr(inner, "__self__", subclass)
        inner.__qualname__ = f"{subclass.__name__}.{inner.__name__}"
        return inner

    def class_decorator(self, subclass: type[_S]) -> type[_S]:
        self.subclass = subclass
        for attr_name in self.attr_names:
            if not attr_name.startswith("__"):
                superattr = getattr(self.superclass, attr_name, None)
                subattr = getattr(subclass, attr_name, None)
                if callable(superattr) and callable(subattr):
                    setattr(subclass, attr_name,
                            self._wrap_method_of(subclass, superattr))
        return subclass

    @classmethod
    def return_as_its_class(cls, meth: UnwrappedMethod) -> WrappedMethod:
        S = TypeVar("S", bound=HasClass)

        @wraps(meth, assigned=cls.ASSIGNED)
        def inner(self: S, *args: Any, **kwargs: Any) -> S:
            return self.__class__(meth(self, *args, **kwargs))

        # TODO
        # setattr(inner, "__self__", self.subclass)
        # inner.__qualname__ = f"{self.subclass.__name__}.{inner.__name__}"
        # inner.__annotations__["return"] = self.subclass
        return inner

    @classmethod
    def return_self_if_no_value(cls, meth: WrappedMethod) -> WrappedMethod:
        S = TypeVar("S")

        @wraps(meth, assigned=cls.ASSIGNED)
        def inner(self: S, value: Boolable) -> S:
            return meth(self, value) if value else self
        return inner


class BoolableMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for Boolable class creation. """
    def __instancecheck__(cls, instance: Any) -> bool:
        try:
            bool(instance)
            return True
        except (TypeError, ValueError):
            return False

    def __subclasscheck__(cls, subclass: type) -> bool:
        return has_method(subclass, "__bool__") \
            or has_method(subclass, "__len__")


class Boolable(metaclass=BoolableMeta):
    """ Any object that you can call `bool()` on is a `Boolable`. """


class MultiTypeMeta(type, abc.ABC):
    _TypeArgs = type | tuple[type, ...]
    _TypeChecker = Callable[[Any, _TypeArgs], bool]

    IS_A: _TypeArgs = (object, )
    ISNT_A: _TypeArgs = tuple()

    @staticmethod
    def check(thing: Any, is_if: _TypeChecker,
              is_a: _TypeArgs = (object, ),
              isnt_a: _TypeArgs = tuple()) -> bool:
        return is_if(thing, is_a) and not is_if(thing, isnt_a)

    def __instancecheck__(cls, instance: Any) -> bool:
        return cls.check(instance, isinstance, cls.IS_A, cls.ISNT_A)

    def __subclasscheck__(cls, subclass: Any) -> bool:
        return cls.check(subclass, issubclass, cls.IS_A, cls.ISNT_A)


class BytesOrStrMeta(MultiTypeMeta):
    IS_A = (bytes, str)


class BytesOrStr(metaclass=BytesOrStrMeta):
    """ Any instance of `bytes` or `str` is a `BytesOrStr` instance. """


class HasClass(abc.ABC):
    __class__: Callable[[Any], Any]


class HasSlots(abc.ABC):
    __slots__: tuple


@runtime_checkable
class MutableItemStore(Protocol):
    """
    Any Container that can get, set, and delete items is a MutableItemStore.
    """

    def __contains__(self, key, /) -> bool: ...
    def __delitem__(self, key, /) -> None: ...
    def __getitem__(self, key, /) -> Any: ...
    def __setitem__(self, key, value, /) -> None: ...


class NonIterable(metaclass=metaclass_hasmethod("__iter__", include=False)):
    """ Any object that isn't an Iterable is a NonIterable. """


class PureIterable(metaclass=metaclass_issubclass(
        is_all_of=(Iterable, ), isnt_any_of=(str, bytes, Mapping),
        name="PureIterableMeta")):
    """ Iterables that aren't strings, bytes, or Mappings are "Pure." """


@runtime_checkable
class Updatable(Protocol):
    """ Any object or class with an `update` method is an `Updatable`.
        `dict`, `MutableMapping`, and `set` are each `Updatable`. """
    update: Callable


class TypeFactory:  # NOTE: Work-in-progress
    @classmethod
    def _has_all(cls, an_obj: Any, method_names: Collection[str]) -> bool:
        for method_name in method_names:
            if not has_method(an_obj, method_name):
                return False
        return True

    @classmethod
    def _lacks_all(cls, an_obj: Any, method_names: Collection[str]) -> bool:
        for method_name in method_names:
            if has_method(an_obj, method_name):
                return False
        return True

    @classmethod
    def hasmethods(cls, all_of: Any = (), none_of: Any = (),
                   altcond: Callable[[Any], bool] | None = None,
                   **kwargs: Any) -> type:
        class_name = name_type_class(all_of, none_of,
                                     get_name=DunderParser().pascalize,
                                     pos_verb="Supports", neg_verb="Lacks")

        def _check_methods(_, thing: Any) -> bool:
            return cls._has_all(thing, all_of) and \
                cls._lacks_all(thing, none_of)

        if altcond:
            def _check(_, thing: Any) -> bool:
                return altcond(thing) and _check_methods(_, thing)
        else:
            _check = _check_methods

        return type(class_name, (type, ), {"metaclass": make_metaclass(
            "MethodMetaclass", _check), **kwargs})


class TimeSpec(dict[str, int]):

    # Names of valid TimeSpec options, each corresponding to a duration unit
    UNIT = Literal["auto", "nanoseconds", "microseconds", "milliseconds",
                   "seconds", "minutes", "hours"]

    # The number of each UNIT per the next unit:
    #   1ns, 1000ns/us, 1000us/ms, 1000ms/sec, 60sec/min, 60min/hr
    OFFSETS = (1, 1000, 1000, 1000, 60, 60)

    def __init__(self) -> None:
        super().__init__()
        units = get_args(self.UNIT)[1:]  # List all time units; exclude "auto"
        self[units[0]] = self.OFFSETS[0]  # Initialize for iteration
        for i in range(1, len(self.OFFSETS)):  # Calculate unit ratios/offsets
            self[units[i]] = self[units[i-1]] * self.OFFSETS[i]


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
    def __enter__(self) -> Self:
        return self

    # TODO Does this stop SysExit and pdb exit from propagating? It shouldn't!
    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        """ Exit the runtime context related to this object. The parameters \
            describe the exception that caused the context to be exited. If \
            the context was exited without an exception, all three arguments \
            will be None.

        Note that __exit__() methods should not reraise the passed-in \
        exception; this is the caller's responsibility.

        Docstring shamelessly stolen from \
        https://docs.python.org/3/reference/datamodel.html#object.__exit__

        :param exc_type: type[BaseException] | None, the `type` of exception \
            caught (or None if no exception occurred)
        :return: bool, True if no exception occurred or if an exception was \
            caught and suppressed; else False to raise the exception
        """
        return (not self.catch) or (exc_type in self.catch)


class SkipOrNot(IgnoreExceptions, abc.ABC):
    def __init__(self, parent: "KeepTryingUntilNoErrors", *catch) -> None:
        super(SkipOrNot, self).__init__(*catch)
        self.parent = parent


class Skip(SkipOrNot):
    def __enter__(self):
        raise SkipException


class DontSkip(SkipOrNot):
    def __exit__(self, exc_type: type[BaseException] | None = None,
                 exc_val: BaseException | None = None, _: Any = None) -> bool:
        """ Upon exiting a code block, inform the parent \
            `KeepSkippingExceptions` context manager whether the code block \
            completed successfully or raised an exception.

        :param exc_type: type[BaseException] | None,_description_, defaults to None
        :param exc_val: BaseException | None,_description_, defaults to None
        :param _: Any,_description_, defaults to None
        :return: bool, _description_
        """
        if exc_val is None:
            self.parent.is_done = True
        else:
            self.parent.errors.append(exc_val)
        return super(DontSkip, self).__exit__(exc_type)


class KeepSkippingExceptions(ErrCatcher):
    def __init__(self, catch: Iterable[type[BaseException]] = list(),
                 is_done: bool = False) -> None:
        """
        :param catch: Iterable[type[BaseException]] to catch and skip; \
            defaults to `ErrCatcher.DEFAULT_CATCH` (`DATA_ERRORS`).
        :param is_done: bool, True to skip any remaining code blocks; \
            else False to execute them 
        """
        super(KeepSkippingExceptions, self).__init__(*catch)
        self.errors: list[BaseException] = list()
        self.is_done = is_done


class KeepTryingUntilNoErrors(KeepSkippingExceptions):
    def __init__(self, *catch: type[BaseException]) -> None:
        """
        :param catch: Iterable[type[BaseException]] to catch and skip. 
        """
        super(KeepTryingUntilNoErrors, self).__init__(catch)

    def __call__(self) -> SkipOrNot:
        """ Execute the following code block unless a previous code block \
            executed successfully (without raising an exception).

        :return: SkipOrNot, Skip to ignore the following code block; else \
            DontSkip to execute it.
        """
        skip_or_not = Skip if self.is_done else DontSkip
        return skip_or_not(self, *self.catch)

    def __enter__(self) -> Self:
        """ Must be explicitly defined here (not only in a superclass) for \
            VSCode to realize that KeepTryingUntilNoErrors(...) returns an \
            instance of the KeepTryingUntilNoErrors class.

        :return: KeepTryingUntilNoErrors, self.
        """
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None,
                 *_: Any) -> bool:
        return exc_type is SkipException
