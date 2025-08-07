#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-08-07
"""
# Import standard libraries
import abc
import builtins
from collections.abc import Callable, Collection, Container, \
    Hashable, Iterable, Iterator, Mapping, Sequence
import operator
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, get_args, Literal, Protocol, NamedTuple, \
    no_type_check, overload, runtime_checkable, SupportsFloat, \
    TypeVar, TYPE_CHECKING
from typing_extensions import Self


if TYPE_CHECKING:
    from _typeshed import SupportsItemAccess
else:  # Can't import _typeshed at runtime, so define its imports manually
    class SupportsItemAccess:
        def __contains__(self, x, /): ...
        def __getitem__(self, key, /): ...
        def __setitem__(self, key, value, /): ...
        def __delitem__(self, key, /): ...

# Purely "internal" errors only involving local data; ignorable in some cases
DATA_ERRORS = (AttributeError, IndexError, KeyError, TypeError, ValueError)

# TypeVars for Lazily class methods' input parameters
CALL_2ARG = Callable[[Any, Any], Any]
CALL_3ARG = Callable[[Any, Any, Any], Any]


def areinstances(objects: Iterable, of_what: type | tuple[type, ...]) -> bool:
    for each_obj in objects:
        if not isinstance(each_obj, of_what):
            return False
    return True


def bool_pair_to_cases(cond1, cond2) -> int:  # TODO cond*: Boolable
    return sum({x + 1 for x in which_of(cond1, cond2)})


def geteverything() -> dict[str, Any]:
    """ 
    :return: dict[str, Any], every global and built-in variable
    """
    return {**globals(), **vars(builtins)}


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

    def call_method(self: Any, *args: Any, **kwargs: Any):
        """
        :param self: Any, object with a method to call
        :param args: Iterable, positional arguments to call the method with
        :param kwargs: Mapping[str, Any], keyword arguments to call the \
            method with
        :return: Any, the output of calling the method of `self` with the \
            specified `args` and `kwargs`
        """
        return getattr(self, method_name)(*args, **kwargs)

    return call_method


@overload
def name_of(an_obj: Any) -> str: ...
@overload
def name_of(an_obj: Any, get: Literal["__name__", "__qualname__"]) -> str: ...
@overload
def name_of(an_obj: Any, get: Literal["__mro__"]) -> tuple[type, ...]: ...


def name_of(an_obj: Any, get: str = "__name__"):
    """ Get the name of an object or of its type/class.

    :param an_obj: Any, object to get the name of.
    :param attr_name: str naming the attribute of `an_obj` (or of its class) \
        to return. Defaults to "__name__".
    :return: str naming an_obj, usually its type/class name.
    """
    return getattr(an_obj, get, getattr(type(an_obj), get))


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


def tuplify(an_obj: Any, split_string: bool = False) -> tuple:
    """
    :param an_obj: Any, object to convert into a tuple.
    :param split_string: bool, True to split a string into a tuple of \
        its characters; else (by default) False to leave strings intact.
    :return: tuple, either `an_obj` AS a tuple if `tuple(an_obj)` works (and \
        `split_string=True` or `an_obj` isn't a string); else `an_obj` IN a \
        single-item tuple.
    """
    try:
        assert split_string or not isinstance(an_obj, str)
        return tuple(an_obj)
    except (AssertionError, TypeError):
        return (an_obj, )


def which_of(*conditions: Any) -> set[int]:  # TODO conditions: Boolable
    """
    :param conditions: Iterable[Boolable] of items to filter
    :return: set[int], the indices of every truthy item in `conditions`
    """
    return set((i for i, cond in enumerate(conditions) if cond))


class HasClass(abc.ABC):
    __class__: Callable[[Any], Any]


class HasSlots(abc.ABC):
    __slots__: tuple


@runtime_checkable
class Poppable[T](Protocol):
    def pop(self, *_) -> T: ...


@runtime_checkable
class Updatable(Protocol):
    """ Any object or class with an `update` method is an `Updatable`.
        `dict`, `MutableMapping`, and `set` are each `Updatable`. """

    def update(self, *_args, **_kwargs): ...


class HumanBytes:
    """ Shamelessly stolen from https://stackoverflow.com/a/63839503 """
    METRIC_LABELS: list[str] = ["B", "kB", "MB", "GB", "TB", "PB",
                                "EB", "ZB", "YB"]
    BINARY_LABELS: list[str] = ["B", "KiB", "MiB", "GiB", "TiB",
                                "PiB", "EiB", "ZiB", "YiB"]

    # PREDEFINED FOR SPEED
    PRECISION_OFFSETS: list[float] = [0.5, 0.05, 0.005, 0.0005]
    PRECISION_FORMATS: list[str] = ["{}{:.0f} {}", "{}{:.1f} {}",
                                    "{}{:.2f} {}", "{}{:.3f} {}"]

    @staticmethod
    def format(num: int | float, metric: bool = False,
               precision: int = 1) -> str:
        """
        Human-readable formatting of bytes, using binary (powers of 1024)
        or metric (powers of 1000) representation.
        """
        assert isinstance(num, (int, float)), "num must be an int or float"
        assert isinstance(metric, bool), "metric must be a bool"
        assert isinstance(precision, int) and 0 <= precision <= 3, \
            "precision must be an int (range 0-3)"

        unit_labels = (HumanBytes.METRIC_LABELS if metric
                       else HumanBytes.BINARY_LABELS)
        last_label = unit_labels[-1]
        unit_step = 1000 if metric else 1024
        unit_step_thresh = unit_step - HumanBytes.PRECISION_OFFSETS[precision]

        is_negative = num < 0
        if is_negative:  # Faster than ternary assignment or always running abs().
            num = abs(num)

        for unit in unit_labels:
            if num < unit_step_thresh:
                # VERY IMPORTANT:
                # Only accepts the CURRENT unit if we're BELOW the threshold where
                # float rounding behavior would place us into the NEXT unit: F.ex.
                # when rounding a float to 1 decimal, any number ">= 1023.95" will
                # be rounded to "1024.0". Obviously we don't want ugly output such
                # as "1024.0 KiB", since the proper term for that is "1.0 MiB".
                break
            if unit != last_label:
                # We only shrink the number if we HAVEN'T reached the last unit.
                # NOTE: These looped divisions accumulate floating point rounding
                # errors, but each new division pushes the rounding errors further
                # and further down in the decimals, so it doesn't matter.
                num /= unit_step

        return HumanBytes.PRECISION_FORMATS[precision].format(
            "-" if is_negative else "", num, unit)


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
    IS_A = (bytes, str, bytearray)


class BytesOrStr(metaclass=BytesOrStrMeta):
    """ Any `bytes`, `str`, or `bytearray` instance is also an instance \
        of the `BytesOrStr` class. """


class PureIterableMeta(MultiTypeMeta):
    IS_A = (Iterable, )
    ISNT_A = (str, bytes, Mapping)


class PureIterable(metaclass=PureIterableMeta):
    """ Iterables that aren't strings, bytes, or Mappings are "Pure." """


class NonTxtColMeta(MultiTypeMeta):
    IS_A = (Collection, )
    ISNT_A = (str, bytes, bytearray)


class NonTxtCollection(metaclass=NonTxtColMeta):
    """ All Collections except `str`, bytes, & `bytearray` are \
        `NonTxtCollection`s. """


class AddSeqMeta(type):

    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, Sequence) and \
            has_method(instance, "__add__")

    def __subclasscheck__(cls, subclass: Any) -> bool:
        return issubclass(subclass, Sequence) and \
            has_method(subclass, "__add__")


class AddableSequence(metaclass=AddSeqMeta):
    """ Any Sequence with an `__add__` method is an `AddableSequence`. """


class Traversible:
    """ Base class for recursive iterators that can visit all items in a \
        nested container data structure. """

    def __init__(self) -> None:
        self.traversed: set[int] = set()

    def _will_now_traverse(self, an_obj: Any) -> bool:
        """
        :param an_obj: Any, object to recursively visit while traversing
        :return: bool, False if `an_obj` was already visited, else True
        """
        objID = id(an_obj)
        not_traversed = objID not in self.traversed
        self.traversed.add(objID)
        return not_traversed


class Recursively:
    _KT = Hashable | tuple[Hashable, ...]

    @staticmethod
    def getitem(an_obj: SupportsItemAccess, key: _KT) -> Any:
        for k in tuplify(key):
            an_obj = an_obj[k]
        return an_obj

    @classmethod
    def getattribute(cls, an_obj: Any, *attr_names: str) -> Any:
        if attr_names:
            return getattr(an_obj, attr_names[0],
                           cls.getattribute(an_obj, *attr_names[1:]))

    @classmethod
    def setitem(cls, an_obj: SupportsItemAccess, key: _KT, value: Any) -> None:
        keys = tuplify(key)
        if len(keys) == 1:
            an_obj[keys[0]] = value
        else:
            cls.setitem(an_obj[keys[0]], keys[1:], value)


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


class IteratorFactory:
    _T = TypeVar("_T")

    @classmethod
    def first_element_of(cls, an_obj: Iterable[_T] | _T) -> _T:
        """ Get `an_obj`'s first element if `an_obj` is iterable; \
            else simply return `an_obj` unchanged.

        :param an_obj: Iterable to return the first element of, or Any.
        :return: Any, the first element of `an_obj` if `an_obj` is iterable; \
                 else `an_obj`
        """
        return next(cls.iterate(an_obj))

    @no_type_check
    @classmethod
    def iterate(cls, an_obj: Iterable[_T] | _T) -> Iterator[_T]:
        """ Iterate `an_obj`.

        :param an_obj: Iterable to iterate over, or Any.
        :return: Iterator over `an_obj` or its elements/values.
        """
        with KeepTryingUntilNoErrors(*DATA_ERRORS) as next_try:
            with next_try():
                iterator = iter(an_obj.values())
            with next_try():
                iterator = iter(an_obj)
            with next_try():
                iterator = iter([an_obj])
        return iterator


class Comparer(IteratorFactory):
    # Class type variables for type hints
    Comparable = TypeVar("Comparable")  # Comparison function input arg(s)
    Comparee = TypeVar("Comparee")      # Item being compared to other items
    Comparison = Callable[[Comparable, Comparable], bool]  # Comparer function
    ToNumber = Callable[[Comparable], SupportsFloat]  # Sizer function
    ToComparable = Callable[[Comparee], Comparable]   # Sizer metafunction

    @classmethod
    def comparison(cls, smallest: bool = False, earliest: bool = False
                   ) -> Comparison:
        """ Get function that compares two `SupportsFloat` objects.

        smallest & earliest => `x.__lt__(y)` (Less Than),
        biggest & latest => `x.__ge__(y)` (Greater than or Equal to), etc.

        :param smallest: bool,_description_, defaults to False
        :param earliest: bool,_description_, defaults to False
        :return: Comparison, function that takes 2 `SupportsFloat` objects, \
            calls an inequality method of the first's on the second, and \
            returns the (boolean) result.
        """
        return method(f'__{"l" if smallest else "g"}'
                      f'{"t" if earliest else "e"}__')

    @classmethod
    def size_of(cls, item: Any, get_size: ToNumber,
                make_comparable: ToComparable) -> SupportsFloat:
        """ Get an item's size as a float.

        :param item: Any, item to return the size of
        :param get_size: Callable[[Any], SupportsFloat], comparison \
            function that converts an item into a numerical value to return
        :param make_comparable: Callable[[Any], Any], secondary comparison \
            function that converts an item into an input acceptable by \
            `compare_their` to convert to a numerical value to return
        :return: SupportsFloat, size of `item`
        """
        try:
            item_size = get_size(item)
        except DATA_ERRORS:
            try:
                item_size = get_size(make_comparable(item))
            except DATA_ERRORS:
                item_size = 1.0
        return item_size

    @classmethod
    def compare(cls, items: Iterable[Comparee], compare_their: ToNumber = len,
                make_comparable: ToComparable = str,
                smallest: bool = False, earliest: bool = False) -> Comparee:
        """ Get the biggest (or smallest) item in `items`. 

        :param items: Iterable[Any], things to compare.
        :param compare_their: Callable[[Any], SupportsFloat], comparison \
            function, defaults to `len`
        :param make_comparable: Callable[[Any], Any], comparison \
            function, defaults to `str`
        :param default: Any, starting item to compare other items against
        :return: Any, item with the largest value returned by calling \
            `compare_their(make_comparable(`item`))`.
        """
        if not items:
            raise ValueError("No items for Comparer.compare to compare!")
        compare = cls.comparison(smallest, earliest)
        biggest = cls.first_element_of(items)
        max_size = cls.size_of(biggest, compare_their, make_comparable)
        for item in items:
            item_size = cls.size_of(item, compare_their, make_comparable)
            if compare(item_size, max_size):  # item_size >= max_size:
                biggest = item
                max_size = item_size
        return biggest


class Methods(NamedTuple):
    get: CALL_2ARG
    has: CALL_2ARG
    set_to: CALL_3ARG

    def lacks(self, an_obj: Any, key: Hashable,
              exclude: Container = set()) -> bool:
        """
        :param key: Hashable
        :param exclude: Container, values to ignore or overwrite. If `a_dict` \
            maps `key` to one, then return True as if `key is not in a_dict`.
        :return: bool, True if `key` is not mapped to a value in `a_dict` or \
            is mapped to something in `exclude`
        """
        return not self.has(an_obj, key) or an_obj[key] in exclude


class Lazily:
    attribute = Methods(get=getattr, has=hasattr, set_to=setattr)
    item = Methods(get=operator.getitem, has=operator.contains,
                   set_to=operator.setitem)
    _TO_GET = Literal["item", "attribute"]

    @classmethod
    def get(cls, an_obj: Any, key: Hashable,
            get_if_absent: Callable,
            get_an: _TO_GET = "attribute",
            exclude: Container = set(),
            getter_args: Iterable = tuple(),
            getter_kwargs: Mapping = dict()) -> Any:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from `LazyButHonestDict.lazyget` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to \
            `key` in `a_dict`) will not be returned; instead returning \
            `get_if_absent(*getter_args, **getter_kwargs)`
        """
        meths: Methods = getattr(cls, get_an)
        return get_if_absent(*getter_args, **getter_kwargs) if \
            meths.lacks(an_obj, key, exclude) else meths.get(an_obj, key)

    @classmethod
    def setdefault(cls, an_obj: Any, key: Hashable,
                   get_if_absent: Callable,
                   get_an: _TO_GET = "attribute",
                   getter_args: Iterable = tuple(),
                   getter_kwargs: Mapping = dict(),
                   exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: Container of possible values to replace with \
            `get_if_absent(*getter_args, **getter_kwargs)` and return if \
            they are mapped to `key` in `a_dict`
        """
        meths: Methods = getattr(cls, get_an)
        if meths.lacks(an_obj, key, exclude):
            meths.set_to(an_obj, key, get_if_absent(
                *getter_args, **getter_kwargs))
        return meths.get(an_obj, key)
