#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-04-09
"""
# Import local custom libraries
from gconanpy.maps import DotDict, Invertionary
from tests.testers import Tester


class TestDotDict(Tester):
    def test_1(self):
        self.add_basics()
        dd = DotDict(self.adict)
        self.check_result(dd.a, 1)
        for k, v in self.adict.items():
            self.check_result(getattr(dd, k), v)

    def test_2(self):
        self.add_basics()
        dd = DotDict(self.adict)
        self.check_result(len(dd), 3)
        del dd.b
        self.check_result([v for v in dd.values()], [1, 3])
        self.check_result(len(dd), 2)
        self.check_result(dd.PROTECTEDS in dd, False)


class TestInvertionary(Tester):
    def get_1s_dict(self) -> dict[str, int]:
        return dict(a=1, b=1, c=1, d=1)

    def map_test(self, map_type: type, in_dict: dict, out_dict: dict,
                 method_to_test: str, *method_args, **method_kwargs) -> None:
        a_map = map_type(in_dict)
        getattr(a_map, method_to_test)(*method_args, **method_kwargs)
        self.check_result(a_map, map_type(out_dict))

    def test_1(self):
        self.add_basics()
        self.map_test(Invertionary, self.adict, {1: "a", 2: "b", 3: "c"},
                      "invert")

    def test_2(self):
        self.map_test(Invertionary, self.get_1s_dict(), {1: "d"}, "invert")

    def test_3(self):
        for holder_type in (list, set, tuple):
            self.map_test(Invertionary, self.get_1s_dict(),
                          {1: holder_type(["a", "b", "c", "d"])}, "invert",
                          keep_collisions_in=holder_type)

    def test_4(self):
        actual_err = None
        try:
            invertable = Invertionary(a=dict(b=2))
            invertable.invert(keep_collisions_in=list)
        except TypeError as expected_err:
            actual_err = expected_err
        assert isinstance(actual_err, TypeError)
