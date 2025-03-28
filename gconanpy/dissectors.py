#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-03-26
"""
# Import standard libraries
import pdb
from typing import Any, Callable, Iterable, Mapping, Generator

# Import local custom libraries
try:
    from seq import are_all_equal, chain, nameof, stringify_list, uniqs_in
    from skippers import KeepTryingUntilNoException
except ModuleNotFoundError:
    from gconanpy.seq import (are_all_equal, chain, nameof,
                              stringify_list, uniqs_in)
    from gconanpy.skippers import KeepTryingUntilNoException


class DifferenceBetween:
    difference: str | None
    diffs: list[str | None]

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

        self.is_different = not are_all_equal(self.comparables)
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

            try:  # Mapping.keys, Mapping.get ?
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
                                 ) or are_all_equal(comparables) else on

        return difference, comparables

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


class Peeler:
    def __init__(self, max_peels: int = 1000):
        self.max_peels = max_peels
        self.peeled = list()

    def can_peel(self, an_obj: Any):
        return not isinstance(an_obj, str) and \
            not isinstance(an_obj, Callable) and \
            not isinstance(an_obj, Generator) and \
            an_obj not in self.peeled and an_obj and \
            not (hasattr(an_obj, "__dict__") and
                 an_obj.__dict__ in self.peeled)

    def are_peelable(self, an_obj: Iterable) -> bool:
        return isinstance(an_obj, Iterable) and self.can_peel(an_obj)

    def core(self, to_peel: Iterable) -> Any:
        """ Extract the biggest (longest) datum from a nested data structure.

        :param to_peel: Iterable, especially a nested container data structure
        :return: Any, the longest datum buried in to-peel's nested layers
        """
        fruits = self.peel(to_peel)
        if len(fruits) > 1:
            sizes = [len(f) for f in fruits]
            biggest = fruits[sizes.index(max(sizes))]
        else:
            biggest = fruits[0]
        return biggest

    def peel(self, to_peel: Any) -> list:
        fruits = [to_peel]
        fruit_lists = list()
        if to_peel not in self.peeled and len(self.peeled) < self.max_peels:
            self.peeled.append(to_peel)
            with KeepTryingUntilNoException() as next_try:
                with next_try():
                    if not to_peel.strip():
                        fruits = list()
                with next_try():
                    fruit_lists = self.peel_values_in(to_peel.__dict__)
                with next_try():
                    if self.are_peelable(to_peel):
                        fruit_lists = [self.peel(v) for v in to_peel
                                       if v not in self.peeled]
            try:
                fruit_lists += self.peel_values_in(to_peel)
            except (AttributeError, ValueError, TypeError):
                pass
            if fruit_lists and any(fruit_lists):
                fruits = chain(fruit_lists)
            try:
                while len(fruits) == 1:
                    fruits = fruits[0]
            except (AttributeError, ValueError, TypeError):
                pass
            if any([isinstance(x, list) for x in fruits]):
                pdb.set_trace()
        return fruits

    @staticmethod
    def peel_dict(a_dict: Mapping) -> Mapping:
        while len(a_dict.keys()) < 2:
            _, a_dict = a_dict.popitem()
        return a_dict

    def peel_values_in(self, to_peel: Any) -> list:
        self.peeled.append(to_peel)
        return chain(*[[self.peel(part) for part in value if part not in
                       self.peeled and part != to_peel and part != value]
                       for value in to_peel.values()
                       if self.are_peelable(value) and value != to_peel])


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
        self.what_elements_are = \
            f"{nameof(an_obj)} {list_its if list_its else what_elements_are}"

        try:
            gotten = uniqs_in(gotten)
        except TypeError:
            pass
        super().__init__(gotten)

    def __repr__(self):
        return f"{self.what_elements_are}: {stringify_list(self)}"
