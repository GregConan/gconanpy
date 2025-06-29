#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-06-28
"""
# Import standard libraries
import builtins
from collections.abc import Iterable
import random
from typing import Any, TypeVar

# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
import gconanpy.attributes as attributes
from gconanpy.debug import StrictlyTime
from gconanpy.mapping import Combinations
from gconanpy.mapping.dicts import Cryptionary, Defaultionary, DotDict, \
    Explictionary, LazyDict, LazyDotDict
from gconanpy.meta.classes import Boolable, MultiTypeMeta
from gconanpy.meta.funcs import metaclass_issubclass, name_of, name_type_class
from tests.testers import Tester


class TestAttributesOf(Tester):
    def test_but_not(self):
        self.add_basics()
        self.check_result(attributes.Of(self.alist).but_not(self.adict),
                          set(dir(list)) - set(dir(dict)))


class TestMetaClasses(Tester):
    _T = TypeVar("_T")

    def assert_that_all(self, objects: Iterable[Any], *,
                        is_if: MultiTypeMeta._TypeChecker = isinstance,
                        is_a: MultiTypeMeta._TypeArgs = (object, ),
                        isnt_a: MultiTypeMeta._TypeArgs = tuple()) -> None:
        for an_obj in objects:
            assert is_if(an_obj, is_a)
            for true_kwargs in Combinations.of_map({"is_a": is_a,
                                                    "isnt_a": isnt_a}):
                assert MultiTypeMeta.check(an_obj, is_if, **true_kwargs)

            assert not is_if(an_obj, isnt_a)
            for false_kwargs in Combinations.of_map({"is_a": isnt_a,
                                                     "isnt_a": is_a}):
                assert not MultiTypeMeta.check(an_obj, is_if, **false_kwargs)

    def test_Boolable_builtins(self) -> None:
        self.assert_that_all(vars(builtins).values(), is_a=Boolable)

    def test_not_Boolable(self) -> None:
        self.assert_that_all((pd.DataFrame(), pd.Series()), isnt_a=Boolable)


class TestMetaFunctions(Tester):

    def test_name_type_class(self) -> None:
        n_variants = 100
        n_runs = 100
        disjoint_classes = {list, tuple, dict, pd.DataFrame, attributes.Of}
        subsets = [*Combinations.of_seq(disjoint_classes)]
        for _ in range(n_variants):
            subclasses = random.choice(subsets)
            not_subclasses = disjoint_classes - set(subclasses)
            with StrictlyTime(f"running {name_of(name_type_class)}"):
                for _ in range(n_runs):
                    name = name_type_class(subclasses, not_subclasses)
            for class_name in disjoint_classes:
                assert name_of(class_name).capitalize() in name

    def test_metaclass_issubclass(self) -> None:
        self.add_basics()
        subclasses = (dict, Explictionary, Defaultionary, DotDict)
        not_subclasses = (LazyDict, LazyDotDict, Cryptionary)

        class DictTestType(metaclass=metaclass_issubclass(
                isnt_any_of=not_subclasses, is_all_of=subclasses)):
            ...

        for correct_subclass in subclasses:
            dd = correct_subclass(self.adict)
            assert isinstance(dd, DictTestType)
            assert issubclass(correct_subclass, DictTestType)

        for incorrect_subclass in not_subclasses:
            dd = incorrect_subclass(self.adict)
            assert not isinstance(dd, DictTestType)
            assert not issubclass(incorrect_subclass, DictTestType)
