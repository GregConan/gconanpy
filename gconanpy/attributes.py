#!/usr/bin/env python3

"""
Functions/classes to access and/or modify the attributes of any object(s).
Greg Conan: gregmconan@gmail.com
Created: 2025-06-02
Updated: 2025-06-05
"""
# Import standard libraries
from collections.abc import Callable, Generator, Iterable
from typing import Any, Literal, TypeVar

# Import local custom libraries
try:
    from metafunc import combine_sets, WrapFunction
    from trivial import always_true
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.metafunc import combine_sets, WrapFunction
    from gconanpy.trivial import always_true

# Constants: TypeVars for...
T = TypeVar("T")  # ...add_to


def add_to(an_obj: T, **attributes: Any) -> T:
    """
    :param an_obj: Any, object to add attributes to
    :return: Any, `an_obj` now with `attributes` added
    """
    for attr_name, attr_value in attributes.items():
        setattr(an_obj, attr_name, attr_value)
    return an_obj


def get_all_names(*objects: Any) -> set[str]:
    """
    :param objects: Iterable of objects to return the attribute names of
    :return: set[str], the name of every attribute of everything in `objects`
    """
    attr_names = set()
    for an_obj in objects:
        attr_names.update(get_names(an_obj))
    return attr_names


def get_names(an_obj: Any) -> set[str]:
    """
    :param an_obj: Any, object to return the attribute names of
    :return: set[str], the name of every attribute of `an_obj`
    """
    names = set()

    # Name some attributes of its class/type
    names.update(dir(type(an_obj)))

    # If it's a class, name some attributes of its base class(es)
    bases = getattr(an_obj, "__bases__", None)
    if bases:
        names.update(combine_sets((set(base.__dict__) for base in bases)))

    # Name some of its own attributes
    names.update(dir(an_obj))

    # Name the rest of its own attributes
    dict_attr = getattr(an_obj, "__dict__", None)
    if dict_attr:
        names.update(dict_attr)

    # Filter out absent attribute names
    to_remove = set()
    for attr_name in names:
        try:
            getattr(an_obj, attr_name)
        except AttributeError:
            to_remove.add(attr_name)
    # TODO Fix, test & timeit (against block above)
    # obj_has = WrapFunction(hasattr, pre=[an_obj])
    # to_remove = {attr_name for attr_name in filter(obj_has, names)}

    return names - to_remove


class Filter:
    # Class variables: method input argument types
    _SELECTOR = Callable[[Any], bool]  #
    _SELECTORS = list[_SELECTOR]
    _WHICH = Literal["names", "values"]
    FilterFunction = Callable[[str, Any], bool]

    include: dict[_WHICH, bool]
    selectors: dict[_WHICH, _SELECTORS]

    def __init__(self, if_names: _SELECTORS = list(),
                 if_values: _SELECTORS = list(),
                 include_names: bool = True,
                 include_values: bool = True) -> None:
        """ _summary_ 

        :param if_names: list[Callable[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        :param if_values: list[Callable[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute or skip it
        """
        self.include = {"names": include_names, "values": include_values}
        self.selectors = {"names": if_names, "values": if_values}

    def add(self, which: _WHICH, func: Callable,
            pre: Iterable = list(), post: Iterable = list(),
            **kwargs: Any) -> None:
        self.selectors[which].append(WrapFunction(func, pre, post,
                                                  **kwargs))

    def build(self) -> FilterFunction:
        """
        :return: Callable[[str, Any], bool] that returns True if the `str` \
            argument passes all of the name filters and the `Any` \
            argument passes all of the value filters, else False
        """
        @staticmethod
        def is_filtered(name: str, value: Any) -> bool:
            return self.check("names", name) and self.check("values", value)
        return is_filtered

    def check(self, which: _WHICH, to_check: Any) -> bool:
        for passes_filter in self.selectors[which]:
            if passes_filter(to_check) is not self.include[which]:
                return False
        return True


class Of:
    """ Select/iterate/copy the attributes of any object. """
    _T = TypeVar("_T")  # Type of object to copy attributes to

    _AttrPair = tuple[str, Any]  # name-value pair

    # Generator that iterates over attribute name-value pairs
    _IterAttrPairs = Generator[_AttrPair, None, None]

    # Filters to choose which attributes to copy or iterate over
    newFilter = Filter
    METHOD_FILTERS: Filter.FilterFunction = \
        Filter(if_values=[callable]).build()

    def __init__(self, what: Any) -> None:
        """ 
        :param what: Any, the object to select/iterate/copy attributes of. \
            "Attributes of what?" <==> `attributes.Of(what)`
        """
        self.names = get_names(what)  # set(dir(what))
        self.what = what

    def _copy_to(self, an_obj: _T, to_copy: _AttrPair | _IterAttrPairs) -> _T:
        for attr_name, attr_value in to_copy:
            setattr(an_obj, attr_name, attr_value)
        return an_obj

    def add_to(self, an_obj: _T, filter_if: newFilter.FilterFunction,
               exclude: bool = False) -> _T:
        """ Copy attributes and their values into `an_obj`.

        :param an_obj: Any, object to add/copy attributes into.
        :param filter_if: Callable[[str, Any], bool] that returns True if \
            the `str` argument passes all of the name filters and \
            the `Any` argument passes all of the value filters, else False
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :return: Any, an_obj with the specified attributes of this object.
        """
        return self._copy_to(an_obj, self.select(filter_if, exclude))

    @staticmethod
    def attr_is_private(name: str, *_: Any) -> bool:
        """ If an attribute/method name starts with an underscore, then \
            assume that it's private, and vice versa if it doesn't 

        :param name: str, _description_
        :return: bool, _description_
        """
        return name.startswith("_")

    def but_not(self, *others: Any) -> set[str]:
        """
        :param others: Iterable of objects to exclude attributes shared by
        :return: set[str] naming all attributes that are in this object but \
            not in any of the `others`
        """
        return set(self.names) - get_all_names(*others)

    def first_of(self, attr_names: Iterable[str], default: Any = None,
                 method_names: set[str] = set()) -> Any:
        """
        :param attr_names: Iterable[str], attributes to check this object for.
        :param default: Any, what to return if this object does not have any of \
            the attributes named in `attr_names`.
        :param method_names: set[str], the methods named in `attr_names` to call \
            before returning them.
        :return: Any, `default` if this object has no attribute named in \
            `attr_names`; else the found attribute, executed with no \
            parameters (if in `method_names`)
        """
        found_attr = default
        attrs = self.names.intersection(set(attr_names))
        match len(attrs):
            case 0:
                pass  # found_attr = default
            case 1:
                found_attr = getattr(self.what, attrs.pop())
            case _:
                for name in attr_names:
                    if name in self.names:
                        found_attr = getattr(self.what, name)
                        break
        if name in method_names and callable(found_attr):
            found_attr = found_attr()
        return found_attr

    def items(self) -> _IterAttrPairs:
        """ Iterate over all of this object's attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each selected attribute.
        """
        yield from self.select(always_true)

    def methods(self) -> Generator[tuple[str, Callable], None, None]:
        """ Iterate over this object's methods (callable attributes).

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each method of this object.
        """
        yield from self.select(filter_if=self.METHOD_FILTERS)

    def method_names(self) -> list[str]:
        """
        :return: list[str], names of all methods (callable attributes) of \
            this object.
        """
        return [meth_name for meth_name, _ in self.methods()]

    def nested(self, *attribute_names: str) -> Any:
        """ `Of(an_obj).nested("first", "second", "third")` will \
        return `an_obj.first.second.third` if it exists or None otherwise.

        :param attribute_names: Iterable[str] of attribute names. The first \
                                names an attribute of an_obj; the second \
                                names an attribute of the first; etc. 
        :return: Any, the attribute of an attribute ... of an attribute of an_obj
        """
        attributes = list(attribute_names)  # TODO reversed(attribute_names) ?
        to_return = self.what
        while attributes and to_return is not None:
            to_return = getattr(to_return, attributes.pop(0), None)
        return to_return

    def private(self) -> _IterAttrPairs:
        """ Iterate over this object's private attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each private attribute.
        """
        yield from self.select(self.attr_is_private)

    def public(self) -> _IterAttrPairs:
        """ Iterate over this object's public attributes.

        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each public attribute.
        """
        yield from self.select(self.attr_is_private, exclude=True)

    def public_names(self) -> list[str]:
        """
        :return: list[str], names of all public attributes of this object.
        """
        return [attr_name for attr_name, _ in self.public()]

    def select(self, filter_if: newFilter.FilterFunction,
               exclude: bool = False) -> _IterAttrPairs:
        """ Iterate over some of this object's attributes. 

        :param filter_if: Callable[[str, Any], bool] that returns True if \
            the `str` argument passes all of the name filters and \
            the `Any` argument passes all of the value filters, else False
        :param exclude: bool, False to INclude all attributes for which all \
            of the filter functions return True; else False to EXclude them.
        :yield: Generator[tuple[str, Any], None, None] that returns the name \
            and value of each selected attribute.
        """
        for name in self.names:
            attr = getattr(self.what, name)
            if filter_if(name, attr) is not exclude:
                yield name, attr

    def select_all(self, filter_if: newFilter.FilterFunction,
                   exclude: bool = False) -> list[_AttrPair]:
        return [(name, attr) for name, attr in
                self.select(filter_if, exclude)]
