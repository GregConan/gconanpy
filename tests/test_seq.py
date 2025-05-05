#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2025-05-04
"""
# Import standard libraries
import datetime as dt
import random

# Import local custom libraries
from gconanpy.metafunc import method_metaclass
from gconanpy.seq import DunderParser
from gconanpy.ToString import stringify, ToString
from tests.testers import Tester


class TestDunderParser(Tester):
    def pascaltest(self, method_name: str, pascalized: str) -> None:
        self.check_result(self.dp.pascalize(method_name), pascalized)
        new_type = method_metaclass(method_name, include=True)
        self.check_result(new_type.__name__, f"Supports{pascalized}Meta")
        new_type = method_metaclass(method_name, include=False)
        self.check_result(new_type.__name__, f"Lacks{pascalized}Meta")

    def test_pascalize(self):
        self.dp = DunderParser()
        for method_name, pascalized in (
            ("__class_instancecheck__", "ClassInstanceCheck"),
            ("__delattr__", "DelAttr"), ("__delitem__", "DelItem"),
            ("__getattr__", "GetAttr"), ("__getitem__", "GetItem"),
            ("__hash__", "Hash"), ("__iter__", "Iter"),
            ("__init_subclass__", "InitSubclass"),
            ("__instancecheck__", "InstanceCheck"),
            ("__next__", "Next"), ("__qualname__", "QualName"),
            ("__setattr__", "SetAttr"), ("__setitem__", "SetItem"),
            ("__sizeof__", "SizeOf"), ("__subclasscheck__", "SubclassCheck")
        ):
            self.pascaltest(method_name, pascalized)


class TestStringify(Tester):
    def check_map(self, expected: str, **kwargs):
        self.add_basics()
        self.check_result(stringify(self.adict, **kwargs), expected)

    def test_bytes(self):
        bytestring = b"hello"
        self.check_result(stringify(bytestring), "hello")

    def test_defaults(self):
        self.check_map("'a': 1, 'b': 2, and 'c': 3")

    def test_add(self):
        self.check_result(type(stringify("hi") + " there"), ToString)
        # self.check_result(type("hi" + stringify(" there")), ToString)  # TODO?

    def test_affix(self):
        self.add_basics()
        affixes = ["{", "(", "[", "<",
                   "}", ")", "]", ">", "hello", " "]
        for _ in range(5):
            prefix = random.choice(affixes)
            suffix = random.choice(affixes)
            stringified = stringify(self.alist, prefix=prefix, suffix=suffix)
            print(f"prefix: {prefix}\nsuffix: {suffix}\n"
                  f"stringified: {stringified}\n")
            assert str.startswith(stringified, prefix)
            assert str.endswith(stringified, suffix)

    def test_dt(self):
        moment = dt.datetime.now()
        self.check_result(stringify(moment), moment.isoformat(
            sep="_", timespec="seconds").replace(":", "-"))

    def test_join_on(self):
        self.check_map("'a'=1, 'b'=2, and 'c'=3", join_on="=")

    def test_lastly(self):
        self.check_map("'a': 1, 'b': 2, 'c': 3", lastly="")

    def test_max_len(self):
        self.check_map("'a': 1, 'b': 2...", max_len=17)

    def test_none(self):
        self.check_result(stringify(None), "")

    def test_quote(self):
        self.check_map('"a": 1, "b": 2, and "c": 3', quote='"')

    def test_quote_nums(self):
        self.check_map("'a': '1', 'b': '2', and 'c': '3'", quote_numbers=True)
        self.check_result(stringify(dict(a=2.5), quote_numbers=True),
                          "'a': '2.5'")

    def test_sep(self):
        self.check_map("'a': 1; 'b': 2; and 'c': 3", sep=";")
