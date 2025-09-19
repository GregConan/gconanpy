#!/usr/bin/env python3

"""
Classes that can filter objects to only get the elements (or attributes) \
    that match certain specified conditions.
Greg Conan: gregmconan@gmail.com
Created: 2025-09-18
Updated: 2025-09-18
"""
# Import standard libraries
import abc
from collections.abc import Callable, Hashable, Iterable, Mapping
from typing import Any, get_args, Literal, overload, Self, TypeVar

# Import local custom libraries
try:
    from gconanpy.meta import tuplify
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from meta import tuplify


class BaseFilter(abc.ABC):
    _FILTERDICT = dict[bool, tuple]

    on: tuple[str, ...]

    def __init__(self, **kwargs) -> None:
        for selector_name in self.on:
            setattr(self, selector_name, {
                True: kwargs[selector_name + "_are"],
                False: kwargs[selector_name + "_arent"]
            })

    def __add__(self, other: Self) -> Self:
        """ 
        :param other: Self, `Filter` to combine with this one
        :return: Self, new `Filter` including every filter function in this \
            `Filter` (`self`) and in the other `Filter` (`other`)
        """
        return type(self)(*((self[which][are] + other[which][are])
                          for which in self.on for are in (True, False)))

    def __getitem__(self, key: str) -> _FILTERDICT:
        """ Access `keys` and `values` attributes as elements/items.

        Defined mostly for convenient use by `Filter.__call__` method.

        :param key: _WHICH, either "keys" or "values"
        :return: _FILTERDICT, `getattr(self, key)`; \
            either `self.keys` or `self.values`
        """
        return getattr(self, key)

    def invert(self) -> Self:
        """ 
        :return: Self, inverted version of this `Filter` which will always \
            return the opposite boolean value as the original `Filter`; for \
            any `Filter` `f`, string `s`, and value `v`, \
            `not f.invert()(s, v) is f(s, v)`
        """
        kwargs = {f"{which}_are{'nt' if cond else ''}": self[which][cond]
                  for which in self.on for cond in (True, False)}
        return type(self)(**kwargs)


class Filter(BaseFilter):
    # Private class variables: own method parameters'/returns' type hints
    _SELECTOR = Callable[[Any], bool]  # Any value filter function
    _SELECTORS = _SELECTOR | Iterable[_SELECTOR]  # Any value filter functions
    _STRSELECTOR = Callable[[str], bool]  # str filter function
    _STRSELECT = _STRSELECTOR | Iterable[_STRSELECTOR]  # str filter functions
    _WHICH = Literal["names", "values"]  # Names of each Filter's attributes
    _FILTERDICT = dict[bool, tuple[_SELECTOR, ...]]  # Types of Filter attrs

    # Public class variable: filter type hint for other methods/functions
    FilterFunction = Callable[[str, Any], bool]  # type(Filter(...))

    # Public instance variables: name filters and value filters
    on = tuple(get_args(_WHICH))
    names: _FILTERDICT
    values: _FILTERDICT

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
        super().__init__(names_are=tuplify(names_are),
                         values_are=tuplify(values_are),
                         names_arent=tuplify(names_arent),
                         values_arent=tuplify(values_arent))

    def __call__(self, name: str, value: Any) -> bool:
        """ 
        :param name: str, attribute name to check whether it passes all \
            conditions defined by this `Filter`
        :param value: Any, attribute value to check whether it passes all \
            conditions defined by this `Filter`
        :return: bool, True if the input name/value pair passes all \
            conditions defined by this `Filter`; else False
        """
        for selectors, to_check in ((self.names, name),
                                    (self.values, value)):
            for correct in (True, False):
                for is_valid in selectors[correct]:
                    if is_valid(to_check) is not correct:
                        return False
        return True


class MapSubset[KT, VT](BaseFilter):
    # Private class variables: own method parameters'/returns' type hints
    _M = TypeVar("_M", bound=Mapping)  # Type of Mapping to get subset(s) of
    _T = TypeVar("_T", bound=Mapping)  # Type of Mapping to return

    _WHICH = Literal["keys", "values"]  # Names of each Filter's attributes
    _FILTERDICT = dict[bool, tuple]  # Types of Filter attrs

    # Public class variable: filter type hint for other methods/functions
    FilterFunction = Callable[[Hashable, Any], bool]  # type(Filter(...))

    # Public instance variables: name filters and value filters
    on = tuple(get_args(_WHICH))
    keys: _FILTERDICT
    values: _FILTERDICT

    def __init__(self, keys_are: KT | Iterable[KT] = tuple(),
                 values_are: VT | Iterable[VT] = tuple(),
                 keys_arent: KT | Iterable[KT] = tuple(),
                 values_arent: VT | Iterable[VT] = tuple()) -> None:
        """
        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True for `filter` to return a subset \
            with ONLY the provided `keys`; else False to return a subset \
            with NONE OF the provided `keys`.
        :param include_values: bool, True for `filter` to return a subset \
            with ONLY the provided `values`; else False to return a subset \
            with NONE OF the provided `values`.
        """
        super().__init__(keys_are=tuplify(keys_are),
                         values_are=tuplify(values_are),
                         keys_arent=tuplify(keys_arent),
                         values_arent=tuplify(values_arent))

    def __call__(self, key: KT, value: VT) -> bool:
        for selectors, to_check in ((self.keys, key),
                                    (self.values, value)):
            for correct in (True, False):
                selection = selectors[correct]
                if selection and (to_check in selection) is not correct:
                    return False
        return True

    @overload  # Mapping[KT, VT] #?
    def of(self, from_map: Mapping, as_type: type[_T]) -> _T: ...
    @overload
    def of(self, from_map: _M) -> _M: ...

    def of(self, from_map: Mapping, as_type: type | None = None):
        """ Construct an instance of this class by picking a subset of \
            key-value pairs to keep.

        :param from_map: Mapping to return a subset of.
        :param as_type: type[Mapping], type of Mapping to return; or None to \
            return the same type of Mapping as `from_map`.
        :return: Mapping, `from_map` subset including only the specified \
            keys and values
        """
        filtered = {k: v for k, v in from_map.items() if self(k, v)}
        if as_type is None:
            as_type = type(from_map)
        return as_type(filtered)
