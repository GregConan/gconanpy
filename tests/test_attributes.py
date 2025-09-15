#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-09-11
Updated: 2025-09-11
"""
# Import standard libraries
from collections.abc import Callable, Iterable
from copy import deepcopy
import itertools
from typing import Any

# Import local custom libraries
from gconanpy import attributes
from gconanpy.testers import Tester
from gconanpy.trivial import always_false, always_none, always_true


class TestAttributesFunctions(Tester):
    _LazyMeth = Callable[[Any, str, Callable], Any]
    NO_EXPECTED = object()
    TRIVIALS = {False: always_false, True: always_true, None: always_none}

    class HasFoo:
        foo: Any

    def check_lazy(self, an_obj: Any, name: str, lazy_meths:
                   Iterable[_LazyMeth], expected_result: Any = NO_EXPECTED,
                   **kwargs: Any):
        for lazy_meth in lazy_meths:
            for result, fn in self.TRIVIALS.items():
                self.check_result(lazy_meth(deepcopy(an_obj),
                                            name, fn, **kwargs),
                                  result if expected_result is
                                  self.NO_EXPECTED else expected_result)

    def test_lazyget_1(self) -> None:
        self.add_basics()
        obj = self.HasFoo()
        FOO = "hello"
        ATTR_LAZIES = (attributes.lazyget, attributes.lazysetdefault)
        self.check_lazy(obj, "foo", ATTR_LAZIES)
        setattr(obj, "foo", FOO)
        self.check_lazy(obj, "foo", ATTR_LAZIES, FOO)
        self.check_lazy(obj, "foo", ATTR_LAZIES, exclude={FOO})
        delattr(obj, "foo")
        self.check_lazy(obj, "foo", ATTR_LAZIES)


class TestAttrsOf(Tester):
    EXAMPLE_TYPES: tuple[type, ...] = (
        list, dict, int, float, str, tuple, bytes)

    def test_but_not_1(self) -> None:
        self.add_basics()
        self.check_result(attributes.AttrsOf(self.alist).but_not(self.adict),
                          set(dir(list)) - set(dir(dict)))

    def test_but_not_2(self) -> None:
        for type1, type2 in itertools.combinations(self.EXAMPLE_TYPES, 2):
            self.check_result(attributes.AttrsOf(type1).but_not(type2),
                              set(dir(type1)) - set(dir(type2)))

    def test_methods(self) -> None:
        for each_type in self.EXAMPLE_TYPES:
            for _, meth in attributes.AttrsOf(each_type).methods():
                assert callable(meth)

    def test_public(self) -> None:
        for each_type in self.EXAMPLE_TYPES:
            for name, _ in attributes.AttrsOf(each_type).public():
                assert not name.startswith("_")
