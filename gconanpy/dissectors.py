#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-04-08
"""
# Import standard libraries
import pdb
from typing import (Any, Callable, Hashable, Iterable, Iterator,
                    SupportsFloat, TypeVar)

# Import local custom libraries
try:
    from debug import Debuggable
    from metafunc import has_method, IgnoreExceptions, \
        KeepTryingUntilNoException, nameof, Trivial
    from seq import (are_all_equal, differentiate_sets,
                     get_key_set, stringify_list, uniqs_in)
    from typevars import CanIgnoreCertainErrors, DifferTypes as Typ
except ModuleNotFoundError:
    from gconanpy.debug import Debuggable
    from gconanpy.metafunc import has_method, IgnoreExceptions, \
        KeepTryingUntilNoException, nameof, Trivial
    from gconanpy.seq import (are_all_equal, differentiate_sets,
                              get_key_set, stringify_list, uniqs_in)
    from gconanpy.typevars import CanIgnoreCertainErrors, DifferTypes as Typ


class DifferenceBetween:
    comparables: list[Typ.ToCompare]
    difference: str | None
    diffs: list[str | None]
    names: list[str]

    def __init__(self, *args: Typ.ToCompare, **kwargs: Typ.ToCompare):
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
            arg_type = nameof(arg)
            arg_name = arg_type
            i = 1
            while arg_name in self.names:
                i += 1
                arg_name = f"{arg_type}{i}"
            self.names.append(arg_name)

        self.is_different = not are_all_equal(self.comparables)
        self.diffs = self.find_difference() if self.is_different else None

    def compare_all_in(self, on: str, get_subcomparator: Typ.GetSubcomparator,
                       comparisons: Iterable[Typ.PartName]) -> list[Typ.Diff]:
        diffs = list()
        get_comparison = iter(comparisons)
        next_name = next(get_comparison, None)
        while next_name is not None and not self.difference:
            diffs = self.compare_by(f"{on} {next_name}", lambda y:
                                    get_subcomparator(y, next_name))
            next_name = next(get_comparison, None)
        return diffs

    def compare_by(self, on: str, get_comparator: Typ.GetComparator
                   ) -> list[Typ.Diff]:
        """ _summary_

        :param on: str, name of the possible difference to find
        :param get_comparator: Callable[[Any], Any], \
            1-arg-to-1-arg function that extracts things to compare
        :return: list, _description_
        """
        comparables = [get_comparator(c) for c in self.comparables]
        if not are_all_equal(comparables):
            self.difference = on
        return comparables

    def compare_elements_0_to(self, end_ix: int) -> list[Typ.Diff]:
        return self.compare_all_in("element", Trivial.get_item_of,
                                   [x for x in range(end_ix)])

    def compare_sets(self, on: str, get_comparisons: Typ.GetPartNames,
                     get_subcomparator: Typ.GetSubcomparator
                     ) -> list[Typ.Diff]:
        """ _summary_ 

        :param on: str, name of the possible difference to find
        :param get_comparisons: Callable[[Any], Iterable[Any]], _description_
        :param get_subcomparator: Callable[[Any, Any], Any], _description_
        :return: list[Diff], _description_
        """
        keys = self.compare_by(on, get_comparisons)
        return differentiate_sets(keys) if self.difference else \
            self.compare_all_in(on, get_subcomparator, keys)

    def find_difference(self) -> list[Typ.Diff] | None:
        """ Find the difference(s) between the objects in self.comparables.
        Returns the first difference found, not an exhaustive list.

        :return: list | None, the values that differ between the objects, or
                 None if no difference is found.
        """
        types = self.compare_by("type", type)
        if self.difference:
            return types

        with IgnoreExceptions(TypeError):
            lens = self.compare_by("length", len)
            if self.difference:
                return lens

            with IgnoreExceptions(AttributeError, TypeError):
                keys = self.compare_by("key", get_key_set)
                if self.difference:
                    diff_keys = differentiate_sets(keys)
                    return diff_keys
                else:
                    values = self.compare_all_in(
                        "value", Trivial.get_item_of, keys)
                    if self.difference:
                        return values

            with IgnoreExceptions(KeyError):
                ix_diffs = self.compare_elements_0_to(set(lens).pop())
                if self.difference:
                    return ix_diffs

        diff_attrs = self.compare_sets("unique attribute(s)", dir, getattr)
        if self.difference:
            return diff_attrs

    def __repr__(self) -> str:
        """
        :return: str, human-readable summary of how self.comparables differ.
        """
        if not self.is_different:
            result = " == ".join(self.names)
        else:
            names = stringify_list(self.names, enclose_in=None)
            if self.difference:
                differences = stringify_list([
                    f"{self.difference} of {self.names[i]} == {self.diffs[i]}"
                    for i in range(len(self.diffs))], quote=None, enclose_in=None)
                result = f"{self.difference} differs between {names}:" \
                    f"\n{differences}."
            else:
                result = f"A difference between {names} exists, but it " \
                    "could not be identified."
        return result


class IteratorFactory(CanIgnoreCertainErrors):
    _T = TypeVar("_T")

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
            is_peelable = len(an_obj) == 1 and not has_method(an_obj, "strip")
        except cls.IGNORABLES:
            is_peelable = False
        return is_peelable

    @classmethod
    def peel(self, to_peel: Iterable) -> Iterable:
        while self.can_peel(to_peel):
            to_peel = self.first_element_of(to_peel)
        return to_peel


class SimpleShredder:
    SHRED_ERRORS = (AttributeError, TypeError)

    def __init__(self) -> None:
        self.reset()

    def _collect(self, an_obj: Any) -> None:
        try:  # If it's a string, then it's not shreddable, so save it
            self.parts.add(an_obj.strip())
        except self.SHRED_ERRORS:

            try:  # If it's a non-str Iterable, then shred it
                iter(an_obj)
                self._shred_iterable(an_obj)

            # Hashable but not Iterable means not shreddable, so save it
            except TypeError:
                self.parts.add(an_obj)

    def _shred_iterable(self, an_obj: Iterable) -> None:
        # If we already shredded it, then don't shred it again
        objID = id(an_obj)
        if objID not in self.shredded:
            self.shredded.add(objID)

            try:  # If it has a __dict__, then shred that
                self._shred_iterable(an_obj.__dict__)
            except self.SHRED_ERRORS:
                pass

            # Shred or save each of an_obj's...
            try:  # ...values if it's a Mapping
                for v in an_obj.values():
                    self._collect(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not
                for element in an_obj:
                    self._collect(element)

    def reset(self):
        self.parts: set = set()
        self.shredded: set[int] = set()

    def shred(self, an_obj: Any) -> set:
        self._collect(an_obj)
        return self.parts


class Shredder(SimpleShredder, Debuggable):
    _T = TypeVar("_T")

    def __init__(self, max_shreds: int = 500, debugging: bool = False,
                 exclude: Iterable[Hashable] = set()):
        self.debugging = debugging
        self.exclude_keys = set(exclude)
        self.max_shreds = max_shreds
        self.reset()

    def _shred_iterable(self, an_obj: Iterable) -> None:
        # If we already shredded it, then don't shred it again
        objID = id(an_obj)
        if objID not in self.shredded and len(self.shredded
                                              ) < self.max_shreds:
            self.shredded.add(objID)

            # If it has a __dict__, then shred that
            with IgnoreExceptions(*self.SHRED_ERRORS):
                self._shred_iterable(an_obj.__dict__)

            try:  # If it's a Mapping, then shred or save each of its values
                for k, v in an_obj.items():
                    if k not in self.exclude_keys:
                        self._collect(v)
            except self.SHRED_ERRORS:

                # If it's not a Mapping, then shred or save each element
                for element in an_obj:
                    self._collect(element)

    def shred(self, an_obj: Any, remember: bool = False) -> set:
        try:
            if not remember:
                self.reset()
            to_return = super(Shredder, self).shred(an_obj)
            if not remember:
                self.reset()
            return to_return
        except RecursionError as err:
            self.debug_or_raise(err, locals())


class Corer(Shredder, CanIgnoreCertainErrors):
    Comparer = Callable[[Any], SupportsFloat]

    def core(self, to_core: Iterable, default: Any = None,
             compare_their: Comparer = len,
             make_comparable: Callable = str) -> Any:
        """ Extract the biggest (longest) datum from a nested data structure.

        :param to_core: Iterable, especially a nested container data structure
        :return: Any, the longest datum buried in to_core's nested layers
        """
        try:
            parts = self.shred(to_core)
            match len(parts):
                case 0:
                    biggest = default
                case 1:
                    biggest = parts.pop()
                case _:

                    # TODO Extract the block below into standalone comparison function?
                    biggest = "0"
                    max_size = compare_their(biggest)
                    for part in parts:
                        try:
                            part_size = compare_their(part)
                        except self.IGNORABLES:
                            try:
                                part_size = compare_their(
                                    make_comparable(part))
                            except self.IGNORABLES:
                                part_size = 1.0
                        if part_size >= max_size:
                            biggest = part
                            max_size = part_size

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
