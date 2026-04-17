#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-04-10
Updated: 2026-04-17
"""
# Import standard libraries
from collections.abc import Collection, Generator, Hashable, Mapping
import random
from typing import Any, cast, TypeVar

# Import local custom libraries
from gconanpy.iters import Combinations, Randoms
from gconanpy import collection
from gconanpy.collection.classes import DuckCollection  # , SimpleDuckCollection
from gconanpy.testers import Tester


# Type variables
_T = TypeVar("_T")


class TestDuckCollection(Tester):
    # Map example data to the type of container it can be converted into
    COLLECTYPES = {list, set, tuple}
    EXAMPLES: dict[Hashable, set[type]] = {
        "This is a sample string": {list, set, tuple, str},
        ("This", "is", "a", "string", "tuple"): COLLECTYPES}

    def check_contains(self, ducks: DuckCollection[_T], key: _T,
                       isin: bool) -> bool:
        """ Test `__contains__` and `isdisjoint` methods of `DuckCollection`

        :return: bool, True `if ((key in ducks) == isin)`; else False
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
        pair = adict.popitem()  # key-value pair
        self.check_contains(ducks, pair[0], isin=False)

        # Use __contains__ and __isdisjoint__ to test get, pop, and set_to
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


class TestCollectionFunctions(Tester):
    _NESTED_INTS = tuple[tuple[int, ...], ...]

    def example_ints(self, inputs2output: Mapping[tuple[int, ...], _T],
                     vary_output_type: bool = True
                     ) -> Generator[tuple[Collection[int], Collection[int], _T
                                          ], None, None]:
        self.add_basics()
        to_check = self.alist
        for coll_type in (set[int], list[int]):
            for compare_to, result in inputs2output.items():
                yield to_check, coll_type(compare_to), result
                yield coll_type(to_check), coll_type(compare_to), result
                if vary_output_type:
                    yield to_check, compare_to, result
                    yield coll_type(to_check), compare_to, result

    def int_in2out(self) -> dict[tuple[int, ...], bool]:
        self.add_basics()
        return {(0, 6): False, (0, 5): False, (1, 6): False, (5, ): True,
                tuple[int, ...](self.alist): True, (1, 2, 3): True}

    def test_list_add(self) -> None:
        self.add_basics()
        collection.add(self.alist, 6)
        self.check_result(self.alist, [1, 2, 3, 4, 5, 6])

    def test_list_difference(self) -> None:
        self.add_basics()
        self.check_result(collection.difference(
            self.alist, {0, 1, 2, 3}), [4, 5])

    def test_list_difference_update(self) -> None:
        test_data = {(0, 1, 2, 3): (4, 5)}
        # for to_check, in_ints, out_ints in self.example_ints(test_data, False):
        self.add_basics()
        collection.difference_update(self.alist, {0, 1, 2, 3})
        self.check_result(self.alist, [4, 5])

    def test_list_intersection(self) -> None:
        self.add_basics()

        # Verify membership
        self.check_result(collection.intersection(
            self.alist, [1, 2, 3], [3, 4, 5]), [3])

        # Verify order
        self.check_result(collection.intersection(self.alist, [4, 2]), [2, 4])

    def test_intersection_update(self) -> None:
        self.add_basics()
        for col_type in (set[int], list[int]):
            a_col = col_type(self.alist)
            for to_intersect, result in (  # Order matters
                (([1, 2, 3], [2, 3, 4], [3, 2]), col_type([2, 3])),
                (([1, 2], [2, 4, 5]), col_type([2]))
            ):
                print(f"intersection_update({a_col}, *{to_intersect}) should "
                      f"produce {result}", end=". ")
                collection.intersection_update(a_col, *to_intersect)
                print(f"It produced {a_col}.")
                self.check_result(a_col, result)

    def test_isdisjoint(self) -> None:
        test_data = {(0, 6): True, (0, 5): False, (1, 6): False}
        for to_check, compare_to, result in self.example_ints(test_data):
            self.check_result(collection.isdisjoint(to_check, compare_to
                                                    ), result)

    def test_issubset(self) -> None:
        for to_check, subset, result in self.example_ints(self.int_in2out()):
            print(f"Is {subset} a subset of {to_check}?", end=" ")
            self.check_result(collection.issubset(subset, to_check), result)
            print("Yes." if result else "No.")

    def test_issuperset(self) -> None:
        for to_check, subset, result in self.example_ints(self.int_in2out()):
            print(f"Is {to_check} a superset of {subset}?", end=" ")
            self.check_result(collection.issuperset(
                to_check, subset), result)
            print("Yes." if result else "No.")

    def test_symmetric_difference(self) -> None:
        self.add_basics()
        test_data = {(4, 5, 6, 7, 8): (1, 2, 3, 6, 7, 8)}
        for coll_type in (set[int], list[int]):
            to_check = coll_type(self.alist)
            for in_ints, out_ints in test_data.items():
                diff = collection.symmetric_difference(to_check, in_ints)
                self.check_result(diff, coll_type(out_ints))

    def test_symmetric_difference_update(self) -> None:
        self.add_basics()
        test_data = {(4, 5, 6, 7, 8): (1, 2, 3, 6, 7, 8)}  # TODO Add more
        for coll_type in (set[int], list[int]):
            to_check = coll_type(self.alist)
            for in_ints, out_ints in test_data.items():
                collection.symmetric_difference_update(to_check, in_ints)
                self.check_result(to_check, coll_type(out_ints))

    def test_list_union(self) -> None:
        self.add_basics()
        unioned = cast(list[int], collection.union(
            self.alist, [4, 5, 6, 7, 8]))

        # Verify that initial list order is unchanged
        self.check_result(unioned[:len(self.alist)], [1, 2, 3, 4, 5])

        # Verify that all new elements are included
        unioned_set = set(unioned)
        self.check_result(unioned_set, {1, 2, 3, 4, 5, 6, 7, 8})
