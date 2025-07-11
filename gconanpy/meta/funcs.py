#!/usr/bin/env python3

"""
Functions to manipulate and define classes and/or other functions.
Greg Conan: gregmconan@gmail.com
Created: 2025-06-20
Updated: 2025-07-06
"""
# Import standard libraries
from collections.abc import (Callable, Collection, Generator,
                             Iterable, Mapping, Sequence)
import itertools
import more_itertools
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, NamedTuple

# Import local custom libraries
try:
    from . import MatcherBase
    from ..reg import DunderParser
    from ..trivial import call_method_of
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.meta import MatcherBase
    from gconanpy.reg import DunderParser
    from gconanpy.trivial import call_method_of

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


def bool_pair_to_cases(cond1, cond2) -> int:  # TODO cond*: Boolable
    return sum({x + 1 for x in which_of(cond1, cond2)})


def combinations_of_conditions(all_conditions: Sequence[str], cond_mappings:
                               Mapping[MatcherBase._KT, Any] = dict()) -> dict:
    class Matcher(MatcherBase):
        conditions = all_conditions
        ConditionCombo = NamedTuple(
            "ConditionsCombo", **{cond: bool for cond in conditions})

    return Matcher({Matcher.as_conds_combo(k): v
                    for k, v in cond_mappings.items()})


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
    def nameit(x: Any) -> str: return get_name(x).capitalize()
    str_isall = "And".join(names_of(tuplify(is_all_of), max_n, nameit))
    str_isntany = "Or".join(names_of(tuplify(isnt_any_of), max_n, nameit))
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


def tuplify_preserve_str(an_obj: Any) -> tuple:
    """
    :param an_obj: Any, object to convert into a tuple.
    :return: tuple, `an_obj` IN a single-item tuple if `an_obj` is a string \
        or `tuple(an_obj)` raises `TypeError`, else `an_obj` AS a tuple.
    """
    try:
        assert not isinstance(an_obj, str)
        return tuple(an_obj)
    except (AssertionError, TypeError):
        return (an_obj, )


def which_of(*conditions: Any) -> set[int]:  # TODO conditions: Boolable
    """
    :param conditions: Iterable[Boolable] of items to filter
    :return: set[int], the indices of every truthy item in `conditions`
    """
    return set((i for i, cond in enumerate(conditions) if cond))
