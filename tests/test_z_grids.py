#!/usr/bin/env python3

"""
Test gconanpy/mapping/grids.py classes last (hence the 'z' in the file name)
because they currently take so much longer to run than any other tests.
Greg Conan: gregmconan@gmail.com
Created: 2025-04-10
Updated: 2026-04-10
"""
# Import standard libraries
from collections.abc import Callable, Generator
import pdb
import random
import string
from typing import Any, ParamSpec, TypeVar

# Import local custom libraries
from gconanpy.iters import duplicates_in, Randoms
from gconanpy.mapping.grids import HashGrid, Locktionary  # GridCryptionary,
from .test_mapping import DictTester

# Type hint variables
_P = ParamSpec("_P")  # for TestAttrMap
_T = TypeVar("_T")  # for TestHashGrid


class TestHashGrid(DictTester):
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
