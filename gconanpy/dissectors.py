#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap abstract data structures.
Extremely useful and convenient for debugging, but not necessary otherwise.
Overlaps significantly with:
    emailbot/debugging.py, Knower/debugging.py, audit-ABCC/src/utilities.py, \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-03-13
"""
# Import standard libraries
from abc import ABC
import itertools
import pdb
from typing import (Any, Callable, Dict, Hashable,
                    Iterable, List, Mapping, Set)

# Import local custom libraries
try:
    from seq import stringify_list, uniqs_in
except ModuleNotFoundError:
    from gconanpy.seq import stringify_list, uniqs_in


class DifferenceBetween:
    difference: str | None
    diffs: List[str | None]

    def __init__(self, *args: Any, **kwargs: Any):
        """ Identify difference(s) between any Python objects or values.

        :param args: Iterable[Any] of objects to compare.
        :param kwargs: Mapping[str, Any] of names to objects to compare.
        """
        self.difference = None
        self.comparables = list()
        self.names = list()

        for name, to_compare in kwargs.items():
            self.names.append(name)
            self.comparables.append(to_compare)

        for arg in args:
            self.comparables.append(arg)
            arg_type = type(arg).__name__
            arg_name = arg_type
            i = 1
            while arg_name in self.names:
                i += 1
                arg_name = f"{arg_type}{i}"
            self.names.append(arg_name)

        self.is_different = not self.are_all_equal(self.comparables)
        self.diffs = self.find_difference() if self.is_different else None

    def find_difference(self) -> list | None:
        """ Find the difference(s) between the objects in self.comparables.
        Returns the first difference found, not an exhaustive list.

        :return: list | None, the values that differ between the objects, or
                 None if no difference is found.
        """
        types = self.compare_their("type", type)
        if self.difference:
            return types

        try:
            lens = self.compare_their("length", len)
            if self.difference:
                return lens

            try:
                diff_keys = self.compare_sets("key", dict.keys, dict.get)
                if self.difference:
                    return diff_keys
            except (AttributeError, TypeError):
                pass

            try:
                diff_elements = self.compare_all_in(
                    [x for x in range(lens[0])], "element", lambda x, i: x[i])
                if self.difference:
                    return diff_elements
            except KeyError:
                pass

        except TypeError:
            pass

        diff_attrs = self.compare_sets("unique attribute(s)", dir, getattr)
        if self.difference:
            return diff_attrs

    def compare_sets(self, on: str, get_strings: Callable[[Any], Iterable[str]],
                     get_subcomparator: Callable[[Any, Any], Any]) -> list:
        """

        :param on: str, name of the possible difference to find
        :param get_strings: Callable[[Any], Iterable[str]], _description_
        :param get_subcomparator: Callable[[Any, Any], Any], _description_
        :return: list, _description_
        """
        comparables = self.compare_their(on, set, get_strings)
        if self.difference:
            to_return = [None] * len(comparables)
            for i in range(len(comparables)):
                for other_set in comparables[:i] + comparables[i+1:]:
                    to_return[i] = comparables[i] - other_set
        else:
            to_return = self.compare_all_in(comparables[0], on,
                                            get_subcomparator)
        return to_return

    def compare_all_in(self, comparables: Iterable, on: str,
                       get_subcomparator: Callable[[Any, Any], Any]
                       ) -> list | None:  # tuple[Any, Any] | None:
        """ 

        :param comparables: Iterable, objects to compare to each other.
        :param on: str, name of the comparables' possible difference to find.
        :param get_subcomparator: Callable[[Any, Any], Any], _description_
        :return: list | None, _description_
        """
        pair = None
        on_iter = iter(comparables)
        next_name = next(on_iter, None)
        while next_name is not None and not self.difference:
            pair = self.compare_their(f"{on} {next_name}", lambda y:
                                      get_subcomparator(y, next_name))
            next_name = next(on_iter, None)
        return pair

    def compare_their(self, on: str, *comparablifiers: Callable[[Any], Any]
                      ) -> list:
        """ 

        :param on: str, name of the possible difference to find
        :param comparablifiers: Iterable[Callable[[Any], Any]] \
            listing 1-arg-to-1-arg functions that extract things to compare
        :return: list, _description_
        """
        difference, comparables = self.compare(
            self.comparables.copy(), on, self.difference, *comparablifiers)
        self.difference = difference
        return comparables

    @classmethod
    def compare(cls, comparables: Iterable, on: str,
                difference: str | None,
                *comparablifiers: Callable[[Any], Any],
                skip: type | None = Callable
                ) -> tuple[str | None, list]:
        """ 

        :param comparables: Iterable, objects to compare to each other.
        :param on: str, name of the possible difference to find
        :param difference: str | None, name of a difference already found
        :param comparablifiers: Iterable[Callable[[Any], Any]]
        :param skip: None | type, comparables to ignore, Callable by default
        :return: tuple[str | None, list], comparable as
        """

        for get_comparator in reversed(comparablifiers):
            for i in range(len(comparables)):
                comparables[i] = get_comparator(comparables[i])

        difference = None if any([isinstance(x, skip) for x in comparables]
                                 ) or cls.are_all_equal(comparables) else on

        return difference, comparables

    @classmethod
    def are_all_equal(cls, comparables: Iterable) -> bool:
        """ `are_all_equal([x, y, z])` means `x == y == z`.

        :param comparables: Iterable of objects to check for equality.
        :return: bool, True if every item in comparables is equal to every
                 other item, otherwise False.
        """
        are_equal = True
        looping = True
        combos_iter = itertools.combinations(comparables, 2)
        while looping and are_equal:
            next_pair = next(combos_iter, None)
            if not next_pair:  # is None:
                looping = False
            elif next_pair[0] != next_pair[1]:
                are_equal = False
        return are_equal

    def __repr__(self) -> str:
        """ 
        :return: str, human-readable summary of how self.comparables differ.
        """
        if self.difference:
            differences = stringify_list([
                f"{self.difference} of {self.names[i]} == {self.diffs[i]}"
                for i in range(len(self.diffs))], quote=None)
            result = f"{self.difference} differs between " \
                f"{stringify_list(self.names)}:\n{differences}."
        elif self.is_different:
            result = f"A difference between {stringify_list(self.names)} " \
                "exists, but it could not be identified."
        else:
            result = " == ".join(self.names)
        return result


class Peeler(ABC):

    @staticmethod
    def can_peel(an_obj: Any) -> bool:  # TODO REFACTOR (VERY INELEGANT!)
        """ 
        :param an_obj: Any
        :return: bool, True if you can run Peeler.peel(an_obj) or \
                 Peeler.core(an_obj) without error, else False
        """
        result = False
        if isinstance(an_obj, Iterable):
            primitivity = [
                hasattr(an_obj, "__mod__"),  # ONLY in primitives
                not hasattr(an_obj, "__class_getitem__"),  # NOT in them
                isinstance(an_obj, Hashable)]
            result = primitivity.count(True) < 2
        return result

    @classmethod
    def core(cls, to_peel: Iterable) -> Any:
        """ Extract the biggest (longest) datum from a nested data structure.

        :param to_peel: Iterable, especially a nested container data structure
        :return: Any, the longest datum buried in to-peel's nested layers
        """
        fruits = cls.peel(to_peel)
        if len(fruits) > 1:
            sizes = [len(f) for f in fruits]
            biggest = fruits[sizes.index(max(sizes))]
        else:
            biggest = fruits[0]
        return biggest

    @classmethod
    def peel(cls, to_peel: Iterable) -> list:
        """ Extract data from bothersome nested container data structures.

        :param to_peel: Iterable, especially a nested container data structure
        :return: list, all data buried in to_peel's nested container layers, \
                 regardless of its exact location inside to_peel
        """
        if cls.can_peel(to_peel):
            try:
                fruit_lists = [cls.peel(to_peel[k])
                               for k in to_peel.keys()]
            except AttributeError:
                fruit_lists = [cls.peel(item) for item in to_peel]
            fruits = list(itertools.chain(*fruit_lists))
        else:
            # fruits.append(to_peel)
            fruits = [to_peel, ]
        return fruits

    @staticmethod
    def peel_dict(a_dict: Mapping) -> Mapping:
        while len(a_dict.keys()) < 2:
            _, a_dict = a_dict.popitem()
        return a_dict


class Xray(list):
    """Given any object, easily check what kinds of things it contains.
    Extremely convenient for interactive debugging."""

    def __init__(self, an_obj: Any, list_its: str | None = None) -> None:
        """ Given any object, easily check what kinds of things it contains. 

        :param an_obj: Any
        :param list_its: str, which detail of an_obj to list.\
            list_its="contents" lists an Iterable's elements.\
            list_its="outputs" gets the results of calling an_obj().\
            list_its="properties" names the attributes of an_obj.\
            list_its=None (by default) will try all 3 in that order.
        """
        to_check = iter(("contents", "outputs", "attributes"))
        what_elements_are = list_its
        gotten = None
        while gotten is None:
            try:  # Figure out what details of an_obj to list
                match what_elements_are:
                    case "contents" | "elements":
                        gotten = [x for x in an_obj]
                    case "outputs" | "results":
                        gotten = [x for x in an_obj()]
                    case "attributes" | "properties":
                        gotten = [x for x in dir(an_obj)]
                    case _:
                        what_elements_are = next(to_check)
            except (NameError, TypeError) as err:
                if list_its:  # Crash if we cannot get what was asked for
                    raise err
                else:  # Keep looking for useful info to return
                    what_elements_are = next(to_check)

        if not list_its:
            list_its = what_elements_are
        what_obj_is = getattr(an_obj, "__name__", type(an_obj).__name__)
        self.what_elements_are = \
            f"{what_obj_is} {list_its if list_its else what_elements_are}"

        try:
            gotten = uniqs_in(gotten)
        except TypeError:
            pass
        super().__init__(gotten)

    def __repr__(self):
        return f"{self.what_elements_are}: {stringify_list(self)}"
