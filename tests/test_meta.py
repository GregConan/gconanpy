#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-08-07
"""
# Import standard libraries
import builtins
from collections import defaultdict
from collections.abc import Callable, Generator, Iterable
from copy import deepcopy
from pprint import pprint
import random
import string
from timeit import timeit
from typing import Any, TypeVar

# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
from gconanpy import attributes
from gconanpy.debug import StrictlyTime
from gconanpy.iters import Combinations, Randoms
from gconanpy.iters.duck import DuckCollection
from gconanpy.mapping.dicts import Cryptionary, Defaultionary, DotDict, \
    Explictionary, LazyDict, LazyDotDict
from gconanpy.meta import Boolable, MultiTypeMeta, name_of, names_of, TimeSpec
from gconanpy.meta.metaclass import MakeMetaclass, name_type_class
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
except (ImportError, ModuleNotFoundError):
    from meta.funcs import method


class BareObject():
    ''' Bare/empty object to freely add new attributes to. Must be defined in
        the same file where it is used. '''

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
        self.check_result(attributes.AttrsOf(self.alist).but_not(self.adict),
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


class TestDuckCollection(Tester):
    _K = TypeVar("_K")
    COLLECTYPES = {list, set, tuple}
    EXAMPLES = {"This is a sample string": {list, set, tuple, str},
                ("This", "is", "a", "string", "tuple"): COLLECTYPES}

    def check_contains(self, ducks: DuckCollection[_K], key: _K,
                       isin: bool) -> bool:
        """ Test __contains__ and isdisjoint methods of DuckCollection

        :return: bool, True `if key in ducks == isin`; else False
        """
        conds = {key in ducks, not ducks.isdisjoint({key}),
                 not ducks.isdisjoint({key: "value"})}
        print(f"{conds} ?= {{{isin}}}")
        return conds == {isin}

    def check_dict(self, adict: dict) -> None:
        ducks = DuckCollection(adict)

        # DuckCollection(Mapping) is equal to its keys
        self.check_result(ducks, adict.keys())

        # Test __contains__ and isdisjoint
        pair = adict.popitem()
        self.check_contains(ducks, pair[0], isin=False)

        # Use __contains__ and __isdisjoin__ to test get, pop, and set_to
        ducks.set_to(*pair)
        self.check_contains(ducks, pair[0], isin=True)
        self.check_result(ducks.get(pair[0]), pair[1])
        self.check_result(ducks.pop(pair[0]), pair[1])
        self.check_contains(ducks, pair[0], isin=False)

        # Use them to test insert and remove
        ducks.insert(pair[1], pair[0])
        self.check_contains(ducks, pair[0], isin=True)
        ducks.remove(pair[0])
        self.check_contains(ducks, pair[0], isin=False)

    def examples(self) -> Generator[tuple[Any, DuckCollection], None, None]:
        for value, collectypes in self.EXAMPLES.items():
            for collectype in collectypes:
                yield value, DuckCollection(collectype(value))

    @staticmethod
    def rand_int_ducks() -> tuple[int, DuckCollection[int]]:
        n_ints = random.randint(Randoms.MIN, Randoms.MAX)
        return n_ints, DuckCollection(list(Randoms.randints(min_n=n_ints,
                                                            max_n=n_ints)))

    def test_add(self) -> None:
        for value, ducks in self.examples():
            old_len = len(ducks)
            ducks.add(value[-5:])
            assert value[-5:] in ducks
            assert len(ducks) in {old_len + len(value[-5:]), old_len + 1}

    def test_clear(self) -> None:
        self.add_basics()
        for collectype in self.COLLECTYPES:
            ducks = DuckCollection(collectype(self.alist))
            ducks.clear()
            self.check_result(ducks.ducks, collectype())

    def test_dict(self, n: int = 10) -> None:
        self.add_basics()
        self.check_dict(self.adict)

        # Test DuckCollection methods on 10 randomly generated dicts
        for _ in range(n):
            self.check_dict(Randoms.randict())

    def test_eq_False(self, n: int = 10) -> None:
        self.add_basics()
        for _ in range(n):
            # Make 2 equal lists of ducks (ints)
            sublist = Randoms.randsublist(self.alist, min_len=1)
            ducks = DuckCollection(sublist)
            ducks2 = DuckCollection(sublist.copy())
            self.check_result(ducks, ducks2)

            # Append a redundant element to differentiate them
            ducks2.add(ducks2.get())
            assert ducks2 != ducks
            assert ducks2 != DuckCollection(set(ducks2))

    def test_eq_True(self) -> None:
        self.add_basics()
        for type1, type2 in Combinations.of_uniques(self.COLLECTYPES, 2, 2):
            for sublist in Combinations.of_uniques(self.alist, max_n=4):
                self.check_result(DuckCollection(type1(sublist)),
                                  DuckCollection(type2(sublist)))

    def test_get_and_pop_ix(self) -> None:
        n_ints, ints = self.rand_int_ducks()
        for i in range(n_ints - 1, 0, -1):
            assert ints.get(i) == ints.pop(i)

    def test_get_and_pop_rand_ix(self, n_tests: int = 10) -> None:
        for _ in range(n_tests):
            n_ints, ints = self.rand_int_ducks()
            for _ in range(n_ints - 1):
                old_len = len(ints)
                pop_ix = random.randint(0, old_len - 1)
                to_pop = ints.get(pop_ix)
                popped = ints.pop(pop_ix)
                self.check_result(popped, to_pop)
                assert ints.get(pop_ix) != to_pop

    def test_pop_no_ix(self) -> None:
        for value, ducks in self.examples():
            old_len = len(ducks)
            if not isinstance(ducks.ducks, set):
                to_pop = value[-1]
            popped = ducks.pop()
            if not isinstance(ducks.ducks, set):
                self.check_result(popped, to_pop)
            self.check_result(len(ducks), old_len - 1)

    def test_remove(self) -> None:
        for value, ducks in self.examples():
            old_len = len(ducks)
            ducks.remove(value[0])
            self.check_result(len(ducks), old_len - 1)


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
        spec = TimeSpec()  # TODO?


class TestMetaFunctions(Tester):
    DISJOINT_CLASSES: set[type] = {
        list, tuple, dict, pd.DataFrame, attributes.AttrsOf}

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

        class DictTestType(metaclass=MakeMetaclass.for_classes(
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
