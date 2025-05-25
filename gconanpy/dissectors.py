#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-05-17
"""
# Import standard libraries
from collections.abc import Callable, Hashable, Iterable, Iterator
import pdb
from typing import Any, SupportsFloat, TypeVar

# Import local custom libraries
try:
    from debug import Debuggable
    from maptools import MapSubset, Traversible
    from metafunc import are_all_equal, DATA_ERRORS, has_method, \
        IgnoreExceptions, KeepTryingUntilNoErrors, method, name_of
    from seq import differentiate_sets, get_key_set, uniqs_in
    from ToString import stringify
    from trivial import always_true, get_item_of
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.debug import Debuggable
    from gconanpy.maptools import MapSubset, Traversible
    from gconanpy.metafunc import are_all_equal, DATA_ERRORS, has_method, \
        IgnoreExceptions, KeepTryingUntilNoErrors, method, name_of
    from gconanpy.seq import differentiate_sets, get_key_set, uniqs_in
    from gconanpy.ToString import stringify
    from gconanpy.trivial import always_true, get_item_of


class DifferenceBetween:
    # Class type variables
    Diff = TypeVar("Diff")
    ToCompare = TypeVar("ToCompare")
    PartName = TypeVar("PartName", bound=Hashable)
    GetComparator = Callable[[ToCompare], Diff]
    GetPartNames = Callable[[ToCompare], Iterable[PartName]]
    GetSubcomparator = Callable[[ToCompare, PartName], Diff]

    # Instance variables
    comparables: list  # The objects to compare/contrast
    difference: str | None  # Name classifying the difference
    diffs: list[str | None]  # The differing values themselves
    names: list[str]  # The names of the objects to compare/contrast

    def __init__(self, *args: ToCompare, **kwargs: ToCompare):
        """ Identify difference(s) between any Python objects/values.

        :param args: Iterable[Any] of objects to compare.
        :param kwargs: Mapping[str, Any] of names to objects to compare.
        """
        self.difference = None

        # List the objects to compare, and their names, for comparison methods
        self.comparables = list()
        self.names = list()
        for name, to_compare in kwargs.items():
            self.names.append(name)
            self.comparables.append(to_compare)
        for arg in args:
            self.comparables.append(arg)

            # By default, name unnamed objects their type and insertion order
            arg_type = name_of(arg)
            arg_name = arg_type
            i = 1
            while arg_name in self.names:
                i += 1
                arg_name = f"{arg_type}{i}"
            self.names.append(arg_name)

        # If objects differ, then discover how; else there's no need
        self.is_different = not are_all_equal(self.comparables)
        self.diffs = self.find()

    def compare_all_in(self, by: str, get_subcomparator: GetSubcomparator,
                       comparisons: Iterable[PartName]) -> list:
        diffs = list()
        get_comparison = iter(comparisons)
        next_name = next(get_comparison, None)
        while not self.difference and next_name is not None:
            diffs = self.compare_by(f"{by} {next_name}", lambda y:
                                    get_subcomparator(y, next_name))
            next_name = next(get_comparison, None)
        return diffs

    def compare_by(self, by: str, get_comparator: GetComparator
                   ) -> list:
        """ _summary_

        :param by: str, name of the possible difference to find
        :param get_comparator: Callable[[Any], Any], \
            1-arg-to-1-arg function that extracts things to compare
        :return: list, _description_
        """
        comparables = [get_comparator(c) for c in self.comparables]
        if not are_all_equal(comparables):
            self.difference = by
        return comparables

    def compare_elements_0_to(self, end_ix: int) -> list:
        return self.compare_all_in("element", get_item_of,
                                   [x for x in range(end_ix)])

    def compare_sets(self, by: str, get_comparisons: GetPartNames,
                     get_subcomparator: GetSubcomparator
                     ) -> list:
        """ _summary_ 

        :param by: str, name of the possible difference to find
        :param get_comparisons: Callable[[Any], Iterable[Any]], _description_
        :param get_subcomparator: Callable[[Any, Any], Any], _description_
        :return: list, _description_
        """
        keys = self.compare_by(by, get_comparisons)
        return differentiate_sets(keys) if self.difference else \
            self.compare_all_in(by, get_subcomparator, next(iter(keys)))

    def find(self) -> list:
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
                        "value", get_item_of, keys)
                    if self.difference:
                        return values

            with IgnoreExceptions(KeyError):
                ix_diffs = self.compare_elements_0_to(set(lens).pop())
                if self.difference:
                    return ix_diffs

        diff_attrs = self.compare_sets("unique attribute(s)", dir, getattr)
        if self.difference:
            return diff_attrs
        else:
            return list()

    def __repr__(self) -> str:
        """
        :return: str, human-readable summary of how self.comparables differ.
        """
        if not self.is_different:
            result = " == ".join(self.names)
        else:
            names = stringify(self.names)
            if self.difference:
                differences = stringify([
                    f"{self.difference} of {self.names[i]} == {self.diffs[i]}"
                    for i in range(len(self.diffs))], quote=None)
                result = f"{self.difference} differs between {names}:" \
                    f"\n{differences}."
            else:
                result = f"A difference between {names} exists, but it " \
                    "could not be identified."
        return result


class IteratorFactory:
    _T = TypeVar("_T")

    @classmethod
    def first_element_of(cls, an_obj: Iterable[_T] | _T) -> _T:
        return next(cls.iterate(an_obj))

    @classmethod
    def iterate(cls, an_obj: Iterable[_T] | _T) -> Iterator[_T]:
        with KeepTryingUntilNoErrors(*DATA_ERRORS) as next_try:
            with next_try():
                iterator = iter(an_obj.values())  # type: ignore
            with next_try():
                iterator = iter(an_obj)  # type: ignore
            with next_try():
                iterator = iter([an_obj])
        return iterator  # type: ignore


class Peeler(IteratorFactory):
    _P = TypeVar("_P")

    @classmethod
    def can_peel(cls, an_obj: Any) -> bool:
        """ 
        :param an_obj: Any,
        :return: bool, True if an_obj is a container of 1 element; else False
        """
        try:
            is_peelable = len(an_obj) == 1 and not has_method(an_obj, "strip")
        except DATA_ERRORS:
            is_peelable = False
        return is_peelable

    def peel(self, to_peel: Iterable[_P]) -> Iterable[_P] | _P:
        """ Extract data from redundant nested container data structures.

        :param to_peel: Iterable, especially a nested container data structure
        :return: Iterable formerly contained in too many layers of nested \
            Iterables; this will be an Iterable unless to_peel contains only \
            one item, in which case the function will return that item
        """
        while self.can_peel(to_peel):
            to_peel = self.first_element_of(to_peel)
        return to_peel


class SimpleShredder(Traversible):
    SHRED_ERRORS = (AttributeError, TypeError)

    def __init__(self) -> None:
        self.reset()

    def _collect(self, an_obj: Any) -> None:
        """ Recursively collect/save the attributes, items, and/or elements \
            of an_obj regardless of how deeply they are nested.

        :param an_obj: Any, object to get the parts of
        """
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
        """ Save every item in an Iterable regardless of how deeply nested, \
            unless that item is "shreddable" (a non-string data container).

        :param an_obj: Iterable to save the "shreddable" elements of.
        """
        # If we already shredded it, then don't shred it again
        if self._will_traverse(an_obj):

            try:  # If it has a __dict__, then shred that
                self._shred_iterable(an_obj.__dict__)
            except self.SHRED_ERRORS:
                pass

            # Shred or save each of an_obj's...
            try:  # ...values if it's a Mapping
                for v in an_obj.values():  # type: ignore
                    self._collect(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not a Mapping
                for element in an_obj:
                    self._collect(element)

    def reset(self):
        super(SimpleShredder, self).__init__()
        self.parts: set = set()
        # self.shredded: set[int] = set()

    def shred(self, an_obj: Any) -> set:
        """ Recursively collect/save the attributes, items, and/or elements \
            of an_obj regardless of how deeply they are nested. Return only \
            the Hashable data in an_obj, not the Containers they're in.

        :param an_obj: Any, object to return the parts of.
        :return: set of the particular Hashable non-Container data in an_obj
        """
        self._collect(an_obj)
        return self.parts


class Shredder(SimpleShredder, Debuggable):
    _T = TypeVar("_T")

    def __init__(self, max_shreds: int = 500, debugging: bool = False,
                 map_filter: MapSubset.Filter = always_true) -> None:
        """ 
        :param max_shreds: int, the maximum number of times to "shred" a \
            data container to collect the data inside; defaults to 500
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        :param map_filter: Callable[[str, Any], bool], MapSubset.Filter \
            function to exclude certain keys and/or values from the returned \
            result; by default, no keys/values will be excluded.
        """
        self.debugging = debugging
        self.filter = map_filter
        self.max_shreds = max_shreds
        self.reset()

    def _shred_iterable(self, an_obj: Iterable) -> None:
        """ Save every item in an Iterable regardless of how deeply nested, \
            unless that item is "shreddable" (a non-string data container) \
            or that item is excluded by the filters defined in __init__

        :param an_obj: Iterable to save the "shreddable" elements of.
        """
        # If we already shredded it, then don't shred it again
        if self._will_traverse(an_obj) and len(self.traversed
                                               ) < self.max_shreds:

            # If it has a __dict__, then shred that
            with IgnoreExceptions(*self.SHRED_ERRORS):
                self._shred_iterable(an_obj.__dict__)

            # Shred or save each of an_obj's...
            try:  # ...values if it's a Mapping
                for k, v in an_obj.items():  # type: ignore
                    if has_method(v, "items") or self.filter(k, v):
                        self._collect(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not a Mapping
                for element in an_obj:
                    self._collect(element)

    def shred(self, an_obj: Any, remember: bool = False) -> set:  # type: ignore
        """ Recursively collect/save the attributes, items, and/or elements \
            of an_obj regardless of how deeply they are nested. Return only \
            the Hashable data in an_obj, not the Containers they're in.

        :param an_obj: Any, object to return the parts of.
        :param remember: bool, True to keep previously collected items; else \
            False to reset the max_shreds counter and return only the items \
            found in this .shred(...) call
        :return: set of the particular Hashable non-Container data in an_obj
        """
        try:
            if not remember:
                self.reset()
            to_return = super(Shredder, self).shred(an_obj)
            if not remember:
                self.reset()
            return to_return
        except RecursionError as err:
            self.debug_or_raise(err, locals())


class Comparer:
    Comparable = TypeVar("Comparable")
    Comparee = TypeVar("Comparee")
    Comparison = Callable[[Comparable, Comparable], bool]
    ToNumber = Callable[[Comparable], SupportsFloat]
    ToComparable = Callable[[Comparee], Comparable]

    @classmethod
    def comparison(cls, smallest: bool = False, earliest: bool = False
                   ) -> Comparison:
        """ Get function that compares two `SupportsFloat` objects.

        smallest & earliest => `x.__lt__(y)` (Less Than),
        biggest & latest => `x.__ge__(y)` (Greater than or Equal to), etc.

        :param smallest: bool,_description_, defaults to False
        :param earliest: bool,_description_, defaults to False
        :return: Comparison, function that takes 2 `SupportsFloat` objects, \
            calls an inequality method of the first's on the second, and \
            returns the (boolean) result.
        """
        return method(f'__{"l" if smallest else "g"}'
                      f'{"t" if earliest else "e"}__')

    @classmethod
    def compare(cls, items: Iterable[Comparee], compare_their: ToNumber = len,
                make_comparable: ToComparable = str, default: Comparee = "0",
                smallest: bool = False, earliest: bool = False) -> Comparee:
        """ Get the biggest (or smallest) item in `items`. 

        :param items: Iterable[Any], things to compare.
        :param compare_their: Callable[[Any], SupportsFloat], comparison \
            function, defaults to `len`
        :param make_comparable: Callable[[Any], Any], comparison \
            function, defaults to `str`
        :param default: Any, starting item to compare other items against
        :return: Any, item with the largest value returned by calling \
            `compare_their(make_comparable(`item`))`.
        """
        compare = cls.comparison(smallest, earliest)
        biggest = default
        max_size = compare_their(biggest)
        for item in items:
            try:
                item_size = compare_their(item)
            except DATA_ERRORS:
                try:
                    item_size = compare_their(make_comparable(item))
                except DATA_ERRORS:
                    item_size = 1.0
            if compare(item_size, max_size):  # item_size >= max_size:
                biggest = item
                max_size = item_size
        return biggest


class Corer(Shredder, Comparer):

    def core(self, to_core: Iterable[Comparer.Comparee],
             default: Comparer.Comparee = None,
             compare_their: Comparer.ToNumber = len,
             make_comparable: Comparer.ToComparable = str
             ) -> Comparer.Comparee:
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
                    biggest = self.compare(parts, compare_their,
                                           make_comparable)
            return biggest
        except DATA_ERRORS as err:
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
                        gotten = dir(an_obj)
                    case _:
                        what_elements_are = next(to_check)
            except (NameError, TypeError) as err:
                if list_its:  # Crash if we cannot get what was asked for
                    raise err
                else:  # Keep looking for useful info to return
                    what_elements_are = next(to_check)

        if not list_its:
            list_its = what_elements_are
        self.what_elements_are = name_of(an_obj) + \
            f" {list_its if list_its else what_elements_are}"

        with IgnoreExceptions(TypeError):
            gotten = uniqs_in(gotten)
        super().__init__(gotten)

    def __repr__(self):
        return f"{self.what_elements_are}: {stringify(self)}"
