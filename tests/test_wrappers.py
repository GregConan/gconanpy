#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2026-03-04
"""
# Import standard libraries
from collections.abc import Callable, Generator
import re

# Import local custom libraries
# from gconanpy.ToString import *
from gconanpy.IO.web import URL
from gconanpy.iters import copy_range, invert_range, Randoms
from gconanpy.testers import Tester
from gconanpy.wrappers import Branches, Sets, SoupTree, WrapFunction


class TestSets(Tester):
    N_TESTS: int = 25
    randintsets: Callable[..., list[set[int]]] = \
        WrapFunction(Randoms.randintsets, min_n=10, max_n=20,
                     min_len=N_TESTS, max_len=N_TESTS)

    def asc_desc_Sets(self, n_tests: int = 20, max_int: int = 20,
                      ) -> Generator[tuple[Sets, Sets, Sets], None, None]:
        for each_int in Randoms.randints(min_n=n_tests, max_n=n_tests,
                                         min_int=2, max_int=max_int):
            asc_range = range(each_int)
            dsc_range = invert_range(asc_range)  # TODO FIX
            ascending = Sets[int]({a} for a in asc_range)
            assert ascending
            descending = Sets[int]({d} for d in dsc_range)
            assert descending
            both = Sets[int]({i, j} for i, j in zip(copy_range(asc_range),
                                                    copy_range(dsc_range)))
            assert both
            yield ascending, descending, both

    def test_differentiate_and_merge(self) -> None:
        sets = Sets[int](({1, 2, 3, 4, 5}, {4, 5, 6, 7, 8}, {6, 7, 8, 9, 10}))
        self.check_result(Sets[int](sets.differentiate()),
                          Sets[int](({1, 2, 3}, set(), {9, 10})))
        self.check_result(sets.merge(), set[int](range(1, 11)))

    def test_differentiate(self) -> None:
        for bigset in self.randintsets():
            randcount = Randoms.randcount()
            sets = Sets[int]((set(Randoms.randsublist(list(bigset)))
                              for _ in randcount))
            differentiated = sets.differentiate()
            for postdif in differentiated:
                for otherset in differentiated:
                    if postdif != otherset:
                        assert postdif.isdisjoint(otherset)

    def test_filter(self) -> None:
        sets = Sets[int](((1, 2, 3), (3, 4, 5, 6), (1, 9, 10)))
        self.check_result(Sets[int](sets.filter(lambda x: x > 5)),
                          Sets[int]((tuple(), (6, ), (9, 10))))

    def test_intersection(self) -> None:
        int_bounds = dict[str, int](min_int=-10, max_int=10)
        self.check_result(Sets[int](((1, 2, 3), (1, 4, 5), (1, 6, 7, 8),
                                     (1, 9, 10))).intersection(), {1})
        self.check_result(Sets[int](((1, 2, 3), (4, 5, 6), (6, 7, 8))
                                    ).intersection(), set())
        for set1 in self.randintsets(**int_bounds):
            others = Sets(Randoms.randintsets(**int_bounds))
            intersected = set(set1).copy()
            for eachset in (set1, *others):
                intersected.intersection_update(eachset)
            self.check_result(Sets((set1, *others)).intersection(),
                              intersected)

    def test_union_each(self) -> None:  # TODO FIX invert_range
        for ascending, descending, both in self.asc_desc_Sets():
            unioned = Sets(tuple(
                ascending.union_each(descending)))  # type: ignore  # TODO?
            self.check_result(unioned, both)

    def test_unique(self) -> None:
        self.check_result(Sets(({1, 2}, {1, 3}, {1, 2, 4}, {1})
                               ).unique(), {3, 4})

        # Test that for Sets with no shared items, unique() == union()
        ints = set(Randoms.randints())  # get random unique integers
        intsets = Sets({i} for i in ints)  # split them, each in its own set
        self.check_result(intsets.union(), intsets.unique())

    def test_update_each(self) -> None:  # TODO FIX invert_range
        for ascending, descending, both in self.asc_desc_Sets():
            ascending.update_each(descending)
            self.check_result(ascending, both)


class TestSoupTree(Tester):
    def test_SoupTree_prettify(self) -> None:
        soup = self.get_soup()
        stree = SoupTree.from_soup(soup)
        branch = Branches()
        invalid = re.compile(f"({branch.T})(?:{branch.O})*"
                             f"({branch.I}|{branch.L}|{branch.T})")
        pretty = stree.prettify(branch=branch)
        assert invalid.match(pretty) is None


class TestURL(Tester):
    GDOCS_URL = "https://docs.google.com/document/d/a1b2c3/edit" \
        "?tab=t.abc123&heading=h.def456&key=12345"

    def test_from_parts(self):
        url = URL.from_parts("docs.google.com", "document",
                             "d", "a1b2c3", "edit",
                             tab="t.abc123", heading="h.def456", key=12345)
        self.check_result(url, self.GDOCS_URL)

    def test_without_params(self):
        url = URL(self.GDOCS_URL)
        self.check_result(url.without_params,
                          self.GDOCS_URL.split("?", 1)[0])
