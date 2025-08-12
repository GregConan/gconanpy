#!/usr/bin/env python3

"""
Functions/classes to manipulate, define, and/or be manipulated by others.
Greg Conan: gregmconan@gmail.com
Created: 2025-07-28
Updated: 2025-08-11
"""
# Import standard libraries
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
import itertools
# from operator import attrgetter, methodcaller  # TODO?
from typing import Any, cast, NamedTuple

# Import local custom libraries
try:
    from . import (bool_pair_to_cases, has_method,
                   name_of, names_of, tuplify)
    from ..reg import DunderParser
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.meta import (bool_pair_to_cases, has_method,
                               name_of, names_of, tuplify)
    from gconanpy.reg import DunderParser


# Constant: Conditions Combination (2+ boolean conditions); MatcherBase keys
CC = tuple[bool, ...]


class MakeMetaclass:
    _CHECKER = Callable[[Any, Any], bool]

    @staticmethod
    def new(name: str, instanceif: _CHECKER, subclassif: _CHECKER) -> type:
        """
        :param name: str, name of the metaclass type to return.
        :param instanceif: Callable[[Any, Any], bool], function to call from \
            the `instancecheck` methods of the returned metaclass.
        :param subclassif: Callable[[Any, Any], bool], function to call from \
            the `subclasscheck` methods of the returned metaclass.
        :return: type, metaclass with `instanceif` as its `__instancecheck__` \
            method and `subclassif` as its `__subclasscheck__` method.
        """
        return type(name, (type, ), {"__instancecheck__": instanceif,
                                     "__subclasscheck__": subclassif})

    @classmethod
    def for_methods(cls, method_name: str, include: bool = True) -> type:
        """ _summary_

        :param method_name: str naming the method that the returned \
            metaclass type object will check whether objects have
        :param include: bool, True to return a metaclass for a type WITH \
            certain methods; else (by default) False for a type WITHOUT them
        :return: type, _description_
        """
        capitalized = DunderParser().pascalize(method_name)
        if include:
            def _check(_cls, thing: Any) -> bool:
                return has_method(thing, method_name)
            verb = "Supports"
        else:
            def _check(_cls, thing: Any) -> bool:
                return not has_method(thing, method_name)
            verb = "Lacks"
        return cls.new(f"{verb}{capitalized}Meta", _check, _check)

    @classmethod
    def for_classes(cls, is_all_of: type | tuple[type, ...] = tuple(),
                    isnt_any_of: type | tuple[type, ...] = tuple(),
                    name: str | None = None) -> type:
        def _checker(is_a: Callable[[Any, type | tuple[type, ...]], bool]):
            @staticmethod
            def _check(instance):
                return (not is_all_of or is_a(instance, is_all_of)
                        ) and not is_a(instance, isnt_any_of)
            return _check
        if not name:
            name = name_type_class(is_all_of, isnt_any_of)
        return cls.new(name, _checker(isinstance), _checker(issubclass))


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


class MatcherBase(dict[CC, Any]):
    ConditionCombo: type[CC]

    # Broader key type; will be converted into CC
    _KT = tuple[str, ...] | list[str] | dict \
        | CC | str | bool | list[bool] | None

    conditions: Sequence[str]  # Instance variable: condition names

    def __init__(self, matches: Mapping[_KT, Any] = dict()
                 ) -> None:
        for conds in itertools.product((True, False),
                                       repeat=len(self.conditions)):
            key = self.as_conds_combo(conds)
            self[key] = matches.get(key, None)

    @classmethod
    def as_conds_combo(cls, conds: _KT) -> CC:
        match conds:
            case cls.ConditionCombo():
                combo = cast(CC, conds)
            case Mapping():
                combo = cls.ConditionCombo(**conds)
            case str():
                combo = cls.conds_in((conds, )) if conds in cls.conditions \
                    else cls.conds_in(conds.split())
            case Sequence():
                conds_types = {type(c) for c in conds}
                if conds_types == {bool}:
                    combo = cls.ConditionCombo(**{cls.conditions[i]: conds[i]
                                                  for i in range(len(conds))})
                elif conds_types == {str}:
                    combo = cls.conds_in(conds)
                else:
                    raise TypeError(f"Cannot parse conditions {conds}")
            case bool() | None:
                combo = cls.ConditionCombo(**{
                    k: bool(conds) for k in cls.conditions})
        return combo

    @classmethod
    def conds_in(cls, conds: Iterable) -> CC:
        return cls.ConditionCombo(**{cond: cond in conds
                                     for cond in cls.conditions})


def combinations_of_conditions(all_conditions: Sequence[str], cond_mappings:
                               Mapping[MatcherBase._KT, Any] = dict()) -> dict:
    class Matcher(MatcherBase):
        conditions = all_conditions
        ConditionCombo = NamedTuple(
            "ConditionsCombo", **{cond: bool for cond in conditions})

    return Matcher({Matcher.as_conds_combo(k): v
                    for k, v in cond_mappings.items()})


class NonIterable(metaclass=MakeMetaclass.for_methods(
        "__iter__", include=False)):
    """ Any object that isn't an Iterable is a NonIterable. """


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

        return type(class_name, (type, ), {"metaclass": MakeMetaclass.new(
            "MethodMetaclass", _check, _check), **kwargs})
