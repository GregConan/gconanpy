#!/usr/bin/env python3

"""
Functions/classes to access and/or modify the attributes of any object(s).
Greg Conan: gregmconan@gmail.com
Created: 2025-06-02
Updated: 2025-09-11
"""
# Import standard libraries
from collections.abc import Callable, Container, Collection, Generator, \
    Iterable, Mapping
from typing import Any, Literal, Self, TypeVar

# Import local custom libraries
try:
    from iters import merge
    from meta import tuplify
    from trivial import always_none, always_true
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.iters import merge
    from gconanpy.meta import tuplify
    from gconanpy.trivial import always_none, always_true


_T = TypeVar("_T")  # Constant: TypeVar for add_to function


def add_to(an_obj: _T, **attributes: Any) -> _T:
    """
    :param an_obj: _T: Any, object to add attributes to
    :return: _T: Any, `an_obj` now with `attributes` added
    """
    for attr_name, attr_value in attributes.items():
        setattr(an_obj, attr_name, attr_value)
    return an_obj


def get_all_names(*objects: Any) -> set[str]:
    """
    :param objects: Iterable of objects to return the attribute names of
    :return: set[str], the name of every attribute of everything in `objects`
    """
    return merge(get_names(an_obj) for an_obj in objects)


def get_names(an_obj: Any) -> set[str]:
    """
    :param an_obj: Any, object to return the attribute names of
    :return: set[str], the name of every attribute of `an_obj`
    """
    names = set()

    # If it's a class, name some attributes of its base class(es)
    bases = getattr(an_obj, "__bases__", None)
    if bases:
        names.update(merge((set(base.__dict__) for base in bases)))

    # Name some of its own attributes
    names.update(dir(an_obj))

    # Name the rest of its own attributes
    dict_attr = getattr(an_obj, "__dict__", None)
    if dict_attr:
        names.update(dict_attr)

    # Filter out absent attribute names
    to_remove = set()
    for attr_name in names:
        if not hasattr(an_obj, attr_name):
            to_remove.add(attr_name)
    names.difference_update(to_remove)

    return names


def has(an_obj: Any, name: str, exclude: Container = set()) -> bool:
    """
    :param name: str
    :param exclude: Container, values to ignore or overwrite. If `an_obj` \
        maps `key` to one, then return True as if `key is not in an_obj`.
    :return: bool, True if `key` is not mapped to a value in `an_obj` or \
        is mapped to something in `exclude`
    """
    if not hasattr(an_obj, name):
        return False

    try:  # If an_obj has the attribute, return True unless it doesn't count
        return getattr(an_obj, name) not in exclude

    # `self.<name> in exclude` raises TypeError if self.<name> isn't Hashable.
    # In that case, self.<name> can't be in exclude, so self has name.
    except TypeError:
        return True


def lazyget(an_obj: Any, name: str,
            get_if_absent: Callable = always_none,
            getter_args: Iterable = list(),
            getter_kwargs: Mapping = dict(),
            exclude: Container = set()) -> Any:
    """ Return the named attribute of `an_obj` if it exists; else \
        return `get_if_absent(*args, **kwargs)`.

    :param an_obj: Any, object to try to get an attribute of.
    :param name: str naming the attribute to try to get.
    :param get_if_absent: Callable, function to get the default value.
    :param getter_args: Iterable[Any] of `get_if_absent` arguments.
    :param getter_kwargs: Mapping[Any] of `get_if_absent` keyword arguments.
    :param exclude: Container of values not to return and instead return \
        `get_if_absent(*getter_args, **getter_kwargs)`.
    :return: Any, the `name` attribute of `an_obj` if it exists and is not \
        in `exclude`; else `get_if_absent(*getter_args, **getter_kwargs)`
    """
    return get_if_absent(*getter_args, **getter_kwargs) if \
        not has(an_obj, name, exclude) else getattr(an_obj, name)


def lazysetdefault(an_obj: Any, name: str, get_if_absent:
                   Callable = always_none, getter_args: Iterable = list(),
                   getter_kwargs: Mapping = dict(),
                   exclude: Container = set()) -> Any:
    """ Return the named attribute of `an_obj` if it exists; else set it \
        it to `get_if_absent(*args, **kwargs)` and return that.

    :param an_obj: Any, object to get (or set) an attribute of.
    :param name: str naming the attribute to get (or set).
    :param get_if_absent: Callable, function to set & return default value.
    :param getter_args: Iterable[Any] of `get_if_absent` arguments.
    :param getter_kwargs: Mapping[Any] of `get_if_absent` keyword arguments.
    :param exclude: Container of possible values to replace with \
        `get_if_absent(*getter_args, **getter_kwargs)` and return (if \
        any of them is the named `an_obj` attribute).
    :return: Any, the `name` attribute of `an_obj` if it exists and is not \
        in `exclude`; else `get_if_absent(*getter_args, **getter_kwargs)`
    """
    if not has(an_obj, name, exclude):
        setattr(an_obj, name, get_if_absent(*getter_args, **getter_kwargs))
    return getattr(an_obj, name)


def setdefault(an_obj: Any, name: str, value: Any,
               exclude: Collection = set()) -> None:
    """ If `an_obj` does not have an attribute called `name`, or if it does \
        but that attribute's value is a member of `exclude`, then set that \
        `name` attribute of `an_obj` to the specified `value`.

    :param an_obj: Any, object to ensure has an attribute with that `name`
    :param name: str naming the attribute to ensure that `an_obj` has
    :param value: Any, new value of the `name` attribute of `an_obj` if that \
        attribute doesn't exist or if its value is in `exclude`
    :param exclude: Collection, values of `an_obj.<name>` to overwrite
    """
    if (getattr(an_obj, name, next(iter(exclude))) in exclude) \
            if exclude else hasattr(an_obj, name):
        setattr(an_obj, name, value)


class Filter:
    _STRSELECTOR = Callable[[str], bool]
    _STRSELECT = _STRSELECTOR | Iterable[_STRSELECTOR]
    _SELECTOR = Callable[[Any], bool]
    _SELECTORS = _SELECTOR | Iterable[_SELECTOR]
    _WHICH = Literal["names", "values"]

    FilterFunction = Callable[[str, Any], bool]

    def __init__(self, names_are: _STRSELECT = tuple(),
                 values_are: _SELECTORS = tuple(),
                 names_arent: _STRSELECT = tuple(),
                 values_arent: _SELECTORS = tuple()) -> None:
        """ _summary_

        :param names_are: Iterable[Callable[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object \
            to check whether the returned generator function should include \
            that attribute (if True) or skip it (if False).
        :param values_are: Iterable[Callable[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute (if True) or skip it (if False).
        :param names_arent: Iterable[Callable[[Any], bool]] of \
            Callables to run on the NAME of every attribute of this object \
            to check whether the returned generator function should include \
            that attribute (if False) or skip it (if True).
        :param values_arent: Iterable[Callable[[Any], bool]] of \
            Callables to run on the VALUE of every attribute of this object, \
            to check whether the returned generator function should include \
            that attribute (if False) or skip it (if True).
        """
        self.names = {True: tuplify(names_are), False: tuplify(names_arent)}
        self.values = {True: tuplify(values_are), False: tuplify(values_arent)}

    __getitem__ = getattr

    def __add__(self, other: Self) -> Self:
        return type(self)(
            *((self[which][are] + other[which][are])
              for which in ("names", "values")
              for are in (True, False))
        )

    def __call__(self, name: str, value: Any) -> Any:
        for selectors, to_check in ((self.names, name),
                                    (self.values, value)):
            for correct in (True, False):
                for is_valid in selectors[correct]:
                    if is_valid(to_check) is not correct:
                        return False
        return True


class AttrsOf:
    """ Select/iterate/copy the attributes of any object. """
    _T = TypeVar("_T")  # Type of object to copy attributes to

    _AttrPair = tuple[str, Any]  # name-value pair

    # Generator that iterates over attribute name-value pairs
    _IterAttrPairs = Generator[_AttrPair, None, None]

    # Filters to choose which attributes to copy or iterate over
    newFilter = Filter
    METHOD_FILTERS = Filter(values_are=callable)

    def __init__(self, what: Any) -> None:
        """
        :param what: Any, the object to select/iterate/copy attributes of. \
            "Attributes of what?" <==> `attributes.AttrsOf(what)`
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

    def select_all(self, filter_if: newFilter.FilterFunction = always_true,
                   exclude: bool = False) -> list[_AttrPair]:
        return [(name, attr) for name, attr in
                self.select(filter_if, exclude)]


class MultiWrapperFactory:
    IsPublicMethod = Filter(values_are=callable,
                            names_arent=AttrsOf.attr_is_private)

    def __init__(self, superclass: type) -> None:
        for meth_name, meth in AttrsOf(superclass).methods():
            ...  # TODO
