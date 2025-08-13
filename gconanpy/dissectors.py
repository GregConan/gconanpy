#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-08-11
"""
# Import standard libraries
from collections.abc import Callable, Hashable, Iterable
from operator import getitem
from typing import Any, TypeVar

# Import local custom libraries
try:
    from debug import Debuggable
    from iters import are_all_equal, MapSubset, SimpleShredder
    from iters.seq import uniqs_in
    from meta import (Comparer, has_method,
                      IgnoreExceptions, IteratorFactory, name_of)
    from meta.typeshed import DATA_ERRORS
    from trivial import always_true, get_key_set
    from wrappers import Sets, stringify_iter
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.debug import Debuggable
    from gconanpy.iters import are_all_equal, MapSubset, SimpleShredder
    from gconanpy.iters.seq import uniqs_in
    from gconanpy.meta import (Comparer, has_method,
                               IgnoreExceptions, IteratorFactory, name_of)
    from gconanpy.meta.typeshed import DATA_ERRORS
    from gconanpy.trivial import always_true, get_key_set
    from gconanpy.wrappers import Sets, stringify_iter


class DifferenceBetween:
    # Class type variables for type hints
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
            i = 1  # TODO try to make a do-while context manager "with-hack"?
            arg_name = f"{arg_type}{i}"
            while arg_name in self.names:
                i += 1
                arg_name = f"{arg_type}{i}"
            self.names.append(arg_name)

        # If objects differ, then discover how; else there's no need
        self.is_different = not are_all_equal(self.comparables)
        self.diffs = self.find() if self.is_different else list()

    def __repr__(self) -> str:
        """
        :return: str, human-readable summary of how self.comparables differ.
        """
        if not self.is_different:
            result = " == ".join(self.names)
        else:
            kwargs_stringify: dict[str, Any] = dict(
                quote=None, prefix=None, suffix=None)
            names = stringify_iter(self.names, **kwargs_stringify)
            if self.difference:
                diffs_list = [
                    f"{self.difference} of {self.names[i]} == {self.diffs[i]}"
                    for i in range(len(self.diffs))]
                diffs_str = stringify_iter(diffs_list, **kwargs_stringify
                                           ).capitalize()
                result = f"{self.difference.capitalize()} differs between " \
                    f"{names}:\n{diffs_str}"
            else:
                result = f"A difference between {names} exists, but it " \
                    "could not be identified."
        return result

    def compare_all_in(self, by: str, get_subcomparator: GetSubcomparator,
                       comparisons: Iterable[PartName]) -> list:
        """ _summary_ 

        :param by: str, name of the possible difference to find
        :param get_subcomparator: GetSubcomparator, _description_
        :param comparisons: Iterable[PartName], _description_
        :return: list, _description_
        """
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
        """ _summary_ 

        :param end_ix: int, _description_
        :return: list, _description_
        """
        return self.compare_all_in("element", getitem,
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
        return list(Sets(keys).differentiate()) if self.difference else \
            self.compare_all_in(by, get_subcomparator, next(iter(keys)))

    def find(self) -> list:
        """ Find the difference(s) between the objects in self.comparables.
            Returns the first difference found, not an exhaustive list.

        :return: list, the values that differ between the objects; \
                 empty if no difference is found.
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
                    return list(Sets(keys).differentiate())
                else:
                    values = self.compare_all_in("value", getitem, keys)
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


class Peeler(IteratorFactory):
    _P = TypeVar("_P")  # Item(s) to extract from a "peeled" container.

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
        if self._will_now_traverse(an_obj) and len(self.traversed
                                                   ) < self.max_shreds:

            # If it has a __dict__, then shred that
            with IgnoreExceptions(*self.SHRED_ERRORS):
                self._shred_iterable(an_obj.__dict__)

            # Shred or save each of an_obj's...
            try:  # ...values if it's a Mapping
                for k, v in an_obj.items():  # type: ignore
                    if has_method(v, "items") or self.filter(k, v):
                        self.shred(v)
            except self.SHRED_ERRORS:

                # ...elements if it's not a Mapping
                for element in an_obj:
                    self.shred(element)


class Corer(Shredder, Comparer):
    _T = TypeVar("_T")  # .core(...) method return type

    def _choose(self, parts: set[_T], default: _T | None = None,
                compare_their: Comparer.ToNumber = len,
                make_comparable: Comparer.ToComparable = str) -> _T | None:
        """ Extract the largest element of a set.

        :param parts: set to return the largest element of
        :param default: Any, item to return if nothing is found in `to_core`.
        :param compare_their: Callable[[Any], SupportsFloat], comparison \
            function that converts an item into a numerical value that can \
            be compared to find (and return) the largest; defaults to `len`
        :param make_comparable: Callable[[Any], Any], secondary comparison \
            function that converts an item into an input acceptable by \
            `compare_their` to convert to a numerical value representing \
            item size to return the largest item; defaults to `str` function
        :return: Any, the longest datum buried in to_core's nested layers
        """
        try:
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

    def core(self, to_core: Iterable, default: _T | None = None,
             reset_first: bool = True,
             compare_their: Comparer.ToNumber = len,
             make_comparable: Comparer.ToComparable = str
             ) -> _T | None:
        """ Extract the largest datum from a nested data structure.

        :param to_core: Iterable, especially a nested container data structure
        :param default: Any, item to return if nothing is found in `to_core`.
        :param reset_first: bool, True to make this Corer forget what it \
            previously traversed and start this traversal fresh; else False \
            to skip anything it previously traversed; defaults to True.
        :param compare_their: Callable[[Any], SupportsFloat], comparison \
            function that converts an item into a numerical value that can \
            be compared to find (and return) the largest; defaults to `len`
        :param make_comparable: Callable[[Any], Any], secondary comparison \
            function that converts an item into an input acceptable by \
            `compare_their` to convert to a numerical value representing \
            item size to return the largest item; defaults to `str` function
        :return: Any, the longest datum buried in to_core's nested layers
        """
        if reset_first:
            self.reset()
        return self._choose(self.shred(to_core), default, compare_their,
                            make_comparable)

    def safe_core(self, to_core: Iterable, as_type: type[_T], default:
                  _T | None = None, reset_first: bool = True,
                  compare_their: Comparer.ToNumber = len,
                  make_comparable: Comparer.ToComparable = str) -> _T:
        """ Extract the largest datum of a specific type from a \
            nested data structure.

        :param to_core: Iterable, especially a nested container data structure
        :param as_type: type of object to extract from `to_core` and return
        :param default: Any, item to return if nothing is found in `to_core`.
        :param reset_first: bool, True to make this Corer forget what it \
            previously traversed and start this traversal fresh; else False \
            to skip anything it previously traversed; defaults to True.
        :param compare_their: Callable[[Any], SupportsFloat], comparison \
            function that converts an item into a numerical value that can \
            be compared to find (and return) the largest; defaults to `len`
        :param make_comparable: Callable[[Any], Any], secondary comparison \
            function that converts an item into an input acceptable by \
            `compare_their` to convert to a numerical value representing \
            item size to return the largest item; defaults to `str` function
        :return: Any, the longest datum buried in to_core's nested layers
        """
        if reset_first:
            self.reset()
        parts = {p for p in self.shred(to_core) if isinstance(p, as_type)}
        cored = self._choose(parts, default, compare_their, make_comparable)
        if cored is None:
            raise ValueError(f"Failed to core {name_of(to_core)}")
        return cored


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
        return f"{self.what_elements_are}: {stringify_iter(self)}"
