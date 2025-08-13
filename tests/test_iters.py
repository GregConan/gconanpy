#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-06
Updated: 2025-08-10
"""
# Import standard libraries
from collections.abc import Generator, Hashable
import random
from timeit import timeit
from typing import Any, TypeVar

# Import local custom libraries
from gconanpy.iters import Combinations, combine_lists, merge, Randoms
from gconanpy.iters.duck import DuckCollection
from gconanpy.testers import Tester


class TestDuckCollection(Tester):
    _K = TypeVar("_K")
    COLLECTYPES = {list, set, tuple}
    EXAMPLES: dict[Hashable, set[type]] = {"This is a sample string": {list, set, tuple, str},
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

    def test_index_1(self) -> None:
        self.add_basics()
        ducks = DuckCollection(self.alist)
        for i in self.alist:
            self.check_result(ducks.index(i), i - 1)
        # TODO ADD MORE TESTS, ESP FOR MAPPINGS

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
