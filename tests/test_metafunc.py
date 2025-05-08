#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-05-07
"""
# Import local custom libraries
from gconanpy.maps import (Defaultionary, Cryptionary, DotDict, Explictionary,
                           LazyDotDict, LazyDict)
from gconanpy.metafunc import AttributesOf, metaclass_issubclass
from tests.testers import Tester


class TestAttributesOf(Tester):
    def test_but_not(self):
        self.add_basics()
        self.check_result(AttributesOf(self.alist).but_not(self.adict),
                          set(dir(list)) - set(dir(dict)))


class TestMetaclassFunctions(Tester):
    def test_metaclass_issubclass(self):
        self.add_basics()
        subclasses = (dict, Explictionary, Defaultionary, DotDict)

        class DictTestType(metaclass=metaclass_issubclass(
                isnt_any_of=(LazyDict, LazyDotDict, Cryptionary),
                is_all_of=subclasses)):
            ...

        for test_class in subclasses:
            dd = test_class(self.adict)
            assert isinstance(dd, DictTestType)
            assert issubclass(test_class, DictTestType)
