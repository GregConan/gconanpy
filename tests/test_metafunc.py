#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-05-17
"""
# Import local custom libraries
from gconanpy.maps import (CustomDicts, Defaultionary, Cryptionary,
                           DotDict, Explictionary, LazyDict)
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
        LazyDotDict = CustomDicts.new_class("LazyDotDict", "dot", "lazy")
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
