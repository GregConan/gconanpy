#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-07-20
"""
# Import standard libraries
import builtins
from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
from pprint import pprint
import random
import string
import time
from timeit import timeit
from typing import Any, TypeVar

# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
from gconanpy import attributes
from gconanpy.debug import StrictlyTime
from gconanpy.mapping import Combinations
from gconanpy.mapping.dicts import Cryptionary, Defaultionary, DotDict, \
    Explictionary, LazyDict, LazyDotDict
from gconanpy.meta.classes import Boolable, MultiTypeMeta, TimeSpec
from gconanpy.meta.funcs import metaclass_issubclass, name_of, \
    name_type_class, names_of
from gconanpy.testers import Tester
from gconanpy.trivial import always_false, always_none, always_true


class TestAccessSpeed(Tester):
    # Remove initial underscore to test_access_speed to view time test
    def _test_access_speed(self) -> None:
        self.add_basics()
        randstr = "".join(random.choices(
            string.ascii_letters + string.digits, k=100))
        arbitraries = dict(anint=-1234, atup=(1, 2, 3), alist=self.alist,
                           adict=self.adict, afloat=-3.14159265358,
                           astr=f"'{randstr}'")
        allattrs = ('anint', 'atup', 'alist', 'adict', 'afloat', 'astr')
        to_test = ("obj.{}",
                   "adict['{}']",
                   "getattr(obj, '{}')",
                   "hasattr(obj, '{}')",
                   "method_get(adict, '{}')",
                   "method_getattribute(obj, '{}')",
                   "method_getitem(adict, '{}')",
                   "operator.getitem(adict, '{}')",
                   "operator.contains(adict, '{}')",
                   "dict.__contains__(adict, '{}')",
                   "'{}' in adict",
                   "dict.__getitem__(adict, '{}')",
                   "dict.get(adict, '{}')",
                   "Mapping.get(adict, '{}')",
                   "object.__getattribute__(obj, '{}')",
                   "setattr(obj, '{}', None)",
                   "object.__setattr__(obj, '{}', None)",
                   "method_setattr(obj, '{}', None)",
                   "method_setitem(adict, '{}', None)",
                   "adict['{}'] = None",
                   "obj.{} = None")

        SETUP = f"""import operator
from typing import Mapping

try:
    from gconanpy.meta.funcs import method
    from gconanpy.trivial import BareObject
except (ImportError, ModuleNotFoundError):
    from meta.funcs import method
    from trivial import BareObject

method_get = method('get')
method_getattribute = method('__getattribute__')
method_getitem = method('__getitem__')
method_setattr = method('__setattr__')
method_setitem = method('__setitem__')

obj = BareObject()
obj.anint={arbitraries['anint']}
obj.atup={arbitraries['atup']}
obj.alist={arbitraries['alist']}
obj.adict={arbitraries['adict']}
obj.afloat={arbitraries['afloat']}
obj.astr={arbitraries['astr']}

adict={arbitraries}
allattrs={allattrs}
"""
        times = {eachcall: sum([
            timeit(eachcall.format(ex), setup=SETUP, number=100000)
            for ex in allattrs]) for eachcall in to_test}  # for _ in range(5)
        # sumtimes = {x: 0.0 for x in times.keys()}
        sumtimes = defaultdict(float)
        keys = defaultdict(set)
        newkeys = ("dict", "method", "operator", "Mapping", "adict")
        for k in times:
            new_key = None
            for new_k in newkeys:
                if k.startswith(new_k):
                    new_key = new_k
                    break
            if not new_key:
                new_key = "adict" if k.endswith("adict") \
                    else "attr" if len(k) > 7 and k[3:7] == "attr" \
                    else "default"
            keys[new_key].add(k)

        for newkey, oldkeys in keys.items():
            for old in oldkeys:
                sumtimes[newkey] += times[old]
            sumtimes[newkey] /= len(oldkeys)

        for d in times, sumtimes:
            pprint({k.rjust(40): round(v * 1000, 3)
                    for k, v in d.items()})
        assert False


class TestAttributesOf(Tester):
    _LazyMeth = Callable[[Any, str, Callable], Any]
    NO_EXPECTED = object()
    TRIVIALS = {False: always_false, True: always_true, None: always_none}

    class HasFoo:
        foo: Any

    def test_but_not(self) -> None:
        self.add_basics()
        self.check_result(attributes.Of(self.alist).but_not(self.adict),
                          set(dir(list)) - set(dir(dict)))

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


class TestMetaClasses(Tester):
    _T = TypeVar("_T")

    def assert_that_all(self, objects: Iterable[Any], *,
                        is_if: MultiTypeMeta._TypeChecker = isinstance,
                        is_a: MultiTypeMeta._TypeArgs = (object, ),
                        isnt_a: MultiTypeMeta._TypeArgs = tuple()) -> None:
        for an_obj in objects:
            assert is_if(an_obj, is_a)
            for true_kwargs in Combinations.of_map({"is_a": is_a,
                                                    "isnt_a": isnt_a}):
                assert MultiTypeMeta.check(an_obj, is_if, **true_kwargs)

            assert not is_if(an_obj, isnt_a)
            for false_kwargs in Combinations.of_map({"is_a": isnt_a,
                                                     "isnt_a": is_a}):
                assert not MultiTypeMeta.check(an_obj, is_if, **false_kwargs)

    def test_Boolable_builtins(self) -> None:
        self.assert_that_all(vars(builtins).values(), is_a=Boolable)

    def test_not_Boolable(self) -> None:
        self.assert_that_all((pd.DataFrame(), pd.Series()), isnt_a=Boolable)

    def test_TimeSpec(self) -> None:
        spec = TimeSpec()


class TestMetaFunctions(Tester):
    DISJOINT_CLASSES: set[type] = {
        list, tuple, dict, pd.DataFrame, attributes.Of}

    def test_names_of(self) -> None:
        for classes in Combinations.of_seq(self.DISJOINT_CLASSES):
            self.check_result(names_of(classes), [name_of(x) for x in classes])

    def test_name_type_class(self) -> None:
        n_variants = 100
        n_runs = 100
        subsets = [*Combinations.of_seq(self.DISJOINT_CLASSES)]
        for _ in range(n_variants):
            subclasses = random.choice(subsets)
            not_subclasses = self.DISJOINT_CLASSES - set(subclasses)
            for nameit in (name_type_class, ):  # , name_type_class2):
                name = ""
                with StrictlyTime(f"running {name_of(nameit)}"):
                    for _ in range(n_runs):
                        nameit(subclasses, not_subclasses)
                name = nameit(subclasses, not_subclasses)
                for each_class in self.DISJOINT_CLASSES:
                    class_name = name_of(each_class).capitalize()
                    if not class_name in str(name):
                        raise ValueError(
                            f"'{name}' is not the right name for Is("
                            f"{names_of(subclasses)})ButIsNot("
                            f"{names_of(not_subclasses)}). "
                            f"{name_of(nameit)} failed because '{class_name}'"
                            f"is not in '{name}'.")

    def test_metaclass_issubclass(self) -> None:
        self.add_basics()
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
