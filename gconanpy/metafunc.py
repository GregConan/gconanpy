#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-06-03
"""
# Import standard libraries
import abc
from collections.abc import (Callable, Collection, Generator,
                             Iterable, Mapping, MutableMapping)
from functools import reduce
import itertools
import more_itertools
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, Concatenate, ParamSpec, TypeVar
from typing_extensions import Self

# Import local custom libraries
try:
    from reg import DunderParser
    from trivial import call_method_of
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.reg import DunderParser
    from gconanpy.trivial import call_method_of

# Constants: TypeVars for...
M = TypeVar("M", bound=MutableMapping)  # ...combine_maps

# Purely "internal" errors only involving local data; ignorable in some cases
DATA_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)


def are_all_equal(comparables: Iterable, eq_meth: str | None = None,
                  reflexive: bool = False) -> bool:
    """ `are_all_equal([a, b, c, d, e])` means `a == b == c == d == e`.

    :param comparables: Iterable of objects to compare.
    :param eq_meth: str naming the method of every item in comparables to \
        call on every other item. `==` (`__eq__`) is the default comparison.
        `are_all_equal((a, b, c), eq_meth="isEqualTo")` means \
        `a.isEqualTo(b) and a.isEqualTo(c) and b.isEqualTo(c)`.
    :param reflexive: bool, True to compare each possible pair of objects in \
        `comparables` forwards and backwards.
        `are_all_equal({x, y}, eq_meth="is_like", reflexive=True)` means \
        `x.is_like(y) and y.is_like(x)`.
    :return: bool, True if calling the `eq_meth` method attribute of every \
        item in comparables on every other item always returns True; \
        otherwise False.
    """
    if not eq_meth:
        result = more_itertools.all_equal(comparables)
    else:
        are_both_equal = method(eq_meth)
        pair_up = itertools.permutations if reflexive \
            else itertools.combinations
        result = True
        for pair in pair_up(comparables, 2):
            if not are_both_equal(*pair):
                result = False
                break
    return result


def bool_pair_to_cases(cond1, cond2) -> int:  # Literal[0, 1, 2, 3]:
    return sum(which_of(cond1, cond2))


def combine_maps(maps: Iterable[M]) -> M:  # TODO Move to maptools?
    """ Merge dicts/maps. (NOTE: It's wild that this implementation works.)

    :param maps: Iterable[Mapping], maps to combine
    :return: Mapping combining all of the `maps` into one
    """
    return reduce(lambda x, y: x.update(y) or x, maps)


def combine_sets(sets: Iterable[set]) -> set:
    """ Merge sets.

    :param sets: Iterable[set] to merge/combine.
    :return: set, the union of all of the provided `sets`.
    """
    return reduce(set.union, sets)


def has_method(an_obj: Any, method_name: str) -> bool:
    """
    :param an_obj: Any
    :param method_name: str, name of a method that `an_obj` might have.
    :return: bool, True if `method_name` names a callable attribute \
        (method) of `an_obj`; otherwise False.
    """
    return callable(getattr(an_obj, method_name, None))


def make_metaclass(name: str, checker: Callable[[Any, Any], bool]) -> type:
    """ 
    :param name: str, name of the metaclass type to return.
    :param checker: Callable[[Any, Any], bool], function to call from the \
        `instancecheck`/`subclasscheck` methods of the returned metaclass.
    :return: type, metaclass with `checker` as its `__instancecheck__` and \
        `__subclasscheck__` methods.
    """
    return type(name, (type, ), {"__instancecheck__": checker,
                                 "__subclasscheck__": checker})


def metaclass_hasmethod(method_name: str, include: bool = True) -> type:
    """ _summary_ 

    :param method_name: str naming the method that the returned metaclass \
        type object will check whether objects have 
    :param include: bool, True to return a metaclass for a type WITH certain \
        methods; else (by default) False for a type WITHOUT certain methods
    :return: type, _description_
    """
    capitalized = DunderParser().pascalize(method_name)
    if include:
        def _check(cls, thing: Any) -> bool:
            return has_method(thing, method_name)
        verb = "Supports"
    else:
        def _check(cls, thing: Any) -> bool:
            return not has_method(thing, method_name)
        verb = "Lacks"
    return make_metaclass(f"{verb}{capitalized}Meta", _check)


def metaclass_issubclass(is_all_of: type | tuple[type, ...] = tuple(),
                         isnt_any_of: type | tuple[type, ...] = tuple(),
                         name: str | None = None) -> type:
    def _checker(is_a: Callable[[Any, type | tuple[type, ...]], bool]):
        def _check(cls, instance):
            return (not is_all_of or is_a(instance, is_all_of)
                    ) and not is_a(instance, isnt_any_of)
        return _check
    if not name:
        name = name_type_class(is_all_of, isnt_any_of)
    return type(name, (type, ), {"__instancecheck__": _checker(isinstance),
                                 "__subclasscheck__": _checker(issubclass)})


def method(method_name: str) -> Callable:
    """ Wrapper to retrieve a specific callable object attribute. 
    `method(method_name)(something, *args, **kwargs)` is the same as \
    `getattr(something, method_name)(*args, **kwargs)`.

    :param method_name: str naming the object method for the returned \
        wrapped function to call
    :return: Callable that runs the named method of its first input argument \
        and passes the rest of its input arguments to the method
    """

    def call_method(self: Any, *args: Any, **kwargs: Any):
        """
        :param self: Any, object with a method to call
        :param args: Iterable, positional arguments to call the method with
        :param kwargs: Mapping[str, Any], keyword arguments to call the \
            method with
        :return: Any, the output of calling the method of `self` with the \
            specified `args` and `kwargs` 
        """
        return call_method_of(self, method_name, *args, **kwargs)

    return call_method


def name_of(an_obj: Any) -> str:
    """ Get the `__name__` of an object or of its type/class.

    :param an_obj: Any
    :return: str naming an_obj, usually its type/class name.
    """
    return of_self_or_class(an_obj, "__name__")


def name_type_class(is_all_of: Any = tuple(), isnt_any_of: Any = tuple(),
                    max_n: int = 5, default: str = "NewTypeClass",
                    pos_verb: str = "Is", neg_verb: str = "IsNot",
                    get_name: Callable[[Any], str] = name_of) -> str:
    str_isall = "And".join(names_of(tuplify(is_all_of), max_n, get_name))
    str_isntany = "Or".join(names_of(tuplify(isnt_any_of), max_n, get_name))
    match bool_pair_to_cases(str_isall, str_isntany):
        case 0:
            name = default
        case 1:
            name = pos_verb + str_isall
        case 2:
            name = neg_verb + str_isntany
        case 3:
            name = f"{pos_verb}{str_isall}But{neg_verb}{str_isntany}"
    return name


def names_of(objects: Collection, max_n: int | None = None,
             get_name: Callable[[Any], str] = name_of) -> list[str]:
    """
    :param objects: Iterable of things to return the names of
    :param max_n: int | None, maximum number of names to return; by default, \
        this function will return all names
    :return: list[str], names of `max_n` (or all) `objects`
    """
    return [get_name(x) for x in objects] if max_n is None else \
        [get_name(x) for i, x in enumerate(objects) if i < max_n]


def of_self_or_class(an_obj: Any, attr_name: str) -> Any:
    """
    :param an_obj: Any, instance of type/class to get the attribute from
    :param attr_name: str naming the attribute to return
    :return: Any, the named attribute of either `an_obj` or its type/class
    """
    return getattr(an_obj, attr_name, getattr(type(an_obj), attr_name))


def parents_of(an_obj: Any) -> tuple[type, ...]:
    """ List the inheritance tree from `class object` to `an_obj`.

    :param an_obj: Any
    :return: tuple[*type], the method resolution order (`__mro__`) of \
        `an_obj` or of `type(an_obj)`.
    """
    return of_self_or_class(an_obj, "__mro__")


def pairs(*args: Any, **kwargs: Any
          ) -> Generator[tuple[Any, Any], None, None]:
    """ Iterate over pairs of items. Used for avoiding creating a dict only \
        to iterate over it, especially when some pairings are redundant.

    :param args: Iterable, arguments to iterate over first; each pair \
        iterated over will be two instances of each arg in `args`.
    :param kwargs: Mapping, arguments to iterate over second; each pair \
        iterated over will be each key-value mapping/pair in `kwargs`.

    :yield: Generator[tuple[Any, Any], None, None]
    """
    for arg in args:
        yield (arg, arg)
    for key, value in kwargs.items():
        yield (key, value)


def rename_keys(a_dict: dict[str, Any], **renamings: str) -> dict:
    """
    :param a_dict: dict with keys to rename
    :param renamings: Mapping[str, str] of old keys to their replacements
    :return: dict, `a_dict` after replacing the specified keys with their \
        new replacements specified in `renamings`
    """  # TODO Move to maptools?
    for old_name, new_name in renamings.items():
        a_dict[new_name] = a_dict.pop(old_name)
    return a_dict


def tuplify(an_obj: Any) -> tuple:
    """ 
    :param an_obj: Any, object to convert into a tuple.
    :return: tuple, either `an_obj` AS a tuple if `tuple(an_obj)` works or \
        `an_obj` IN a single-item tuple if it doesn't.
    """
    try:
        return tuple(an_obj)
    except TypeError:
        return (an_obj, )


def which_of(*conditions: bool) -> set[int]:
    """
    :param conditions: Iterable[Boolable] of items to filter
    :return: set[int], the indices of every truthy item in `conditions`
    """
    return set((i for i, cond in enumerate(conditions) if cond))


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
