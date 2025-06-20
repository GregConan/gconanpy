#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-06-20
"""
# Import standard libraries
import abc
from collections.abc import (Callable, Collection, Generator,
                             Iterable, Mapping, MutableMapping)
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, Concatenate, ParamSpec, TypeVar
from typing_extensions import Self

# Import local custom libraries
try:
    from funcs import DATA_ERRORS, has_method, make_metaclass, \
        metaclass_hasmethod, metaclass_issubclass, name_of, name_type_class
    from ..reg import DunderParser
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.meta.funcs import DATA_ERRORS, has_method, make_metaclass, \
        metaclass_hasmethod, metaclass_issubclass, name_of, name_type_class
    from gconanpy.reg import DunderParser


class MethodWrapper:
    _P = ParamSpec("_P")  # _P means (*args, **kwargs)
    _T = TypeVar("_T")  # _T means self.__class__ means type(self)
    UnwrappedMethod = Callable[Concatenate[_T, _P], Any]
    WrappedMethod = Callable[Concatenate[_T, _P], _T]

    @staticmethod
    def return_as_its_class(meth: UnwrappedMethod) -> WrappedMethod:
        S = TypeVar("S", bound=HasClass)

        def inner(self: S, *args: Any, **kwargs: Any) -> S:
            return self.__class__(meth(self, *args, **kwargs))
        return inner

    @staticmethod
    def return_self_if_no_value(meth: WrappedMethod) -> WrappedMethod:
        S = TypeVar("S")

        def inner(self: S, value: Boolable) -> S:
            return meth(self, value) if value else self
        return inner


class WrapFunction:  # (Callable):
    """ Function wrapper that also stores some of its input parameters. """

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """ Call/execute/unwrap/"thaw" the wrapped/"frozen" function.

        :return: Any, the output of calling the wrapped/"frozen" function \
            with the specified input parameters
        """
        return self.inner(*args, **kwargs)

    def __init__(self, call: Callable, pre: Iterable = list(),
                 post: Iterable = list(), **kwargs: Any) -> None:
        """ Wrap/"freeze" a function with some parameters already defined \
            to call that function with those parameters later.

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
        # TODO Use stringify_map(kwargs) and stringify_iter(call, pre, post) ?
        kwargstrs = [f"{k}={v}" for k, v in kwargs.items()]
        self.stringified = f"{name_of(self)}(call={name_of(call)}, " \
            f"pre={pre}, post={post}, {', '.join(kwargstrs)})"

        self.inner = inner

    def __repr__(self) -> str:
        """
        :return: str, annotated function header describing this WrapFunction.
        """
        return self.stringified

    def expect(self, output: Any) -> Self:
        """ 
        :param output: Any, expected output returned from inner \
            wrapped/"frozen" function.
        :return: WrapFunction[..., bool] that returns True if the inner \
            wrapped/"frozen" function returns `output` and False otherwise.
        """
        def is_as_expected(*args, **kwargs) -> bool:
            return self.inner(*args, **kwargs) == output
        return self.__class__(is_as_expected)

    def foreach(self, *objects: Any) -> Generator[Any, None, None]:
        """ Call the wrapped/"frozen" function with its specified parameters \
            on every object in `objects`. Iterate lazily; only call/execute \
            the wrapped function on each object at the moment of retrieval.

        :yield: Generator[Any, None, None], what the wrapped/"frozen" \
            function returns when given each object in `objects` as an input.
        """
        for an_obj in objects:
            yield self.inner(an_obj)


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


class BytesOrStrMeta(type):
    _Checker = Callable[[Any, type | tuple[type, ...]], bool]

    def _check(cls, thing: Any, check: _Checker) -> bool:
        return check(thing, (bytes, str))

    def __instancecheck__(cls, instance: Any) -> bool:
        return cls._check(instance, isinstance)

    def __subclasscheck__(cls, subclass: Any) -> bool:
        return cls._check(subclass, issubclass)


class BytesOrStr(metaclass=BytesOrStrMeta):
    """ Any instance of `bytes` or `str` is a `BytesOrStr` instance. """


class HasClass(abc.ABC):
    __class__: Callable[[Any], Any]


class HasSlots(abc.ABC):
    __slots__: tuple


class NonIterable(metaclass=metaclass_hasmethod("__iter__", include=False)):
    """ Any object that isn't an Iterable is a NonIterable. """


class PureIterable(metaclass=metaclass_issubclass(
        is_all_of=(Iterable, ), isnt_any_of=(str, bytes, Mapping),
        name="PureIterableMeta")):
    """ Iterables that aren't strings, bytes, or Mappings are "Pure." """


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
