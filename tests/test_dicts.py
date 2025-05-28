#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-05-26
"""
# Import standard libraries
from collections.abc import Callable, Generator, Mapping
from typing import Any

# Import local custom libraries
from gconanpy.dicts import \
    Cryptionary, Defaultionary, DotDict, DotPromptionary, Explictionary, \
    FancyDict, Invertionary, LazyDict, LazyDotDict, Promptionary, \
    SubCryptionary, Subsetionary, Updationary, Walktionary
from gconanpy.maptools import WalkMap
from tests.testers import Tester


DotInvertionary = type("DotInvertionary", (DotDict, Invertionary), dict())
DotWalktionary = type("DotWalktionary", (DotDict, Walktionary), dict())
InvertCryptionary = type("InvertCryptionary",
                         (Cryptionary, Invertionary), dict())
InvertPromptionary = type("InvertPromptionary",
                          (Promptionary, Invertionary), dict())
SubDotDict = type("SubDotDict", (DotDict, Subsetionary), dict())


class DictTester(Tester):
    _ExplType = type[Explictionary]
    TEST_CLASSES: tuple[_ExplType, ...]

    def get_1s_dict(self) -> dict[str, int]:
        return dict(a=1, b=1, c=1, d=1)

    get_custom_dicts: Callable[[], Generator[Explictionary, None, None]]

    def map_test(self, map_type: _ExplType, in_dict: dict, out_dict: dict,
                 method_to_test: str, *method_args, **method_kwargs) -> None:
        a_map = map_type(in_dict)
        getattr(a_map, method_to_test)(*method_args, **method_kwargs)
        self.check_result(a_map, map_type(out_dict))

    def cant_call(self, method_name: str, custom_class: _ExplType):
        self.add_basics()
        # CantClass = CustomDicts.new_class("CantClass", *custom_features)
        try:
            getattr(custom_class(self.adict), method_name)()
            assert False
        except AttributeError:
            pass


class TestCryptionary(DictTester):
    TEST_CLASSES: tuple[type[Cryptionary], ...] = (
        Cryptionary, InvertCryptionary, SubCryptionary)

    def get_custom_dicts(self) -> Generator[Cryptionary, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

    def test_getitem(self):
        cli_args = self.build_cli_args()
        self.check_result(cli_args.creds["password"], "my_password")

    def test_repr(self):
        cli_args = self.build_cli_args()
        self.check_result(type(cli_args.creds), Cryptionary)

        assert "password" in cli_args.creds.encrypted
        if "my_password" in str(cli_args.creds):
            raise ValueError(f"'my_password' visible in {cli_args.creds}")


class TestDefaultionary(DictTester):  # TODO
    TEST_CLASSES: tuple[type[Defaultionary], ...] = (
        Defaultionary, FancyDict, LazyDict, LazyDotDict)

    def get_custom_dicts(self) -> Generator[Defaultionary, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

    def test_setdefaults_1(self) -> None:
        for dfty in self.get_custom_dicts():
            dfty.setdefaults()  # TODO


class TestDotDicts(DictTester):
    TEST_CLASSES: tuple[type[DotDict], ...] = (
        DotDict, DotPromptionary, DotWalktionary, FancyDict,
        LazyDotDict, SubDotDict)

    def get_custom_dicts(self) -> Generator[DotDict, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

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

    # TODO test CustomDicts.new_class("DotWalk", "dot", "walk") ?
    def test_homogenize(self):
        for dd in self.get_custom_dicts():
            dd.testdict = dict(hello=dict(q=dd),
                               world=DotDict(foo=dict(bar="baz")))
            print(type(dd.testdict["world"]))
            for a_dict in (dd["testdict"], dd["testdict"]["hello"],
                           dd.testdict["world"].foo):  # type: ignore
                assert not isinstance(a_dict, type(dd))
            dd.homogenize()
            for a_map in WalkMap(dd).values():
                print(f"a_map: {a_map}")
                assert isinstance(a_map, type(dd))

    def test_protected(self):
        self.add_basics()
        ldd = LazyDotDict(self.adict)

        protected_attrs = getattr(ldd, ldd.PROTECTEDS)
        assert self.cannot_alter(ldd, *protected_attrs)
        assert protected_attrs.issuperset({"lazyget", "lazysetdefault",
                                           ldd.PROTECTEDS})
        # for attr_name in protected_attrs: self.check_result(ldd[attr_name], getattr(ldd, attr_name))  # TODO?

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


class TestInvertionary(DictTester):
    # TODO Add InvertCryptionary and make it decrypt before inverting
    TEST_CLASSES: tuple[type[Invertionary], ...] = (
        DotInvertionary, FancyDict, Invertionary, InvertPromptionary)

    def get_custom_dicts(self) -> Generator[Invertionary, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

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

    def test_cant(self):
        # TODO Use combinations(...) of custom_kwargs
        self.cant_call("invert", Updationary)
        self.cant_call("invert", Promptionary)


class TestUpdationary(DictTester):
    TEST_CLASSES: tuple[type[Updationary], ...] = (
        DotDict, DotWalktionary, FancyDict, LazyDict, LazyDotDict,
        SubDotDict, Updationary)

    def get_custom_dicts(self) -> Generator[Updationary, None, None]:
        self.add_basics()
        for dict_class in self.TEST_CLASSES:
            yield dict_class(self.adict)

    def one_update_test(self, updty: Updationary, expected_len: int,
                        a_map: Mapping | None = None,
                        **expected: Any) -> Updationary:
        for copy in (False, True):
            updatefn = updty.update_copy if copy else updty.update
            if a_map is None:
                newd = updatefn(**expected)
            else:
                newd = updatefn(a_map, **expected)
                expected.update(a_map)
            if copy:
                updty = newd  # type: ignore
            self.check_result(len(updty), expected_len)
            for k, v in expected.items():
                self.check_result(updty[k], v)
        return updty

    def test_update_1(self) -> None:
        for updty in self.get_custom_dicts():
            self.one_update_test(updty, 4, d=4)

    def test_update_2(self) -> None:
        for updty in self.get_custom_dicts():
            updty = self.one_update_test(updty, 4, dict(d=4))
            self.one_update_test(updty, 4, dict(a=3), c=1)
