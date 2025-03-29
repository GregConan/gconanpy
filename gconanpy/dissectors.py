#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-03-28
"""
# Import standard libraries
import pdb
from typing import Any, Callable, Iterable, Iterator, Mapping, Generator, TypeVar

# Import local custom libraries
try:
    from debug import Debuggable
    from metafunc import IgnoreExceptions, KeepTryingUntilNoException, nameof
    from seq import are_all_equal, chain, stringify_list, uniqs_in
except ModuleNotFoundError:
    from gconanpy.debug import Debuggable
    from gconanpy.metafunc import IgnoreExceptions, KeepTryingUntilNoException, nameof
    from gconanpy.seq import are_all_equal, chain, stringify_list, uniqs_in


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


def has_method(an_obj, method_name: str) -> bool:
    return callable(getattr(an_obj, method_name, None))


class IteratorFactory:
    _T = TypeVar("_T")
    IGNORABLES = (AttributeError, IndexError, KeyError, TypeError, ValueError)

    @classmethod
    def first_element_of(cls, an_obj: Iterable[_T] | _T) -> _T:
        return next(cls.iterate(an_obj))

    @classmethod
    def iterate(cls, an_obj: Iterable[_T] | _T) -> Iterator[_T]:
        with KeepTryingUntilNoException(*cls.IGNORABLES) as next_try:
            with next_try():
                iterator = iter(an_obj.values())
            with next_try():
                iterator = iter(an_obj)
            with next_try():
                iterator = iter([an_obj])
        return iterator


class Peeler(IteratorFactory):

    @classmethod
    def can_peel(cls, an_obj: Any) -> bool:
        try:
            return len(an_obj) == 1 and not has_method(an_obj, "strip")
        except cls.IGNORABLES:
            return False

    @classmethod
    def peel(self, to_peel: Iterable) -> Iterable:
        while self.can_peel(to_peel):
            to_peel = self.first_element_of(to_peel)
        return to_peel


class RollingPin(Peeler, Debuggable):
    _T = TypeVar("_T")

    def __init__(self, max_rolls: int = 1000, debugging: bool = False):
        self.debugging: bool = debugging
        self.max_rolls: int = max_rolls
        self.num_rolls: int = 0

    def can_flatten(self, an_obj: Any) -> bool:
        return an_obj and self.num_rolls < self.max_rolls \
            and isinstance(an_obj, Iterable) \
            and not has_method(an_obj, "strip") \
            and not callable(an_obj) \
            and not isinstance(an_obj, Generator)

    def can_flatten_all(self, an_obj: Iterable) -> bool:
        try:
            return all(self.can_flatten(part) for part in an_obj)
        except self.IGNORABLES:
            return False

    def chain(self, iterables: Iterable[Iterable[_T]]) -> Iterable[_T]:
        return self.peel([x for x in chain(iterables)]) \
            if self.can_flatten_all(iterables) else iterables

    def flatten(self, an_obj: Any) -> list:
        flattened = [an_obj]
        parts = list()
        if self.can_flatten(an_obj):
            an_obj = self.peel(an_obj)
            with IgnoreExceptions(*self.IGNORABLES):
                parts += self.flatten(an_obj.__dict__)
            if self.can_flatten(an_obj):
                for part in an_obj:
                    self.num_rolls += 1
                    with IgnoreExceptions(*self.IGNORABLES):
                        parts.append(self.flatten(part))
            with IgnoreExceptions(*self.IGNORABLES):
                parts += self.flatten_values_in(an_obj)
            if any(parts):
                flattened = self.chain(parts)
        return self.peel(flattened)

    def flatten_values_in(self, an_obj: Any) -> list:
        an_obj = self.peel(an_obj)
        flattened = list()
        for value in an_obj.values():
            try:
                while self.can_flatten(value):
                    value = self.flatten(value)
                    self.num_rolls += 1
                flattened.append(value)
            except self.IGNORABLES as err:
                pdb.set_trace()
                print()
        self.num_rolls += 1
        return self.chain(flattened)


class Corer(RollingPin):

    def core(self, to_core: Iterable) -> Any:
        """ Extract the biggest (longest) datum from a nested data structure.

        :param to_core: Iterable, especially a nested container data structure
        :return: Any, the longest datum buried in to_core's nested layers
        """
        try:
            parts = self.flatten(to_core)
            if len(parts) > 1:
                sizes = list()
                for part in parts:
                    try:
                        part_size = len(part)
                    except self.IGNORABLES:
                        part_size = 1
                    sizes.append(part_size)
                biggest = parts[sizes.index(max(sizes))]
            else:
                biggest = parts[0]
            return biggest
        except self.IGNORABLES as err:
            self.debug_or_raise(err, locals())


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
        self.what_elements_are = f"{nameof(an_obj)} {list_its if list_its else what_elements_are}"

        try:
            gotten = uniqs_in(gotten)
        except TypeError:
            pass
        super().__init__(gotten)

    def __repr__(self):
        return f"{self.what_elements_are}: {stringify_list(self)}"
