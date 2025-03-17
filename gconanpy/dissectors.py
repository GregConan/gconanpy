#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap abstract data structures.
Extremely useful and convenient for debugging, but not necessary otherwise.
Overlaps significantly with:
    audit-ABCC/src/utilities.py, \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-03-16
"""
# Import standard libraries
from abc import ABC
import itertools
import pdb
from typing import (Any, Callable, Hashable, Iterable,
                    Mapping, Sequence, TypeVar)

# Import local custom libraries
try:
    from seq import noop, stringify_list, uniqs_in
except ModuleNotFoundError:
    from gconanpy.seq import noop, stringify_list, uniqs_in


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

    @classmethod
    def peel2(cls, to_peel: Any) -> list:
        fruits = [to_peel]
        fruit_lists = None
        if to_peel is not None:
            try:
                if not str.strip(to_peel):
                    fruits = list()
            except TypeError:
                try:
                    fruit_lists = [cls.peel2(to_peel[k])
                                   for k in to_peel.keys()]
                except (AttributeError, TypeError):
                    try:
                        # if isinstance(to_peel, bs4.PageElement):
                        if len(to_peel.contents):
                            fruit_lists = [cls.peel2(c) for c
                                           in to_peel.contents]
                    except AttributeError:
                        try:
                            fruit_lists = [cls.peel2(el) for el in to_peel]
                        except TypeError:
                            pass
        if fruit_lists is not None:
            fruits = list(itertools.chain(*fruit_lists))
        return fruits

    @staticmethod
    def peel_dict(a_dict: Mapping) -> Mapping:
        while len(a_dict.keys()) < 2:
            _, a_dict = a_dict.popitem()
        return a_dict


class Whittler(ABC):
    """ Iteratively "whittle down" a string(/etc) and stop as soon as
    (a) it meets a certain condition, and/or
    (b) you found what you were looking for inside it. """
    _T = TypeVar("T")
    _S = TypeVar("S")
    _X = TypeVar("X")

    def is_none(x: Any): return x is None  # Mostly to use as default argument

    @staticmethod
    def whittle(to_modify: _T, iter_over: Sequence[_S],
                modify: Callable[[_T, _S, tuple[_X, ...]], _T],
                is_not_ready: Callable[[_T], bool] = is_none,
                modify_args: Iterable[_X] = list(), start_at: int = 0,
                end_at: int | None = None, step: int = 1,
                is_viable: Callable[[_T], bool] = len) -> _T:
        """ While to_modify is_not_ready, modify it by iterating iter_over.

        :param to_modify: _T, _description_
        :param iter_over: Sequence[_S] to iterate over
        :param modify: Callable[[_T, _S, tuple[_X, ...]], _T], _description_
        :param is_not_ready: Callable[[_T], bool], sufficient condition; \
            returns False if to_modify is ready to return and True if it \
            needs further modification; defaults to "to_modify is None"
        :param modify_args: Iterable[_X], additional positional arguments to call \
            modify(to_modify) with on every iteration
        :param start_at: int, iter_over index to begin at; defaults to 0
        :param end_at: int, iter_over index to stop at; defaults to len(iter_over)
        :param step: int, increment to iterate iter_over by; defaults to 1
        :param is_viable: Callable[[_T], bool], necessary condition; \
            returns True if to_modify is a valid/acceptable/sensical value \
            to return or True otherwise; defaults to len(to_modify) > 0
        :param modify_kwargs: Mapping[str, Any], keyword arguments to pass
            into the to_
        :return: _T, _description_
        """
        # if is_not_ready(to_modify):
        ix = start_at
        end = len(iter_over) if end_at is None else end_at

        not_yet_at, step = (int.__lt__, abs(step)) if \
            ix <= end else (int.__ge__, -abs(step))

        while is_not_ready(to_modify) and not_yet_at(ix, end):
            modified = modify(to_modify, iter_over[ix], *modify_args)
            if is_viable(modified):
                to_modify = modified
            ix += 1

        return to_modify

    @classmethod
    def pop(cls, parts: Iterable[str],
            is_not_ready: Callable[[str], bool] = is_none,
            min_len: int = 1, get_target: Callable[[str], _T | None] = noop,
            pop_ix: int = -1, join_on: str = " ") -> tuple[str, _T | None]:
        """
        _summary_
        :param parts: Iterable[str], _description_
        :param is_not_ready: Callable[[str], bool], function that returns False \
            if join_on.join(parts) is ready to return and True if it still \
            needs to be modified further; defaults to Whittler.is_none
        :param pop_ix: int,_description_, defaults to -1
        :param join_on: str,_description_, defaults to " "
        :return: _type_, _description_
        """
        gotten = get_target(parts[-1])
        rejoined = join_on.join(parts)
        while is_not_ready(rejoined) and len(parts) > min_len \
                and cls.is_none(gotten):
            parts.pop(pop_ix)
            gotten = get_target(parts[-1])
            rejoined = join_on.join(parts)
        return rejoined, gotten


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
