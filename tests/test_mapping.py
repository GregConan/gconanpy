#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-07
Updated: 2025-10-10
"""
# Import standard libraries
from collections.abc import (Callable, Generator, Iterable,
                             Mapping, MutableMapping)
from math import prod
import pdb
import random
import string
from types import SimpleNamespace
from typing import Any, TypeVar

# Import local custom libraries
from gconanpy import mapping
from gconanpy.access import attributes
from gconanpy.access import ACCESS, Access, Accessor
from gconanpy.debug import StrictlyTime
from gconanpy.iters import Combinations, duplicates_in, MapWalker, powers_of_ten, Randoms
from gconanpy.mapping.dicts import *
from gconanpy.mapping.grids import HashGrid, Locktionary  # GridCryptionary,
from gconanpy.meta import full_name_of, TimeSpec
# from tests import test_mapping
from gconanpy.testers import Tester, TimeTester
from gconanpy.trivial import (always_false, always_none,
                              always_true, return_self)


# Make various combinations of custom dicts to validate them all
DotInvertionary = type("DotInvertionary", (DotDict, Invertionary), dict())
DotWalktionary = type("DotWalktionary", (DotDict, Walktionary), dict())
InvertCryptionary = type("InvertCryptionary",
                         (Cryptionary, Invertionary), dict())
InvertPromptionary = type("InvertPromptionary",
                          (Promptionary, Invertionary), dict())
SubDotDict = type("SubDotDict", (DotDict, Subsetionary), dict())


class DictTester(Tester):
    _E = TypeVar("_E", bound=CustomDict)
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
                 *method_args: Any, **method_kwargs: Any) -> None:
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

    def test_getitem(self, args_type: type[DotDict] = DotDict,
                     classes: CLASSES = TEST_CLASSES) -> None:
        for dict_class in classes:
            cli_args = self.build_cli_args(args_type, dict_class)
            self.check_result(cli_args.creds["password"], "my_password")

    def test_repr(self, args_type: type[DotDict] = DotDict,
                  classes: CLASSES = TEST_CLASSES) -> None:
        for dict_class in classes:
            cli_args = self.build_cli_args(args_type, dict_class)
            self.check_result(type(cli_args.creds), dict_class)

            assert "password" in cli_args.creds.encrypted
            if "my_password" in str(cli_args.creds):
                raise ValueError(f"'my_password' visible in {cli_args.creds}")


class TestDictFunctions(DictTester):
    # has_setdefaults = type("has_setdefaults", (dict, ), dict(setdefaults=""))
    _KT = TypeVar("_KT")
    _VT = TypeVar("_VT")
    _M = TypeVar("_M", bound=MutableMapping)

    def check_setdefaults(self, expected: dict[str, int],
                          setdefaults: Callable = mapping.setdefaults,
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

    def check_sorted_by(self, expected: list[tuple[_KT, _VT]],
                        a_dict: dict[_KT, _VT], by: Literal["keys", "values"],
                        sorted_by: Callable = mapping.sorted_by,
                        dict_class: type[dict] = dict,
                        print_vars: bool = True):
        sorty = dict_class(a_dict)
        if print_vars:  # If the check fails, show local vars to debug why
            print(locals())
            self.check_result(list(sorted_by(sorty, by)), expected)
            self.check_result(list(sorted_by(sorty, by, descending=True)),
                              list(reversed(expected)))
        else:
            assert list(sorted_by(sorty, by)) == expected
            assert list(sorted_by(sorty, by, descending=True)) \
                == list(reversed(expected))

    def invert_test(self, in_dict: dict, out_dict: dict,
                    invert: Callable = mapping.invert,
                    dict_class: type[dict] = dict,
                    **invert_kwargs: Any) -> None:
        to_invert = dict_class(in_dict)
        inverted = invert(to_invert, **invert_kwargs) or to_invert
        self.check_result(dict(inverted), out_dict)

    @staticmethod
    def multiply_subtract(*multiply: int | float, **subtract: int | float
                          ) -> int | float:
        return prod(multiply) - sum(subtract.values())

    def one_update_test(self, a_dict: _M, expected_len: int,
                        from_map: Mapping | None = None,
                        # update: Callable = methods.update,
                        **expected: Any) -> _M:
        if from_map is None:
            new_dict = mapping.update(a_dict, **expected)
        else:
            new_dict = mapping.update(a_dict, from_map, **expected)
            expected.update(from_map)
        self.check_result(len(new_dict), expected_len)
        for k, v in expected.items():
            self.check_result(new_dict[k], v)
        return new_dict

    def test_chain_get(self, chain_get: Callable = mapping.chain_get,
                       dict_class: type[dict] = dict) -> None:
        self.add_basics()
        adict = dict_class(self.adict)

        # Tests where chain_get should return default
        for no_keys in (tuple(), list(), ("x", "y", "z"), ("y", "z"),
                        [i for i in range(5)]):  # , (list(), tuple())  # ?
            self.check_result(chain_get(adict, no_keys), None)
            self.check_result(chain_get(adict, no_keys, "the"), "the")

        # Tests where chain_get should return the value mapped to "a"
        for seq_with_a in (("y", "z", "a", "b"), ["a", "b", "c", "d"],
                           ("x", "y", "z", "a"), ["a"], ["d", "a"]):
            self.check_result(chain_get(adict, seq_with_a), adict["a"])

    def test_has_all(self, has_all: Callable = mapping.has_all,
                     dict_class: type[dict] = dict) -> None:
        self.add_basics()
        dict1 = dict_class(self.adict)
        assert not has_all(dict1, ("a", "b", "c", "d"))
        dict2: dict[str, Any] = self.adict.copy()
        assert has_all(dict1, dict2.keys())
        dict2["nothing"] = None
        assert not has_all(dict1, dict2.keys(), {None})

    def test_invert_1(self, invert: Callable = mapping.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        self.invert_test(self.adict, {1: "a", 2: "b", 3: "c"},
                         invert, dict_class)

    def test_invert_2(self, invert: Callable = mapping.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        self.invert_test(self.get_1s_dict(), {1: "d"},
                         invert, dict_class)

    def test_invert_3(self, invert: Callable = mapping.invert,
                      dict_class: type[dict] = dict) -> None:
        self.add_basics()
        # for holder_type in (list, set, tuple):  # TODO
        self.invert_test(self.get_1s_dict(),
                         {1: ["a", "b", "c", "d"]}, invert,
                         dict_class, keep_keys=True)

    def test_invert_4(self, invert: Callable = mapping.invert,
                      dict_class: type[dict] = dict) -> None:
        actual_err = None
        try:
            uninvertable = dict_class(a=dict(b=2))
            invert(uninvertable, keep_collisions_in=list)
        except TypeError as expected_err:
            actual_err = expected_err
        assert isinstance(actual_err, TypeError)

    def test_invert_5(self, invert: Callable = mapping.invert,
                      dict_class: type[dict] = dict) -> None:
        invertable = dict_class(a="b", b="a")
        inverted = invert(invertable)
        if inverted is None:
            inverted = invertable
        self.check_result(inverted, invertable)

    def test_lazyget_key(self, lazyget: Callable = mapping.lazyget,
                         dict_class: type[dict] = dict) -> None:
        self.add_basics()
        a_dict = dict_class(self.adict)
        for k, v in a_dict.items():
            self.check_result(lazyget(a_dict, k), v)
            for triv_fn, triv_out in self.TRIVIALS.items():
                for args in list(), tuple(), self.alist:
                    for kwargs in dict(), self.adict:

                        # Return the value to get if we do not exclude it
                        for exclude in Combinations.excluding(
                                a_dict.values(), {v}):
                            self.check_result(lazyget(
                                a_dict, k, triv_fn, exclude,
                                *args, **kwargs), v)

                        # If we exclude the value to get, return the default
                        self.check_result(lazyget(a_dict, k, triv_fn, {v}, *args,
                                                  **kwargs), triv_out)

    def test_lazyget_nonkey(self, lazyget: Callable = mapping.lazyget,
                            dict_class: type[dict] = dict) -> None:
        self.add_basics()
        a_dict = dict_class(self.adict)
        for nonkey in (None, 50, "hello", dict, dict_class, 3.14, lazyget):
            for args in Randoms.randintsets(min_n=20, max_n=20):
                kwargs = Randoms.randict(values=tuple(
                    Randoms.randints(min_n=0, max_n=5)), value_types=int, key_types=str)

                # Verify that lazyget correctly runs the function it's given
                self.check_result(lazyget(
                    a_dict, nonkey, self.multiply_subtract, {}, *args, **kwargs
                ), self.multiply_subtract(*args, **kwargs))

    def unhashable_lazytest(self, lazy_getter: Callable,
                            dict_class: type[dict] = dict) -> None:
        VALUE = ["arbitrary", "unhashable", "list", set(), dict()]
        KEY = "a"
        a_dict = dict_class({KEY: VALUE})
        self.check_result(VALUE, lazy_getter(
            a_dict, KEY, return_self, {None}, VALUE))

    def test_has(self, dict_has: Callable = mapping.has,
                 dict_class: type[dict] = dict) -> None:
        self.add_basics()
        VALUE = ["arbitrary", "unhashable", "list", set(), dict()]
        KEY = "a"
        a_dict = dict_class({KEY: VALUE})
        assert dict_has(a_dict, KEY)
        assert not dict_has(a_dict, KEY, exclude=[VALUE])
        assert not dict_has(dict_class(), KEY)

    def test_lazyget_unhashable(self, lazyget: Callable = mapping.lazyget,
                                dict_class: type[dict] = dict) -> None:
        self.unhashable_lazytest(lazyget, dict_class)

    def test_lazysetdefault_unhashable(
            self, lazysetdefault: Callable = mapping.lazysetdefault,
            dict_class: type[dict] = dict) -> None:
        self.unhashable_lazytest(lazysetdefault, dict_class)

    def test_lookup(self, lookup: Callable = mapping.lookup,
                    args_class: type[dict] = dict,
                    creds_class: type[dict] = dict) -> None:
        cli_args = self.build_cli_args(args_class, creds_class)
        print(locals())
        self.check_result(lookup(cli_args, "a dict"), self.adict)
        for k, v in self.adict.items():
            self.check_result(lookup(cli_args, f"a dict.{k}"), v)

    def test_setdefaults_1(self, setdefaults: Callable = mapping.setdefaults,
                           dict_class: type[dict] = dict) -> None:
        self.check_setdefaults(dict(b=2, c=3, d=1), setdefaults, dict_class)

    def test_setdefaults_2(self, setdefaults: Callable = mapping.setdefaults,
                           dict_class: type[dict] = dict) -> None:
        self.check_setdefaults(dict(b=2, c=1, d=1), setdefaults, dict_class,
                               exclude={3})

    def test_sorted_by_1(self, sorted_by: Callable = mapping.sorted_by,
                         dict_class: type[dict] = dict,
                         show: bool = True) -> None:
        self.add_basics()
        for which in ("keys", "values"):
            self.check_sorted_by([("a", 1), ("b", 2), ("c", 3)], self.adict,
                                 which, sorted_by, dict_class, show)

    def test_sorted_by_2(self, sorted_by: Callable = mapping.sorted_by,
                         dict_class: type[dict] = dict,
                         show: bool = True) -> None:
        revdict = dict(c=1, b=2, a=3)
        self.check_sorted_by([("a", 3), ("b", 2), ("c", 1)], revdict,
                             "keys", sorted_by, dict_class, show)
        self.check_sorted_by([("c", 1), ("b", 2), ("a", 3)], revdict,
                             "values", sorted_by, dict_class, show)

    def test_update_1(self) -> None:
        self.add_basics()
        self.one_update_test(self.adict, 4, d=4)

    def test_update_2(self) -> None:
        self.add_basics()
        new_dict = self.one_update_test(self.adict, 4, dict(d=4))
        self.one_update_test(new_dict, 4, dict(a=3), c=1)


class TestAccessor(DictTester):
    CLASSES = tuple[type[Accessor], ...]
    TEST_CLASSES: CLASSES = (Accessor, )
    UNIT: TimeSpec.UNIT = "seconds"

    class TRIPLETTERS:
        """ Example/dummy object to access attributes of """
        a = 1
        b = 2
        c = 3

    def test_lazyget_basic(self) -> None:
        self.add_basics()
        VALUE = "arbitrary"
        getdefault = lambda *_: VALUE
        self.check_result(ACCESS["item"].lazyget(
            self.adict, "a", getdefault), 1)

    def prep(self, n_tests_orders_of_magnitude: int = 4) -> None:
        self.add_basics()
        randicts = list()
        randobjs = list()
        for _ in Randoms.randcount(max_len=20):
            randicts.append({**Randoms.randict(
                keys=string.ascii_letters, max_len=10), **self.adict})
            randobjs.append(SimpleNamespace(**randicts[-1]))
        self.randicts = tuple(randicts)
        self.randobjs = tuple(randobjs)
        self.test_Ns = powers_of_ten(n_tests_orders_of_magnitude)

    def time_lazy(self, lazy_meth: Callable, lazy_result: Any,
                  input_obj: Any, asattrs: bool = False,
                  getter: Callable = always_none,
                  exclude: Container = set(), *args,
                  **kwargs: Any) -> float:
        # randicts = SimpleNamespace(**self.randicts) if attrs else self.randicts
        duration = 0.0
        with StrictlyTime(f"running {kwargs.pop('lazyname')} "
                          f"{sum(self.test_Ns)} times",
                          time_unit=self.UNIT) as strictimer:
            self.lazytest(lazy_meth, lazy_result, input_obj, asattrs, getter,
                          exclude, *args, **kwargs)
        duration += strictimer.elapsed
        return duration

    def lazytest(self, lazy_meth: Callable, lazy_result: Any,
                 input_obj: Any, asattrs: bool = False,
                 getter: Callable = always_none,
                 exclude: Container = set(), *args,
                 **kwargs: Any) -> None:
        if "lazyname" in kwargs:
            kwargs.pop("lazyname")
        rands = self.randobjs if asattrs else self.randicts
        items = dict.items if not asattrs else \
            lambda x: attributes.AttrsOf(x).public()
        for eachN in self.test_Ns:
            for _ in range(eachN):
                for d in rands:
                    for k, v in items(input_obj):
                        assert lazy_meth(d, k, getter, exclude,
                                         *args, **kwargs) == v
                    for wrong in ("this isn't a key", "neither is this",
                                  "nor this", "nor that"):
                        assert lazy_meth(d, wrong, getter, exclude,
                                         *args, **kwargs) == lazy_result

    # TODO?
    # def test_lazyget_nonkey(self):
    #   TestDictFunctions().test_lazyget_nonkey(ACCESS[item].lazyget)
    #   TestDictFunctions().test_lazyget_nonkey(ACCESS[attribute].lazyget)

    # Change to `timing: bool = True` to run time test
    def test_lazy(self, n_tests_orders_of_magnitude: int = 3,
                  timing: bool = False):
        self.prep(n_tests_orders_of_magnitude)
        getter_args = ({1, 2}, set(), {5}, {"foo", "bar"})
        result = {1, 2, 5, "foo", "bar"}
        # TRIPLETTERS = SimpleNamespace(**self.adict)

        item_funcs = [ACCESS["item"].lazyget, ACCESS["item"].lazysetdefault]
        # Access.item.lazyget, Access.item.lazysetdefault]  # TODO ?
        if not timing:
            lazytest = self.lazytest

        else:
            lazytest = self.time_lazy

            # Only include the mapping.lazy* method tests if we're timing
            # (for comparison); otherwise they are redundant
            item_funcs.append(mapping.lazyget)
            item_funcs.append(mapping.lazysetdefault)

        print("Testing item access")
        for itemfunc in item_funcs:
            lazytest(itemfunc, result, self.adict, False, set.union, set(),
                     *getter_args, lazyname=full_name_of(itemfunc))

        print("Testing attribute access")
        for attrfunc in [attributes.lazyget,
                         attributes.lazysetdefault,
                         ACCESS["attribute"].lazyget,
                         ACCESS["attribute"].lazysetdefault]:
            # Access.attribute.lazyget, Access.attribute.lazysetdefault]:  # TODO ?
            lazytest(attrfunc, result, self.TRIPLETTERS, True, set.union, set(),
                     *getter_args, lazyname=full_name_of(itemfunc))
        assert not timing  # If we're timing, raise err to print results


class TestExclutionary(DictTester):
    CLASSES = tuple[type[Exclutionary], ...]
    TEST_CLASSES: CLASSES = (Exclutionary, FancyDict, LazyDict, LazyDotDict)

    def test_chain_get(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            return TestDictFunctions().test_chain_get(DictClass.chain_get, DictClass)

    def test_has(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_has(DictClass.has_all, DictClass)

    def test_has_all(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_has_all(DictClass.has_all, DictClass)

    def test_setdefaults_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_setdefaults_1(DictClass.setdefaults, DictClass)

    def test_setdefaults_2(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_setdefaults_2(DictClass.setdefaults, DictClass)


class TestDotDicts(DictTester):
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
                           dd.testdict["world"].foo):
                assert not isinstance(a_dict, type(dd))
            dd.homogenize()
            for a_map in MapWalker(dd, only_yield_maps=True).values():
                print(f"a_map: {a_map}")
                assert isinstance(a_map, type(dd))

    def test_lookup(self, classes: CLASSES = TEST_CLASSES,
                    crypty_type: type = Cryptionary) -> None:
        for DictClass in classes:
            TestDictFunctions().test_lookup(
                DictClass.lookup, DictClass, crypty_type)

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


class TestInvertionary(DictTester):
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
        self.check_all_classes(TestDictFunctions().test_invert_1)

    def test_invert_2(self) -> None:
        self.check_all_classes(TestDictFunctions().test_invert_2)

    def test_invert_3(self) -> None:
        self.check_all_classes(TestDictFunctions().test_invert_3)

    def test_invert_4(self) -> None:
        self.check_all_classes(TestDictFunctions().test_invert_4)

    def test_invert_5(self) -> None:
        self.check_all_classes(TestDictFunctions().test_invert_5)

    def test_cant_invert(self, classes: tuple[type[dict], ...] = (
            Promptionary, Updationary)) -> None:
        # TODO Use combinations(...) of custom_kwargs
        for DictClass in classes:
            self.cant_call("invert", DictClass)


class TestLazyDict(DictTester):
    CLASSES = tuple[type[LazyDict], ...]
    TEST_CLASSES: CLASSES = (FancyDict, LazyDict, LazyDotDict,
                             Promptionary, DotPromptionary)

    def test_lazyget_key(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_lazyget_key(
                DictClass.lazyget, DictClass)

    def test_lazyget_nonkey(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_lazyget_nonkey(
                DictClass.lazyget, DictClass)

    def test_lazyget_unhashable(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_lazyget_unhashable(
                DictClass.lazyget, DictClass)

    def test_lazysetdefault_unhashable(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_lazysetdefault_unhashable(
                DictClass.lazyget, DictClass)


class TestSortionary(DictTester):
    CLASSES = tuple[type[Sortionary], ...]
    TEST_CLASSES: CLASSES = (FancyDict, Sortionary)

    def test_sorted_by_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_sorted_by_1(
                DictClass.sorted_by, DictClass)

    def test_sorted_by_2(self, classes: CLASSES = TEST_CLASSES) -> None:
        for DictClass in classes:
            TestDictFunctions().test_sorted_by_2(
                DictClass.sorted_by, DictClass)

    # Remove the initial underscore to run time test
    def _test_time_sorted_by(self, classes: CLASSES = TEST_CLASSES,
                             n_tests_orders_of_magnitude: int = 5) -> None:
        testNs = powers_of_ten(n_tests_orders_of_magnitude)
        with StrictlyTime(f"running {sum(testNs)} Sortionary tests"):
            tester = TestDictFunctions()
            for n in testNs:
                for _ in range(n):
                    for DictClass in classes:
                        params = (DictClass.sorted_by, DictClass, False)
                        tester.test_sorted_by_1(*params)
                        tester.test_sorted_by_2(*params)
        assert False  # Show time taken


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
    CLASSES = tuple[type[CustomDict], ...]
    TEST_CLASSES: CLASSES = (DotWalktionary, FancyDict, Walktionary)

    def test_walk_keys_1(self, classes: CLASSES = TEST_CLASSES) -> None:
        """ Test that `d.walk(False).keys()` reduces to `d.keys()` for a \
            dict `d` that contains no `Mappings` nested inside of it. """
        for adict in self.get_custom_dicts(classes, Walktionary):
            self.check_result([k for k in adict.walk(False).keys()],
                              [k for k in adict.keys()])

    def test_walk_keys_2(self, args_type: type[Walktionary] = DotWalktionary,
                         crypty_type: type = Cryptionary) -> None:
        cli_args = self.build_cli_args(args_type, crypty_type)
        keys = {k for k in cli_args.walk(only_yield_maps=False)}
        self.check_result(keys, {"a", "a dict", "a list", "address", "b",
                                 "bytes_nums", "c", "creds", "debugging",
                                 "password"})


class TestHashGrid(DictTester):
    _T = TypeVar("_T")
    _Pairs = list[tuple[tuple[_T, ...], _T]]
    _PairGenerator = Generator[tuple[_Pairs, HashGrid]]
    _StrDimsGen = Generator[tuple[list[dict[str, str]], list[str], HashGrid]]
    CLASSES = tuple[type[HashGrid], ...]
    TEST_CLASSES: CLASSES = (HashGrid, Locktionary)  # , GridCryptionary)

    def double_check(self, hg: HashGrid, keys, value):
        self.check_result(hg[keys], value)
        self.check_result(hg[*keys], value)

    @staticmethod
    def int_pairs_HG(classes: CLASSES = TEST_CLASSES, n_tests: int = 20,
                     min_pairs: int = 2, max_pairs: int = Randoms.MAX,
                     min_keys: int = 2, max_keys: int = Randoms.MAX
                     ) -> _PairGenerator:
        for hgclass in classes:
            for _ in range(n_tests):
                keylen = random.randint(min_keys, max_keys)
                pairs = [(tuple(Randoms.randints(min_n=keylen, max_n=keylen)),
                          random.randint(Randoms.MIN, Randoms.MAX))
                         for _ in Randoms.randcount(min_pairs, max_pairs)]
                yield (pairs, hgclass(*pairs))

    def dims_names_test(self, get_pairs: Callable[[CLASSES, int], _StrDimsGen],
                        classes: CLASSES = TEST_CLASSES, n_tests: int = 20) -> None:
        for dim_keys, _, hg in get_pairs(classes, n_tests):
            self.check_result(hg.dim_names, tuple(dim_keys[0]))
            assert len(hg.dim_names) == len(set(hg.dim_names))

    def pairs_test_pop(self, get_pairs: Callable[[CLASSES, int], _PairGenerator],
                       classes: CLASSES = TEST_CLASSES, n_tests: int = 20) -> None:
        for pairs, hg in get_pairs(classes, n_tests):
            for keys, value in pairs:
                try:
                    self.check_result(hg.pop(keys), value)
                    assert keys not in hg
                except AssertionError as err:
                    print(f"\nhg={hg}\nlen(hg)={len(hg)}"
                          f"\nkeys={keys}\nvalue={value}")
                    raise err

    def pairs_test_get_set(
            self, get_pairs: Callable[[CLASSES, int], _PairGenerator],
            classes: CLASSES = TEST_CLASSES, n_tests: int = 20) -> None:
        for pairs, hg in get_pairs(classes, n_tests):  # TODO FIX
            for keys, value in pairs:
                try:
                    self.double_check(hg, keys, value)
                    hg[*keys] = None  # Test __setitem__
                    self.double_check(hg, keys, None)  # Test __(g/s)etitem__
                except AssertionError as err:
                    print(f"\nhg={hg}\nlen(hg)={len(hg)}"
                          f"\nkeys={keys}\nvalue={value}")
                    raise err

    @staticmethod
    def str_dims_HG(classes: CLASSES = TEST_CLASSES, n_tests: int = 20
                    ) -> _StrDimsGen:
        for hgclass in classes:
            for _ in range(n_tests):
                n_dims = random.randint(2, Randoms.MAX)
                n_pairs = random.randint(2, Randoms.MAX)
                not_unique_yet = True
                while not_unique_yet:
                    keys = Randoms.randtuple(n_dims, string.ascii_letters)
                    tuples = Randoms.randtuples(
                        min_n=n_dims, max_n=n_dims, min_len=n_pairs,
                        max_len=n_pairs, unique=True)
                    dimensions = {names: vals for names, vals
                                  in zip(keys, tuples)}
                    dim_keys = [{dim_name: dim_vals[i] for dim_name, dim_vals
                                in dimensions.items()} for i in range(n_pairs)]
                    not_unique_yet = duplicates_in(dim_keys)
                values = [Randoms.randstr() for _ in range(n_pairs)]
                yield dim_keys, values, hgclass(
                    values=values, strict=True, **dimensions)

    @staticmethod
    def str_pairs_HG(classes: CLASSES = TEST_CLASSES, n_tests: int = 20
                     ) -> _PairGenerator:
        n = n_tests // len(classes)  # tests per class
        for hgclass in classes:
            for _ in range(n):
                # Create a random HashGrid to test its methods
                pairs = [(keys, Randoms.randstr()) for keys in
                         Randoms.randtuples(same_len=True, unique=True)]
                hg = hgclass(*pairs)
                yield pairs, hg

    def test_int_pairs_contains(self, classes: CLASSES = TEST_CLASSES,
                                n_tests: int = 5) -> None:
        for pairs, hg in self.int_pairs_HG(classes, n_tests):
            for keys, _ in pairs:
                assert keys in hg  # Test __contains__

    def test_int_pairs_get_set(self, classes: CLASSES = TEST_CLASSES,
                               n_tests: int = 20) -> None:
        self.pairs_test_get_set(self.int_pairs_HG, classes,
                                n_tests)  # TODO FIX

    def test_int_pairs_pop(self, classes: CLASSES = TEST_CLASSES,
                           n_tests: int = 20) -> None:
        self.pairs_test_pop(self.int_pairs_HG, classes, n_tests)  # TODO FIX

    def test_str_dims_contains(self, classes: CLASSES = TEST_CLASSES,
                               n_tests: int = 20) -> None:
        for dim_keys, _, hg in self.str_dims_HG(classes, n_tests):
            for keys in dim_keys:
                assert keys in hg

    # def test_wrong_n_keys  # TODO

    def test_str_dims_get_set(self, classes: CLASSES = TEST_CLASSES,
                              n_tests: int = 250) -> None:
        for dim_keys, values, hg in self.str_dims_HG(classes, n_tests):
            for i in range(len(values)):
                try:
                    self.check_result(hg[dim_keys[i]], values[i])
                    hg[dim_keys[i]] = None
                    self.check_result(hg[dim_keys[i]], None)
                except AssertionError as err:
                    print(f"\nhg={hg}\nlen(hg)={len(hg)}\n"
                          f"keys={dim_keys[i]}\nvalue={values[i]}\n"
                          f"")
                    pdb.set_trace()  # TODO Uncomment to interactively debug
                    raise err

    def test_str_dims_names(self, classes: CLASSES = TEST_CLASSES,
                            n_tests: int = 20) -> None:
        self.dims_names_test(self.str_dims_HG, classes, n_tests)

    def test_str_dims_pop(self, classes: CLASSES = TEST_CLASSES,
                          n_tests: int = 500) -> None:
        for dim_keys, values, hg in self.str_dims_HG(classes, n_tests):
            for i in range(len(values)):
                try:
                    assert dim_keys[i] in hg
                    self.check_result(values[i], hg.pop(dim_keys[i]))
                    assert dim_keys[i] not in hg
                except AssertionError as err:
                    print(f"\nhg={hg}\nlen(hg)={len(hg)}\n"
                          f"keys={dim_keys[i]}\nvalue={values[i]}")
                    # pdb.set_trace()  # TODO Uncomment to interactively debug
                    raise err

    def test_str_pairs_contains(self, classes: CLASSES = TEST_CLASSES,
                                n_tests: int = 5) -> None:
        for pairs, hg in self.str_pairs_HG(classes, n_tests):
            for keys, _ in pairs:
                assert keys in hg  # Test __contains__

    def test_str_pairs_get_set(self, classes: CLASSES = TEST_CLASSES,
                               n_tests: int = 20) -> None:
        self.pairs_test_get_set(self.str_pairs_HG, classes, n_tests)

    def test_str_pairs_pop(self, classes: CLASSES = TEST_CLASSES,
                           n_tests: int = 20) -> None:
        self.pairs_test_pop(self.str_pairs_HG, classes, n_tests)


"""
class TestOOPvsFunctions(TimeTester):

    def test_all_times(self, n_tests_orders_of_magnitude: int = 3):
        func_tester = TestDictFunctions()
        results = set()
        for OOPClass in (TestExclutionary, TestDotDicts, TestInvertionary,
                         TestUpdationary, TestWalktionary):
            oop_tester = OOPClass()
            for method_name in attributes.AttrsOf(OOPClass).method_names():
                if method_name.startswith("test_") and \
                        hasattr(TestDictFunctions, method_name):
                    results.add(self.time_method(
                        method_name, n_tests_orders_of_magnitude,
                        func_tester, oop_tester))

        # Print results (which requires raising an error)
        print(results)
        assert False
"""  # Unquote to time-test; prefixing underscore to method name doesn't work
