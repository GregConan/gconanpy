#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-06
Updated: 2026-04-10
"""
# Import standard libraries
import random
from timeit import timeit

# Import local custom libraries
from gconanpy.iters import combine_lists, invert_range, merge, Randoms
from gconanpy.iters.filters import MapSubset
from gconanpy.testers import Tester


class TestMapSubset(Tester):
    def test_keys_are(self) -> None:
        self.add_basics()
        subsetter = MapSubset(keys_are=("a", "b"))
        print(f"filter: {vars(subsetter)}")
        self.check_result(subsetter.of(self.adict),
                          dict(a=1, b=2))


class TestMerge(Tester):
    MIN = 1    # Default minimum number of items/tests
    MAX = 100  # Default maximum number of items/tests

    def test_combine_lists(self, max_n: int = 10) -> None:
        self.add_basics()
        for n in range(1, max_n):
            self.check_result(combine_lists([self.alist] * n),
                              self.alist * n)

    def test_merge_dicts_1(self, min_len: int = MIN, max_len: int = MAX,
                           max_n: int = MAX) -> None:
        for _ in range(max_n):
            dicts = []
            expected = {}
            for _ in Randoms.randcount(min_len, max_len):
                adict = Randoms.randict()
                dicts.append(adict)
                expected.update(adict)
            self.check_result(merge(dicts), expected)

    def test_merge_dicts_2(self) -> None:
        self.add_basics()
        dicts = [self.adict, dict(d=4), dict(e=5), dict(b=6, e=7), dict(f=8)]
        self.check_result(merge(dicts), dict(a=1, b=6, c=3, d=4, e=7, f=8))

    def test_merge_sets(self, max_n: int = MAX) -> None:
        for _ in range(max_n):
            sets = Randoms.randintsets()
            expected = sets[0].union(*sets[1:])
            self.check_result(merge(sets), expected)

    # Remove the initial underscore to run time test
    def _test_times(self, n_tests: int = 10, n_reps: int = 100,
                    max_len: int = 25):
        merges = {"union": "set.union",
                  "update": "lambda x,y: x.update(y) or x"}
        SETUP = "from functools import reduce\nsets={}"
        STMT = "reduce({}, sets)"
        time_taken = {x: 0.0 for x in merges}
        for _ in range(n_tests):
            setup = SETUP.format(Randoms.randintsets(max_len=max_len))
            for which, merge_fn in merges.items():
                time_taken[which] += timeit(STMT.format(merge_fn),
                                            setup=setup, number=n_reps)
        assert merges["update"] < merges["union"]


class TestRandoms(Tester):
    def test_randtuples_unique(self, n_tests: int = 1000) -> None:
        for _ in range(n_tests):
            width = 2  # random.randint(2, Randoms.MAX)
            length = random.randint(2, Randoms.MAX)
            tuples = Randoms.randtuples(min_n=width, max_n=width,
                                        min_len=length,
                                        max_len=length, unique=True)
            self.check_result(len(set(tuples)), len(tuples))


class TestRangeFunctions(Tester):
    """
    def test_copy_invert_range(self, n_tests: int = 10) -> None:
        for _ in Randoms.randcount(n_tests, n_tests):
            a_range = Randoms.randrange()
            self.check_result(
                [x for x in reversed(copy_range(a_range))],
                [y for y in a_range])
    """  # TODO

    def test_invert_range(self, n_tests: int = 10) -> None:
        for _ in range(n_tests):
            a_range = Randoms.randrange()
            self.check_result(
                [x for x in invert_range(invert_range(a_range))],
                [y for y in a_range])
