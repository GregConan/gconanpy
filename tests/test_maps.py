#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-04-29
"""
# Import standard libraries
from collections.abc import Generator, Mapping
from typing import Any

# Import local custom libraries
from gconanpy.maps import Defaultionary, DotDict, Invertionary, LazyDotDict
from tests.testers import Tester


class MapTester(Tester):
    TEST_CLASSES: tuple[type[Mapping], ...]

    def get_1s_dict(self) -> dict[str, int]:
        return dict(a=1, b=1, c=1, d=1)

    def get_custom_dicts(self) -> Generator[type, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

    def map_test(self, map_type: type, in_dict: dict, out_dict: dict,
                 method_to_test: str, *method_args, **method_kwargs) -> None:
        a_map = map_type(in_dict)
        getattr(a_map, method_to_test)(*method_args, **method_kwargs)
        self.check_result(a_map, map_type(out_dict))


class TestInvertionary(MapTester):
    TEST_CLASSES = (Invertionary, )  # Defaultionary, DotDict, LazyDotDict)

    def test_1(self):
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            self.map_test(dict_class, self.adict, {1: "a", 2: "b", 3: "c"},
                          "invert")

    def test_2(self):
        for dict_class in self.TEST_CLASSES:
            self.map_test(dict_class, self.get_1s_dict(), {1: "d"}, "invert")

    def test_3(self):
        for dict_class in self.TEST_CLASSES:
            for holder_type in (list, set, tuple):
                self.map_test(dict_class, self.get_1s_dict(),
                              {1: holder_type(["a", "b", "c", "d"])},
                              "invert", keep_collisions_in=holder_type)

    def test_4(self):
        for dict_class in self.TEST_CLASSES:
            actual_err = None
            try:
                invertable = dict_class(a=dict(b=2))
                invertable.invert(keep_collisions_in=list)
            except TypeError as expected_err:
                actual_err = expected_err
            assert isinstance(actual_err, TypeError)

    def test_5(self):
        for dict_class in self.TEST_CLASSES:
            invertable = dict_class(a="b", b="a")
            self.check_result(invertable.invert(copy=True), invertable)


class TestDefaultionary(MapTester):
    TEST_CLASSES = (Defaultionary, DotDict, LazyDotDict)

    def one_update_test(self, dfty: Defaultionary, expected_len: int,
                        a_map: Mapping | None = None,
                        **expected: Any) -> Defaultionary:
        for copy in (False, True):
            if a_map is None:
                newd = dfty.update(**expected, copy=copy)
            else:
                newd = dfty.update(a_map, **expected, copy=copy)
                expected.update(a_map)
            if copy:
                dfty = newd
            self.check_result(len(dfty), expected_len)
            for k, v in expected.items():
                self.check_result(dfty[k], v)
        return dfty

    def test_update_1(self) -> None:
        for dfty in self.get_custom_dicts():
            self.one_update_test(dfty, 4, d=4)

    def test_update_2(self) -> None:
        for dfty in self.get_custom_dicts():
            dfty = self.one_update_test(dfty, 4, dict(d=4))
            self.one_update_test(dfty, 4, dict(a=3), c=1)

    def test_setdefaults_1(self) -> None:
        for dfty in self.get_custom_dicts():
            dfty.setdefaults()


class TestDotDicts(MapTester):
    TEST_CLASSES = (DotDict, LazyDotDict)

    def test_set(self):
        for dd in self.get_custom_dicts():
            self.check_result(dd.a, 1)
            for k, v in self.adict.items():
                self.check_result(getattr(dd, k), v)

    def test_len(self):
        for dd in self.get_custom_dicts():
            self.check_result(len(dd), 3)
            del dd.b
            self.check_result([v for v in dd.values()], [1, 3])
            self.check_result(len(dd), 2)
            self.check_result(dd.PROTECTEDS in dd, False)

    def test_get(self):
        for dd in self.get_custom_dicts():
            dd.five = 5
            self.check_result(dd["five"], 5)
            dd["six"] = 6
            self.check_result(dd.six, 6)
            assert self.cannot_alter(dd, "get")

    def test_homogenize(self):
        for dd in self.get_custom_dicts():
            dd.testdict = dict(a=dd)
            assert not isinstance(dd["testdict"], type(dd))
            dd.homogenize()
            assert isinstance(dd["testdict"], type(dd))
            assert isinstance(dd.testdict, type(dd))

    def test_protected(self):
        self.add_basics()
        ldd = LazyDotDict(self.adict)

        protected_attrs = getattr(ldd, ldd.PROTECTEDS)
        assert self.cannot_alter(ldd, *protected_attrs)
        assert protected_attrs.issuperset({"lazyget", "lazysetdefault",
                                           ldd.PROTECTEDS})

    def test_subclass(self):
        self.add_basics()
        for ddclass in self.TEST_CLASSES:
            class DotDictSubClass(ddclass):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def __getattr__(self, name):
                    return f"sub{super().__getattr__(name)}"

            ddsc = DotDictSubClass(self.adict)
            self.check_result({x: getattr(ddsc, x) for x in ddsc.keys()},
                              dict(a="sub1", b="sub2", c="sub3"))
