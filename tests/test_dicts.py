#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-06-10
"""
# Import standard libraries
from collections.abc import Callable, Generator, Iterable, Mapping
from typing import Any, TypeVar

# Import local custom libraries
# from gconanpy import attributes
from gconanpy import mapping
from gconanpy.mapping import map_funcs
from gconanpy.mapping.dicts import Cryptionary, Defaultionary, DotDict, DotPromptionary, Explictionary, FancyDict, Invertionary, LazyDict, LazyDotDict, Promptionary, SubCryptionary, Subsetionary, Updationary, Walktionary
# from tests import test_dicts
from tests.testers import Tester  # , TimeTester


DotInvertionary = type("DotInvertionary", (DotDict, Invertionary), dict())
DotWalktionary = type("DotWalktionary", (DotDict, Walktionary), dict())
InvertCryptionary = type("InvertCryptionary",
                         (Cryptionary, Invertionary), dict())
InvertPromptionary = type("InvertPromptionary",
                          (Promptionary, Invertionary), dict())
SubDotDict = type("SubDotDict", (DotDict, Subsetionary), dict())


class DictTester(Tester):
    _E = TypeVar("_E", bound=Explictionary)
    CLASSES = tuple[type[_E], ...]
    TEST_CLASSES: CLASSES

    def get_custom_dicts(self, classes: CLASSES, _base: type[_E]
                         ) -> Generator[_E, None, None]:
        self.add_basics()
        for dict_class in classes:
            yield dict_class(self.adict)

    def get_1s_dict(self, keys: Iterable[str] = ("a", "b", "c", "d")
                    ) -> dict[str, int]:
        return {key: 1 for key in keys}

    def map_test(self, method_to_test: Callable, map_type: type[dict],
                 in_dict: dict, out_dict: dict,
                 *method_args, **method_kwargs) -> None:
        a_map = map_type(in_dict)
        method_to_test(a_map, *method_args, **method_kwargs)
        self.check_result(a_map, map_type(out_dict))

    def cant_call(self, method_name: str, custom_class: type[dict]):
        self.add_basics()
        try:
            getattr(custom_class(self.adict), method_name)()
            assert False
        except AttributeError:
            pass


class TestCryptionary(DictTester):
    CLASSES = tuple[type[Cryptionary], ...]
    TEST_CLASSES: CLASSES = (
        Cryptionary, InvertCryptionary, SubCryptionary)

    def test_getitem(self, args_type: type = DotDict,
                     classes: CLASSES = TEST_CLASSES) -> None:
        for dict_class in classes:
            cli_args = self.build_cli_args(args_type, dict_class)
            self.check_result(cli_args.creds["password"], "my_password")

    def test_repr(self, args_type: type = DotDict,
                  classes: CLASSES = TEST_CLASSES) -> None:
        for dict_class in classes:
            cli_args = self.build_cli_args(args_type, dict_class)
            self.check_result(type(cli_args.creds), dict_class)

            assert "password" in cli_args.creds.encrypted
            if "my_password" in str(cli_args.creds):
                raise ValueError(f"'my_password' visible in {cli_args.creds}")


class TestDictFunctions(DictTester):
    # has_setdefaults = type("has_setdefaults", (dict, ), dict(setdefaults=""))

    def check_setdefaults(self, expected: dict[str, int],
                          setdefaults: Callable = map_funcs.setdefaults,
                          dict_class: type[dict] = dict,
                          **setdefaults_kwargs: Any) -> None:
        self.add_basics()
        newdefaults = self.get_1s_dict()  # dict(a=1, b=1, c=1, d=1)
        new_dict = dict_class(self.adict)
        result = setdefaults(new_dict, **newdefaults,
                             **setdefaults_kwargs)
        if result is None:
            result = new_dict
        for k, v in expected.items():
            self.check_result(result[k], v)

    def invert_test(self, in_dict: dict, out_dict: dict,
                    invert: Callable = map_funcs.invert,
                    dict_class: type[dict] = dict,
                    **invert_kwargs: Any) -> None:
        to_invert = dict_class(in_dict)
        inverted = invert(to_invert, **invert_kwargs)
        if inverted is None:
            inverted = to_invert
        self.check_result(dict(inverted), out_dict)

    def one_update_test(self, a_dict: dict, expected_len: int,
                        from_map: Mapping | None = None,
                        # update: Callable = methods.update,
                        **expected: Any) -> dict:
        if from_map is None:
            new_dict = map_funcs.update(a_dict, **expected)
        else:
            new_dict = map_funcs.update(a_dict, from_map, **expected)
            expected.update(from_map)
        self.check_result(len(new_dict), expected_len)
        for k, v in expected.items():
            self.check_result(new_dict[k], v)
        return new_dict

    def test_has_all(self, has_all: Callable = map_funcs.has_all,
                     dict_class: type[dict] = dict) -> None:
        self.add_basics()
        dict1 = dict_class(self.adict)
        assert not has_all(dict1, ("a", "b", "c", "d"))
        dict2: dict[str, Any] = self.adict.copy()
        assert has_all(dict1, dict2.keys())
        dict2["nothing"] = None
        assert not has_all(dict1, dict2.keys(), {None})

    def test_invert_1(self, invert: Callable = map_funcs.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        self.invert_test(self.adict, {1: "a", 2: "b", 3: "c"},
                         invert, dict_class)

    def test_invert_2(self, invert: Callable = map_funcs.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        self.invert_test(self.get_1s_dict(), {1: "d"},
                         invert, dict_class)

    def test_invert_3(self, invert: Callable = map_funcs.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        for holder_type in (list, set, tuple):
            self.invert_test(self.get_1s_dict(),
                             {1: holder_type(["a", "b", "c", "d"])}, invert,
                             dict_class, keep_collisions_in=holder_type)

    def test_invert_4(self, invert: Callable = map_funcs.invert,
                      dict_class: type[dict] = dict) -> None:
        actual_err = None
        try:
            uninvertable = dict_class(a=dict(b=2))
            invert(uninvertable, keep_collisions_in=list)
        except TypeError as expected_err:
            actual_err = expected_err
        assert isinstance(actual_err, TypeError)

    def test_invert_5(self, invert: Callable = map_funcs.invert,
                      dict_class: type[dict] = dict) -> None:
        invertable = dict_class(a="b", b="a")
        inverted = invert(invertable)
        if inverted is None:
            inverted = invertable
        self.check_result(inverted, invertable)

    def test_lookup(self, lookup: Callable = map_funcs.lookup,
                    args_class: type[dict] = dict,
                    creds_class: type[dict] = dict) -> None:
        cli_args = self.build_cli_args(args_class, creds_class)
        self.check_result(lookup(cli_args, f"a dict"), self.adict)
        for k, v in self.adict.items():
            self.check_result(lookup(cli_args, f"a dict.{k}"), v)

    def test_setdefaults_1(self,
                           setdefaults: Callable = map_funcs.setdefaults,
                           dict_class: type[dict] = dict) -> None:
        self.check_setdefaults(dict(b=2, c=3, d=1), setdefaults, dict_class)

    def test_setdefaults_2(self,
                           setdefaults: Callable = map_funcs.setdefaults,
                           dict_class: type[dict] = dict) -> None:
        self.check_setdefaults(dict(b=2, c=1, d=1), setdefaults, dict_class,
                               exclude={3})

    def test_update_1(self) -> None:
        self.add_basics()
        self.one_update_test(self.adict, 4, d=4)

    def test_update_2(self) -> None:
        self.add_basics()
        new_dict = self.one_update_test(self.adict, 4, dict(d=4))
        self.one_update_test(new_dict, 4, dict(a=3), c=1)


class TestDefaultionary(TestDictFunctions):  # TODO
    CLASSES = tuple[type[Defaultionary], ...]
    TEST_CLASSES: CLASSES = (Defaultionary, FancyDict, LazyDict, LazyDotDict)

    def test_has_all(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            super().test_has_all(DictClass.has_all, DictClass)

    def test_setdefaults_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            super().test_setdefaults_1(DictClass.setdefaults, DictClass)

    def test_setdefaults_2(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            super().test_setdefaults_2(DictClass.setdefaults, DictClass)


class TestDotDicts(TestDictFunctions):
    CLASSES = tuple[type[DotDict], ...]
    TEST_CLASSES: CLASSES = (DotDict, DotPromptionary, DotWalktionary,
                             FancyDict, LazyDotDict, SubDotDict)

    def test_set(self, classes: CLASSES = TEST_CLASSES) -> None:
        for dd in self.get_custom_dicts(classes, DotDict):
            self.check_result(dd.a, 1)
            for k, v in self.adict.items():
                self.check_result(getattr(dd, k), v)

    def test_len(self, classes: CLASSES = TEST_CLASSES) -> None:
        for dd in self.get_custom_dicts(classes, DotDict):
            self.check_result(len(dd), 3)
            del dd.b
            self.check_result([v for v in dd.values()], [1, 3])
            self.check_result(len(dd), 2)
            self.check_result(dd.PROTECTEDS in dd, False)

    def test_get(self, classes: CLASSES = TEST_CLASSES) -> None:
        for dd in self.get_custom_dicts(classes, DotDict):
            dd.five = 5
            self.check_result(dd["five"], 5)
            dd["six"] = 6
            self.check_result(dd.six, 6)
            assert self.cannot_alter(dd, "get")

    def test_homogenize(self, classes: CLASSES = TEST_CLASSES) -> None:
        for dd in self.get_custom_dicts(classes, DotDict):
            dd.testdict = dict(hello=dict(q=dd),
                               world=DotDict(foo=dict(bar="baz")))
            print(type(dd.testdict["world"]))
            for a_dict in (dd["testdict"], dd["testdict"]["hello"],
                           dd.testdict["world"].foo):  # type: ignore
                assert not isinstance(a_dict, type(dd))
            dd.homogenize()
            for a_map in mapping.Walk(dd, only_yield_maps=True).values():
                print(f"a_map: {a_map}")
                assert isinstance(a_map, type(dd))

    def test_lookup(self, classes: CLASSES = TEST_CLASSES,
                    crypty_type: type = Cryptionary) -> None:
        for DictClass in classes:
            super().test_lookup(DictClass.lookup, DictClass, crypty_type)

    def test_protected(self, classes: CLASSES = (
            FancyDict, LazyDotDict)) -> None:
        self.add_basics()
        for LazyDotDictClass in classes:
            ldd = LazyDotDictClass(self.adict)

            protected_attrs: set | Any = getattr(ldd, ldd.PROTECTEDS)
            assert self.cannot_alter(ldd, *protected_attrs)
            assert protected_attrs.issuperset({"lazyget", "lazysetdefault",
                                               ldd.PROTECTEDS})
            # for attr_name in protected_attrs: self.check_result(ldd[attr_name], getattr(ldd, attr_name))  # TODO?

    def test_subclass(self, classes: CLASSES = TEST_CLASSES) -> None:
        self.add_basics()
        for ddclass in classes:
            class DotDictSubClass(ddclass):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                def __getattr__(self, name):
                    return f"sub{super().__getattr__(name)}"

            ddsc = DotDictSubClass(self.adict)
            self.check_result({x: getattr(ddsc, x) for x in ddsc.keys()},
                              dict(a="sub1", b="sub2", c="sub3"))


class TestInvertionary(TestDictFunctions):
    # TODO Add InvertCryptionary and make it decrypt before inverting
    CLASSES = tuple[type[Invertionary], ...]
    TEST_CLASSES: CLASSES = (
        DotInvertionary, FancyDict, Invertionary, InvertPromptionary)

    def check_all_classes(self, tester_method: Callable,
                          classes: CLASSES = TEST_CLASSES) -> None:
        self.add_basics()
        for DictClass in classes:
            tester_method(DictClass.invert, DictClass)

    def test_invert_1(self) -> None:
        self.check_all_classes(super().test_invert_1)

    def test_invert_2(self) -> None:
        self.check_all_classes(super().test_invert_2)

    def test_invert_3(self) -> None:
        self.check_all_classes(super().test_invert_3)

    def test_invert_4(self) -> None:
        self.check_all_classes(super().test_invert_4)

    def test_invert_5(self) -> None:
        self.check_all_classes(super().test_invert_5)

    def test_cant_invert(self, classes: tuple[type[dict], ...] = (
            Promptionary, Updationary)) -> None:
        # TODO Use combinations(...) of custom_kwargs
        for DictClass in classes:
            self.cant_call("invert", DictClass)


class TestUpdationary(DictTester):
    CLASSES = tuple[type[Updationary], ...]
    TEST_CLASSES: CLASSES = (
        DotDict, DotWalktionary, FancyDict, LazyDict, LazyDotDict,
        SubDotDict, Updationary)

    def one_update_test(self, updty: Updationary, expected_len: int,
                        a_map: Mapping | None = None,
                        **expected: Any) -> Updationary:
        for copy in (False, True):
            if a_map is None:
                newd = updty.update(copy=copy, **expected)
            else:
                newd = updty.update(a_map, copy, **expected)
                expected.update(a_map)
            if copy:
                updty = newd
            self.check_result(len(updty), expected_len)
            for k, v in expected.items():
                self.check_result(updty[k], v)
        return updty

    def test_update_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        for updty in self.get_custom_dicts(classes, Updationary):
            self.one_update_test(updty, 4, d=4)

    def test_update_2(self, classes: CLASSES = TEST_CLASSES) -> None:
        for updty in self.get_custom_dicts(classes, Updationary):
            updty = self.one_update_test(updty, 4, dict(d=4))
            self.one_update_test(updty, 4, dict(a=3), c=1)


class TestWalktionary(DictTester):
    CLASSES = tuple[type[Explictionary], ...]
    TEST_CLASSES: CLASSES = (DotWalktionary, FancyDict, Walktionary)

    def test_walk_keys_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        """ Test that `d.walk(False).keys()` reduces to `d.keys()` for a \
            dict `d` that contains no `Mappings` nested inside of it. """
        for adict in self.get_custom_dicts(classes, Walktionary):
            self.check_result([k for k in adict.walk(False).keys()],
                              [k for k in adict.keys()])

    def test_walk_keys_2(self, args_type: type = DotWalktionary,
                         crypty_type: type = Cryptionary) -> None:
        cli_args = self.build_cli_args(args_type, crypty_type)
        keys = {k for k in cli_args.walk(only_yield_maps=False)}
        self.check_result(keys, {"a", "a dict", "a list", "address", "b",
                                 "bytes_nums", "c", "creds", "debugging",
                                 "password"})


"""
class TestOOPvsFunctions(TimeTester):

    def test_all(self, n_tests_orders_of_magnitude: int = 3):
        func_tester = TestDictFunctions()
        results = set()
        for OOPClass in (TestDefaultionary, TestDotDicts, TestInvertionary,
                         TestUpdationary, TestWalktionary):
            oop_tester = OOPClass()
            for method_name in attributes.Of(OOPClass).method_names():
                if method_name.startswith("test_") and \
                        hasattr(TestDictFunctions, method_name):
                    results.add(self.time_method(
                        method_name, n_tests_orders_of_magnitude,
                        func_tester, oop_tester))

        # Print results (which requires raising an error)
        print(results)
        assert False
"""
