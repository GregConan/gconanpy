#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-04-15
"""
# Import standard libraries
from collections.abc import Generator

# Import local custom libraries
from gconanpy.maps import DotDict, Invertionary, LazyDotDict
from tests.testers import Tester


class TestDotDict(Tester):
    TEST_CLASSES = (DotDict, LazyDotDict)

    def get_dot_dicts(self) -> Generator[type, None, None]:
        self.add_basics()
        for ddclass in self.TEST_CLASSES:
            yield ddclass(self.adict)

    def test_1(self):
        for dd in self.get_dot_dicts():
            self.check_result(dd.a, 1)
            for k, v in self.adict.items():
                self.check_result(getattr(dd, k), v)

    def test_2(self):
        for dd in self.get_dot_dicts():
            self.check_result(len(dd), 3)
            del dd.b
            self.check_result([v for v in dd.values()], [1, 3])
            self.check_result(len(dd), 2)
            self.check_result(dd.PROTECTEDS in dd, False)

    def test_3(self):
        for dd in self.get_dot_dicts():
            dd.five = 5
            self.check_result(dd["five"], 5)
            dd["six"] = 6
            self.check_result(dd.six, 6)
            assert self.cannot_alter(dd, "get")

    def test_4(self):
        for dd in self.get_dot_dicts():
            dd.testdict = dict(a=dd)
            assert not isinstance(dd["testdict"], type(dd))
            dd.homogenize()
            assert isinstance(dd["testdict"], type(dd))

    def test_5(self):
        self.add_basics()
        ldd = LazyDotDict(self.adict)

        protected_attrs = getattr(ldd, ldd.PROTECTEDS)
        assert self.cannot_alter(ldd, *protected_attrs)

        lazy_attrs = {"lazyget", "lazysetdefault"}
        assert lazy_attrs.issubset(protected_attrs)

    def test_6(self):
        self.add_basics()
        for ddclass in self.TEST_CLASSES:
            class DotDictSubClass(ddclass):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def __getattr__(self, name):
                    return f"sub{ddclass.__getattr__(self, name)}"

            ddsc = DotDictSubClass(self.adict)
            self.check_result({x: getattr(ddsc, x) for x in dir(ddsc)},
                              dict(a="sub1", b="sub2", c="sub3"))


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
