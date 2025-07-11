#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-06
Updated: 2025-07-09
"""
# Import standard libraries
from collections.abc import Sequence
from timeit import timeit
from typing import Any

# Import local custom libraries
from gconanpy.seq import combine_lists, merge, Recursively
from gconanpy.testers import Randoms, Tester


class TestSeq(Tester):
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


class TestMerge(Tester):
    MIN = 1    # Default minimum number of items/tests
    MAX = 100  # Default maximum number of items/tests

    def test_combine_lists(self, max_n: int = 10) -> None:
        self.add_basics()
        for n in range(1, max_n):
            self.check_result(combine_lists(
                [self.alist] * n), self.alist * n)

    def test_merge_dicts_1(self, min_len: int = MIN, max_len: int = MAX,
                           max_n: int = MAX) -> None:
        for _ in range(max_n):
            dicts = list()
            expected = dict()
            for _ in Randoms.randrange(min_len, max_len):
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

    def test_times(self, n_tests: int = 10, n_reps: int = 100,
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
