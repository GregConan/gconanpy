#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-07
Updated: 2025-11-05
"""
# Import standard libraries
import builtins
from collections import defaultdict
from collections.abc import Iterable, Sequence
import random
import string
from timeit import timeit
from typing import Any, TypeVar

# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
from gconanpy.access import attributes
from gconanpy.debug import StrictlyTime
from gconanpy.iters import Combinations
from gconanpy.mapping.dicts import Cryptionary, CustomDict, DotDict, \
    Exclutionary, LazyDict, LazyDotDict, Sortionary
from gconanpy.meta import Boolable, name_of, names_of, \
    Recursively, TimeSpec
# from gconanpy.meta.access import ACCESS, Access
from gconanpy.meta.metaclass import MakeMetaclass, name_type_class
from gconanpy.meta.typeshed import MultiTypeMeta
from gconanpy.testers import Tester


class TestAccessSpeed(Tester):
    # Remove initial underscore to test_access_speed to view time test
    def _test_access_speed(self) -> None:
        self.add_basics()
        randstr = "".join(random.choices(
            string.ascii_letters + string.digits, k=100))
        arbitraries = dict(anint=-1234, atup=(1, 2, 3), alist=self.alist,
                           adict=self.adict, afloat=-3.14159265358,
                           astr=f"'{randstr}'")
        # allattrs = ('anint', 'atup', 'alist', 'adict', 'afloat', 'astr')
        allattrs = tuple(arbitraries)
        to_test = ("obj.{}",  # Test default getters
                   "adict['{}']",
                   "adict.get('{}')",
                   "getattr(obj, '{}')",
                   "hasattr(obj, '{}')",
                   "operator.getitem(adict, '{}')",
                   "operator.contains(adict, '{}')",
                   "dict.__contains__(adict, '{}')",
                   "'{}' in adict",
                   "dict.__getitem__(adict, '{}')",
                   "dict.get(adict, '{}')",
                   "Mapping.get(adict, '{}')",
                   "object.__getattribute__(obj, '{}')",

                   # Test custom getters from meta/__init__.py
                   "getdefault(adict, '{}')",
                   "method_get(adict, '{}')",
                   "method_getattribute(obj, '{}')",
                   "method_getitem(adict, '{}')",

                   # Test custom getters from meta/access.py
                   "Access.item.get(adict, '{}')",
                   "Access.item.getdefault(adict, '{}')",
                   "Access.item.contains(adict, '{}')",
                   "Access.attribute.get(obj, '{}')",
                   "Access.attribute.contains(obj, '{}')",
                   "ACCESS['item'].get(adict, '{}')",
                   "ACCESS['item'].getdefault(adict, '{}')",
                   "ACCESS['item'].contains(adict, '{}')",
                   "ACCESS['attribute'].get(obj, '{}')",
                   "ACCESS['attribute'].contains(obj, '{}')",

                   # Test default setters
                   "setattr(obj, '{}', None)",
                   "object.__setattr__(obj, '{}', None)",
                   "dict.setdefault(adict, '{}', None)",
                   "adict.setdefault('{}', None)",
                   "setdefault(adict, '{}', None)",
                   "adict['{}'] = None",
                   "obj.{} = None",

                   # Test custom setters
                   "method_setattr(obj, '{}', None)",
                   "method_setitem(adict, '{}', None)",
                   "attributes.setdefault(obj, '{}', None)",
                   "Access.item.set_to(adict, '{}', None)",
                   "Access.attribute.set_to(obj, '{}', None)",
                   "ACCESS['item'].set_to(adict, '{}', None)",
                   "ACCESS['attribute'].set_to(obj, '{}', None)")

        SETUP = f"""import operator
from typing import Mapping

try:
    from gconanpy import attributes
    from gconanpy.meta import method
    from gconanpy.meta.access import ACCESS, Access, getdefault, setdefault
except (ImportError, ModuleNotFoundError):
    import attributes
    from meta import method
    from meta.access import ACCESS, Access, getdefault, setdefault


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
            timeit(eachcall.format(ex), setup=SETUP, number=200000)
            for ex in allattrs]) for eachcall in to_test}  # for _ in range(5)
        # sumtimes = {x: 0.0 for x in times.keys()}
        sumtimes = defaultdict(float)
        keys = defaultdict(set)
        newkeys = ("dict", "method", "operator", "Mapping", "adict", "access",
                   "Access", "ACCESS", "attributes")
        for k in times:
            new_key = None
            for new_k in newkeys:
                if k.startswith(new_k):
                    new_key = new_k
                    break
            if not new_key:
                new_key = "adict" if k.endswith("adict") \
                    else "attr" if len(k) > 7 and k[3:7] == "attr" \
                    else "access" if k[1:10] == "etdefault" else "default"
            keys[new_key].add(k)

        # Sort each access method, and category average thereof, by time taken
        for newkey, oldkeys in keys.items():
            for old in oldkeys:
                sumtimes[newkey] += times[old]
            sumtimes[newkey] /= len(oldkeys)
        to_print = [f"{k} = {round(v * 1000, 3)}" for d in (times, sumtimes)
                    for k, v in Sortionary(**d).sorted_by("values")]

        # Check how far to the right to justify the printed text so all of the
        # times line up in the output, then print them
        indent = max(len(eachline) for eachline in to_print)
        for eachline in to_print:
            print(eachline.rjust(indent))

        assert False


class TestMetaClasses(Tester):
    _T = TypeVar("_T")

    def assert_that_all(self, objects: Iterable[Any], *,
                        is_if: MultiTypeMeta._TypeChecker = isinstance,
                        is_a: MultiTypeMeta._TypeArgs = (),
                        isnt_a: MultiTypeMeta._TypeArgs = ()) -> None:
        for an_obj in objects:
            assert (not is_a) or is_if(an_obj, is_a)
            if is_a != isnt_a:
                for true_kwargs in Combinations.of_map({"is_a": is_a,
                                                        "isnt_a": isnt_a}):
                    assert MultiTypeMeta.check(an_obj, is_if, **true_kwargs)

                assert not is_if(an_obj, isnt_a)
                for false_kwargs in Combinations.of_map({"is_a": isnt_a,
                                                        "isnt_a": is_a}):
                    if any(false_kwargs.values()):
                        assert not MultiTypeMeta.check(
                            an_obj, is_if, **false_kwargs)

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
        for classes in Combinations.of_objects(self.DISJOINT_CLASSES):
            self.check_result(names_of(classes), [name_of(x) for x in classes])

    def test_name_type_class(self, n_variants: int = 100,
                             n_runs: int = 100) -> None:
        subsets = [*Combinations.of_objects(self.DISJOINT_CLASSES)]
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
        subclasses = (dict, CustomDict, Exclutionary, DotDict)
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


class TestRecursively(Tester):
    NEST_AT: int = -1
    NEW_VAL: Any = "hello"

    @classmethod
    def nested_list(cls, levels: int = 3, nest_at: int = NEST_AT,
                    to_nest: Any = NEW_VAL, others: Sequence = tuple()
                    ) -> list:
        return [*others[:nest_at], to_nest if levels < 1 else cls.nested_list(
            levels - 1, nest_at, to_nest, *others
        ), *others[nest_at:]]

    def get_nested_lists(self, ix: int = NEST_AT, diff: Any = NEW_VAL
                         ) -> tuple[list, list]:
        self.add_basics()
        nested = self.nested_list()
        expected = nested.copy()
        expected[ix][ix][ix] = diff
        return nested, expected

    def test_Recursively_setitem(self) -> None:
        IX = self.NEST_AT
        VAL = self.NEW_VAL
        nested, expected = self.get_nested_lists(IX, VAL)
        Recursively.setitem(nested, (IX, IX, IX), VAL)
        self.check_result(nested, expected)

    def test_Recursively_getitem(self) -> None:
        IX = self.NEST_AT
        VAL = self.NEW_VAL
        _, nested = self.get_nested_lists(IX, VAL)
        self.check_result(Recursively.getitem(nested, (IX, IX, IX)), VAL)
