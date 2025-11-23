#!/usr/bin/env python3

"""
Useful/convenient custom extensions of Python's dictionary class.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-11-22
"""
# Import standard libraries
from collections import defaultdict
from collections.abc import (Callable, Collection, Container, Generator,
                             Hashable, Iterable, Mapping, Sequence)
from configparser import ConfigParser
from operator import itemgetter
from typing import Any, cast, get_args, Literal, overload, ParamSpec, \
    Self, TypeVar

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from gconanpy.access.attributes import get_names as get_attr_names
    from gconanpy.bytesify import Bytesifier
    from gconanpy.debug import Debuggable
    from gconanpy.iters import MapWalker, SimpleShredder
    from gconanpy.iters.filters import MapSubset
    from gconanpy.meta import name_of, Traversible
    from gconanpy.meta.typeshed import DATA_ERRORS, SupportsRichComparison
    from gconanpy.trivial import always_none
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from access.attributes import get_names as get_attr_names
    from bytesify import Bytesifier
    from debug import Debuggable
    from iters import MapWalker, SimpleShredder
    from iters.filters import MapSubset
    from meta import name_of, Traversible
    from meta.typeshed import DATA_ERRORS, SupportsRichComparison
    from trivial import always_none

# Type variables for .__init__(...) and .update(...) method input parameters
MapParts = Iterable[tuple[Hashable, Any]]
FromMap = TypeVar("FromMap", Mapping, MapParts, None)


class CustomDict[KT, VT](dict[KT, VT]):
    """ Custom dict base class that explicitly includes its class name in \
        its string representation(s) via __repr__ method. """

    def __repr__(self) -> str:
        """
        :return: str, string representation of custom dict class including \
                 its class name: "CustomDict({...})"
        """  # Not super() because that messes up distant subclasses' __repr__
        return f"{name_of(self)}({dict.__repr__(self)})"

    def copy(self) -> Self:
        """ `D.copy()` -> a shallow copy of `D`. 

        :return: Self, another instance of this same type of custom \
            dictionary with the same contents.
        """
        return self.__class__(self)


class Exclutionary[KT, VT](CustomDict[KT, VT]):
    """ Custom dict class that adds `exclude=` options to `dict` methods, \
        letting it ignore specified values as if they were blank. It also
        has extended functionality centered around the `default=` option, \
        functionality used by various other CustomDicts. The Exclutionary \
        can also use `setdefault` on many different elements at once via \
        `setdefaults`. `LazyDict` base class. Previously "Defaultionary".
    """
    _D = TypeVar("_D")  # Type hint for "default" parameter

    def chain_get(self, keys: Sequence[KT], default: _D = None,
                  exclude: Container[VT] = set()) -> VT | _D:
        """ Return the value mapped to the first key if any, else return \
            the value mapped to the second key if any, ... etc. recursively. \
            Return `default` if this dict doesn't contain any of the `keys`.

        :param keys: Sequence[KT], keys mapped to the value to return
        :param default: _D: Any, object to return if none of the `keys` are \
            in this Exclutionary
        :param exclude: Container[VT], values to ignore or overwrite. If one \
            of the `keys` is mapped to a value in `exclude`, then skip that \
            key as if `key is not in self`.
        :return: Any, value mapped to the first key (of `keys`) in this dict \
            if any; otherwise `default` if no `keys` are in this dict.
        """
        for key in keys:
            if self.has(key, exclude):
                return self[key]
        return default

    def get(self, key: KT, default: _D = None,
            exclude: Container[VT] = set()) -> VT | _D:
        """ Return the value mapped to `key` in `self`, if any; else return \
            `default`. Defined to add `exclude` option to `dict.get`.

        :param key: KT: Hashable, key mapped to the value to return
        :param default: _D: Any, object to return `if not self.has` the key, \
            i.e. `if key not in self or self[key] in exclude`
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, then return True as if `key is not in self`.
        :return: VT | _D, value `self` maps to `key` if any; else `default`
        """
        return self[key] if self.has(key, exclude) else default

    def has(self, key: KT, exclude: Container[VT] = set()) -> bool:
        """
        :param key: KT: Hashable
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `self` maps `key` to one, then return False as if \
            `key is not in self`.
        :return: bool, True if `key` is mapped to a value in `self` and \
            is not mapped to anything in `exclude`.
        """
        try:  # If we have the key, return True unless its value doesn't count
            result = self[key] not in exclude

        except KeyError:  # If we don't have the key, return False
            result = False

        # `self[key] in exclude` raises TypeError if self[key] isn't Hashable.
        # In that case, self[key] can't be in exclude, so self has key.
        except TypeError:
            result = True

        return result

    def has_all(self, keys: Iterable[KT], exclude: Container[VT] = set()
                ) -> bool:
        """
        :param keys: Iterable[KT], keys to find in this Exclutionary.
        :param exclude: Container[VT], values to overlook/ignore such that \
            if `self` maps a key to one of those values, then this method \
            will return False as if `key is not in self`.
        :return: bool, True if every key in `keys` is mapped to a value that \
            is not in `exclude`; else False.
        """
        try:
            next(self.missing_keys(keys, exclude))
            return False
        except StopIteration:
            return True

    def missing_keys(self, keys: Iterable[KT], exclude: Container[VT] = set()
                     ) -> Generator[KT, None, None]:
        """
        :param keys: Iterable[KT], keys to find in this Exclutionary.
        :param exclude: Container[VT], values to overlook/ignore such that \
            if `self` maps a key to one of those values, then this method \
            will yield that key as if `key is not in self`.
        :yield: Generator[KT, None, None], all `keys` that either are not in \
            this Exclutionary or are mapped to a value in `exclude`.
        """
        if exclude:
            for key in keys:
                if not self.has(key, exclude):
                    yield key
        else:
            for key in keys:
                if key not in self:
                    yield key

    @overload
    def setdefaults(self, **kwargs: VT) -> None: ...
    @overload
    def setdefaults(self, exclude: Container[VT], **kwargs: VT) -> None: ...

    def setdefaults(self, exclude=set(), **kwargs: VT) -> None:
        """ Fill any missing values in self from kwargs.
            `dict.update` prefers to overwrite old values with new ones.
            `setdefaults` is like `update`, but prefers to keep old values.

        :param exclude: Container[VT], values to overlook/ignore such that \
            if `self` maps `key` to one of those values, then this method \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key is not in self`.
        :param kwargs: Mapping[str, Any] of values to add to self if needed.
        """
        for key in self.missing_keys(cast(Iterable[KT], kwargs), exclude):
            self[key] = kwargs[cast(str, key)]


class Invertionary(CustomDict):
    # Type variables for invert method
    _K = bool | Literal["unpack"]  # type[Collection]  # TODO

    # def invert(self, keep_keys_in: _KeyBag = None) -> None: ...  # TODO
    @overload
    def invert(self, keep_keys: _K = False) -> None: ...
    @overload
    def invert(self, keep_keys=False, copy: Literal[True] = True) -> Self: ...

    @overload
    def invert(self, keep_keys=False,
               copy: Literal[False] = False) -> None: ...

    def invert(self, keep_keys: _K = False, copy: bool = False):
        """ Swap keys and values. Inverting {1: 2, 3: 4} returns {2: 1, 4: 3}.

        When 2+ keys are mapped to the same value, then that value will be \
        mapped either to a `keep_collisions_in` container of all of those \
        keys or (by default) to only the most recently-added key.

        :param keep_keys: True to map each value to a list of the keys that \
            previously were mapped to it, False to only keep the last key mapped \
            to each value, or "unpack" (if every value is iterable) to map each \
            element of each value to a list of the previously-mapped keys.
        :param copy: bool, True to return an inverted copy of this \
            Invertionary instead of inverting the original; else False to \
            invert the original and return None. Defaults to False
        :return: Self if `copy=True`, else None
        """
        # If we are NOT keeping all keys mapped to the same value, then
        # just keep whichever key was added most recently
        if not keep_keys:
            inverted = {v: k for k, v in self.items()}

        else:  # If we ARE keeping all keys mapped to the same value, then:
            inverted = defaultdict(list)  # Avoid conflating keys & values

            # "Shred" each iterable value to map each of its elements to key
            if keep_keys == "unpack":
                shredder = SimpleShredder()
                for key, value in self.items():
                    for subval in shredder.shred(value):
                        inverted[subval].append(key)
                    shredder.reset()

            else:  # If keep_keys=True, then simply keep the keys in a list
                for key, value in self.items():
                    inverted[value].append(key)
        if copy:
            return type(self)(inverted)
        else:
            self.clear()
            self.update(inverted)


class Sortionary[KT: SupportsRichComparison, VT: SupportsRichComparison
                 ](CustomDict[KT, VT]):
    """ Custom dict class that can yield a generator of its key-value pairs \
        sorted in order of either keys or values. """
    _BY = Literal["keys", "values"]
    _WHICH: dict[_BY, itemgetter] = {"keys": itemgetter(0),
                                     "values": itemgetter(1)}

    def sorted_by(self, by: _BY, descending: bool = False
                  ) -> Generator[tuple[KT, VT], None, None]:
        """ Adapted from https://stackoverflow.com/a/50569360

        :param by: Literal["keys", "values"], "keys" to yield key-value \
            pairings sorted by keys; else "values" to sort them by values
        :param descending: bool, True to yield the key-value pairings with \
            the largest ones first; else False to yield the smallest first; \
            defaults to False
        :yield: Generator[tuple[KT, VT], None, None], each key-value pairing \
            in this Sortionary as a tuple, sorted `by` keys or values in \
            ascending or `descending` order
        """
        for k, v in sorted(self.items(), key=self._WHICH[by],
                           reverse=descending):
            yield (k, v)


class Subsetionary[KT, VT](CustomDict[KT, VT]):

    @classmethod
    def from_subset_of(cls, from_map: Mapping,
                       keys_are: KT | Iterable[KT] = set(),
                       values_are: VT | Iterable[VT] = set(),
                       keys_arent: KT | Iterable[KT] = set(),
                       values_arent: VT | Iterable[VT] = set()) -> Self:
        """ Convert a subset of `from_map` into a new `Subsetionary`.

        :param from_map: Mapping to create a new Subsetionary from a subset of.
        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True to return a subset of this dict with \
            ONLY the provided `keys`; else False to return a subset with \
            NONE OF the provided `keys`.
        :param include_values: bool, True to return a subset with \
            ONLY the provided `values`; else False to return a subset with \
            NONE OF the provided `values`.
        :return: Subsetionary including only the specified keys and values.       
        """
        return MapSubset[KT, VT](keys_are, values_are, keys_arent,
                                 values_arent).of(from_map, cls)

    def subset(self, keys_are: KT | Iterable[KT] = set(),
               values_are: VT | Iterable[VT] = set(),
               keys_arent: KT | Iterable[KT] = set(),
               values_arent: VT | Iterable[VT] = set()) -> Self:
        """ Create a new `Subsetionary` including only a subset of this one.

        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True to return a subset of this dict with \
            ONLY the provided `keys`; else False to return a subset with \
            NONE OF the provided `keys`.
        :param include_values: bool, True to return a subset with \
            ONLY the provided `values`; else False to return a subset with \
            NONE OF the provided `values`.
        :return: Subsetionary including only the specified keys and values.       
        """
        return MapSubset[KT, VT](keys_are, values_are, keys_arent,
                                 values_arent).of(self)


class Updationary[KT, VT](CustomDict[KT, VT]):

    def __init__(self, from_map: FromMap = None, **kwargs: Any) -> None:
        """
        :param from_map: Mapping | Iterable[tuple[Hashable, Any]] | None, \
            Mapping to convert into a new instance of this class; `map` or \
            `iterable` in `dict.__init__` method; None by default to create \
            an empty dictionary (or create a dict from `kwargs` alone).
        :param kwargs: Mapping[str, Any] of values to add to this Updationary.
        """
        self.update(from_map, **kwargs)

    @overload
    def update(self, from_map: FromMap, **kwargs: Any) -> None: ...

    @overload
    def update(self, from_map: FromMap, copy: bool = True,
               **kwargs: Any) -> Self: ...

    def update(self, from_map=None, copy=False, **kwargs):
        """ Add or overwrite items in this Mapping from other Mappings.

        :param from_map: Mapping | Iterable[tuple[Hashable, Any] ] | None \
            of key-value pairs to save into this Updationary. Overwrites \
            existing pairs, but can be overwritten by `kwargs`. Defaults to \
            None. Effectively the same as `m` in `dict.update` method. 
        :param copy: bool, True to return an updated copy of this \
            Updationary instead of updating the original; else False to \
            update the original and return None.
        :param kwargs: Mapping[str, Any] of key-value pairs to save into \
            this Updationary. If `kwargs` and `from_map` map the same key to \
            different values, then the value in `kwargs` will be saved.
        :return: None if copy=False; else a dict of the same class as `self`.
        """
        updated = self.copy() if copy else self
        run_update = super(Updationary, updated).update
        for each_map in from_map, kwargs:  # kwargs can overwrite from_map
            if each_map:
                run_update(each_map)  # type: ignore  # TODO
        if copy:
            return updated


class Walktionary[KT, VT](CustomDict[KT, VT]):
    def walk(self, only_yield_maps: bool = True) -> MapWalker:
        """ Recursively iterate over this dict and every dict inside it. \
            Defined explicitly to make `only_yield_maps` default to True.

        :param only_yield_maps: bool, True for this iterator to return \
            key-value pairs only if the value is also a `Mapping`; else \
            False to return every item iterated over. Defaults to True.
        :return: MapWalker with `keys`, `values`, and `items` methods to \
            recursively iterate over this `Walktionary`.
        """
        return MapWalker(self, only_yield_maps)


class OverlapPercents[Sortable: SupportsRichComparison
                      ](CustomDict[str, Sortionary[Sortable, float]]):
    def __init__(self, **collecs: Collection[Sortable]) -> None:
        """ Calculate what percentage of the elements of each `Collection` \
            are also in each other `Collection`.

        :param collecs: Mapping[str, Collection[Sortable]] of each \
            `Collection`'s name to its elements.
        """
        for collecname, collec in collecs.items():
            # Define & fill before adding to self in order to appease pyright
            sorty = Sortionary()
            for othername, othercollns in collecs.items():
                sorty[othername] = \
                    len(collec) / len(set(collec) | set(othercollns))

            self[collecname] = sorty  # Add to self

    def sorted_by(self, key: str, descending: bool = True
                  ) -> Generator[Sortable, None, None]:
        for sortable_subkey, _ in self[key].sorted_by("values", descending):
            yield sortable_subkey


class DotDict[KT: str, VT](Updationary[KT, VT], Traversible):
    """ dict with dot.notation item access. Compare `sklearn.utils.Bunch`.
        DotDict can get/set items as attributes: if `name` is not protected, \
        then `self.name is self["name"]`.

    Benefit: You can get/set items by using '.' or key names in brackets.
    Keeps most core functionality of the Python dict type.

    Adapted from answers to https://stackoverflow.com/questions/2352181 and \
    `attrdict` from https://stackoverflow.com/a/45354473 and `dotdict` from \
    https://github.com/dmtlvn/dotdict/blob/main/dotdict/dotdict.py
    """
    _D = TypeVar("_D")  # Default option input parameter type hint for lookup

    # Attributes, methods, and other keywords that should not be
    # mutable/modifiable as items/key-value pairs. Define them all explicitly
    # so static type checkers can distinguish between using dot notation to
    # get a named attribute and using it as shorthand to get a value/item.
    _PROTECTEDS = "__protected_keywords__"
    _ATTR = Literal[
        '__class__', '_D', '__dict__', '__doc__', '__module__',
        '__orig_bases__', '__parameters__', '__type_params__',
        '_ATTR', '_METHODS', '__protected_keywords__', "traversed"]
    _METHODS = Literal[
        '__class_getitem__', '__contains__', '__delattr__', '__delitem__',
        '__dir__', '__eq__', '__format__', '__ge__', '__getattr__',
        '__getattribute__', '__getitem__', '__getstate__', '__gt__',
        '__init__', '__init_subclass__', '__ior__', '__iter__', '__le__',
        '__len__', '__lt__', '__ne__', '__new__', '__or__', '__reduce__',
        '__reduce_ex__', '__repr__', '__reversed__', '__ror__',
        '__setattr__', '__setitem__', '__setstate__', '__sizeof__',
        '__str__', '__subclasshook__', '__weakref__', '_is_ready_to',
        '_will_now_traverse', 'clear', 'copy', 'fromConfigParser',
        'fromkeys', 'get', 'get_subset_from_lookups', 'homogenize', 'items',
        'keys', 'lookup', 'pop', 'popitem', 'setdefault', 'update', 'values']

    def __init__(self, from_map: FromMap = None, **kwargs: VT) -> None:
        """ 
        :param from_map: Mapping | Iterable[tuple[Hashable, Any]] | None, \
            Mapping to convert into a new instance of this class; `map` or \
            `iterable` in `dict.__init__` method; defaults to None.
        :param kwargs: Mapping[str, Any] of values to add to this DotDict.
        """
        # Fill this DotDict by initializing as an Updationary
        Updationary.__init__(self, from_map, **kwargs)

        # Initialize self as a Traversible for self.homogenize() method
        Traversible.__init__(self)

        # Ensure that any subclasses' attributes are protected as well
        dict.__setattr__(self, self._PROTECTEDS,
                         {*get_args(self._ATTR), *get_args(self._METHODS),
                          }.union(get_attr_names(self)))

    def __delattr__(self, name: KT) -> None:
        """ Implement `delattr(self, name)`. Same as `del self[name]`.
            Deletes item (key-value pair) instead of attribute.

        :param name: str naming the item in self to delete.
        """
        _delattr = self.__delitem__ \
            if self._is_ready_to("delete", name, AttributeError) \
            else super(DotDict, self).__delattr__
        return _delattr(name)

    @overload
    def __getattribute__(self, name: _METHODS) -> Callable: ...
    @overload
    def __getattribute__(self, name: _ATTR) -> Any: ...
    @overload
    def __getattribute__(self, name: KT) -> VT: ...

    def __getattribute__(self, name):
        # Overloaded instead of __getattr__ because otherwise static type
        # checkers won't recognize value types when accessed with dot notation
        """ `self.__getattribute__(name) == getattr(self, name) == self.<name>`
            If name is not protected, then `self.name is self["name"]`

        Effectively the same as `__getattr__ = dict.__getitem__` except that \
        `hasattr(self, <not in dict>)` works (it doesn't raise a `KeyError`) \
        and type checkers can infer types of keys accessed with dot notation.

        :param name: str naming the attribute/element of self to return.
        :raises AttributeError: if name is not an item or attribute of self.
        :return: Any, `getattr(self, name)` and/or `self[name]`
        """
        try:  # First, try to get an attribute (e.g. a method) of this object
            return object.__getattribute__(self, name)
        except AttributeError as err:

            try:  # Next, get a value mapped to the key, if any
                return object.__getattribute__(self, "__getitem__")(name)

            # If neither exists, then raise AttributeError
            except KeyError:  # Don't raise KeyError; it breaks hasattr
                raise err from None  # Only show 1 exception in the traceback

    def __getstate__(self) -> Self:
        """ Returns self unchanged. Required for pickling. """
        return self

    def __setattr__(self, name: KT, value: Any) -> None:
        """ Implement `setattr(self, name, value)`. Same as \
            `self[name] = value`. Explicitly defined to include \
            `_is_ready_to` check preventing user from overwriting \
            protected attributes/methods.

        :param name: str naming the attribute/key to map the value to
        :param value: Any, the value of the new attribute/item
        """
        _setattr = self.__setitem__ \
            if self._is_ready_to("overwrite", name, AttributeError) \
            else super(DotDict, self).__setattr__
        return _setattr(name, value)

    def __setitem__(self, key: KT, value: Any) -> None:
        """ Set self[key] to value. Explicitly defined to include \
            `_is_ready_to` check preventing user from overwriting \
            protected attributes/methods.

        :param key: str naming the key to map the value to
        :param value: Any, the value of the new item
        """
        self._is_ready_to("overwrite", key, KeyError)
        return super(DotDict, self).__setitem__(key, value)

    def __setstate__(self, state: Mapping) -> None:
        """ Required for pickling.

        :param state: Mapping of key-value pairs to update this `DotDict` with.
        """
        self.update(state)
        self.__dict__: dict[KT, Any] = self

    def _is_ready_to(self, alter: str, attr_name: str, err_type:
                     type[BaseException]) -> bool:
        """ Check if an attribute of self is protected or if it's alterable

        :param alter: str, verb naming the alteration
        :param attribute_name: str, name of the attribute of self to alter
        :raises err_type: if the attribute is protected
        :return: bool, True if the attribute is not protected; \
                 else raise error
        """
        protecteds = getattr(self, "__protected_keywords__", ())
        if attr_name in protecteds:
            raise err_type(f"Cannot {alter} read-only '{name_of(self)}' "
                           f"object attribute '{attr_name}'")
        else:
            return bool(protecteds)

    @classmethod
    def fromConfigParser(cls, config: ConfigParser) -> Self:
        """
        :param config: ConfigParser to convert into DotDict
        :return: DotDict with the key-value mapping structure of config
        """
        self = cls({section: {k: v for k, v in config.items(section)}
                    for section in config.sections()})
        self.homogenize()
        return self

    def get_subset_from_lookups(self, to_look_up: Mapping[KT, str],
                                sep: str = ".", default: Any = None) -> Self:
        """ `self.get_subset_from_lookups({"a": "b/c"}, sep="/")` \
            -> `DotDict({"a": self.b.c})`

        :param to_look_up: Mapping[str, str] of every key to put in the \
            returned DotDict to the path to its value in this DotDict (`self`)
        :param sep: str, separator between subkeys in `to_look_up.values()`, \
            defaults to "."
        :param default: Any, value to map to any keys not found in `self`; \
            defaults to None
        :return: Self mapping every key in `to_look_up` to the value \
            at its mapped path in `self`
        """
        return type(self)({key: self.lookup(path, sep, default)
                           for key, path in to_look_up.items()})

    def homogenize(self, replace: type[dict] = dict) -> None:
        """ Recursively transform every dict contained inside this DotDict \
            into a DotDict itself, ensuring nested dot access to attributes.
            From https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param replace: type of element/child/attribute to change to DotDict.
        """
        cls = type(self)
        for k, v in self.items():
            if self._will_now_traverse(v) and isinstance(v, replace):
                if not isinstance(v, cls):
                    self[k] = cls(v)
                cast(DotDict, self[k]).homogenize()

    def lookup(self, path: str, sep: str = ".", default: _D = None) -> VT | _D:
        """ Get the value mapped to a key in nested structure. Adapted from \
            https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param path: str, path to key in nested structure, e.g. "a.b.c"
        :param sep: str, separator between keys in path; defaults to "."
        :param default: _D: Any, value to return if key is not found
        :return: _VT | _D, value mapped to nested key, if any; else default
        """
        keypath = list(reversed(path.split(sep)))
        retrieved = self
        try:
            while keypath:
                key = keypath.pop()
                try:
                    retrieved = cast(Mapping[str, VT], retrieved)[key]
                except KeyError:
                    retrieved = cast(Mapping[int, VT], retrieved)[int(key)]

        # If value is not found, then return the default value
        except DATA_ERRORS:
            retrieved = default
        return default if keypath else cast(VT, retrieved)


class LazyDict[KT, VT](Updationary[KT, VT], Exclutionary[KT, VT]):
    """ Dict that can get/set items and ignore the default parameter \
        until/unless it is needed, ONLY evaluating it after failing to \
        get/set an existing key. Benefit: The `default=` code does not \
        need to be valid (yet) if self already has the key. If you pass a \
        function to a "lazy" method, then that function only needs to work \
        if a value is missing.

    Keeps most core functionality of the Python `dict` type.
    Extended `LazyButHonestDict` from https://stackoverflow.com/q/17532929 """
    _D = TypeVar("_D")  # Default output returned by lazy getter function
    _P = ParamSpec("_P")  # Input arguments for lazy getter functions

    def lazyget(self, key: KT, get_if_absent: Callable[_P, _D] = always_none,
                exclude: Container[VT] = set(), *args: _P.args,
                **kwargs: _P.kwargs) -> VT | _D:
        """ Adapted from `LazyButHonestDict.lazyget` from \
            https://stackoverflow.com/q/17532929

        :param key: KT, a key this LazyDict might map to the value to return
        :param get_if_absent: Callable that returns the default value
        :param args: Iterable[Any], `get_if_absent` arguments
        :param kwargs: Mapping, `get_if_absent` keyword arguments
        :param exclude: Container[VT] of possible values which (if they are \
            mapped to `key` in `self`) won't be returned; instead returning \
            `get_if_absent(*args, **kwargs)`
        :return: VT, the value that this dict maps to `key`, if that value \
            isn't in `exclude`; else `return get_if_absent(*args, **kwargs)`
        """
        return self[key] if self.has(key, exclude) else \
            get_if_absent(*args, **kwargs)

    def lazysetdefault(self, key: KT, get_if_absent: Callable[_P, VT]
                       = always_none, exclude: Container[VT] = set(),
                       *args: _P.args, **kwargs: _P.kwargs) -> VT:
        """ Return the value for key if key is in this `LazyDict` and not \
            in `exclude`; else add that key to this `LazyDict`, set its \
            value to `get_if_absent(*args, **kwargs)`, and then return that.

        Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: KT, a key this LazyDict might map to the value to return
        :param get_if_absent: Callable, function to set & return default value
        :param args: Iterable[Any], `get_if_absent` arguments
        :param kwargs: Mapping, `get_if_absent` keyword arguments
        :param exclude: Container[VT] of possible values to replace with \
            `get_if_absent(*args, **kwargs)` and return if \
            they are mapped to `key` in `self` but not in `exclude`
        :return: VT, the value that this dict maps to `key`, if that value \
            isn't in `exclude`; else `return get_if_absent(*args, **kwargs)`
        """
        if not self.has(key, exclude):
            self[key] = get_if_absent(*args, **kwargs)
        return self[key]


class Promptionary[KT, VT](LazyDict[KT, VT]):
    """ LazyDict able to interactively prompt the user to fill missing values.
    """

    def get_or_prompt_for(self, key: KT, prompt: str,
                          prompt_fn: Callable[[str], str] = input,
                          exclude: Container[VT] = set()) -> VT | str:
        """ Return the value mapped to key in self if one already exists and \
            is not in `exclude`; else prompt the user to interactively \
            provide it and return that.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container[VT], values to ignore or overwrite. If \
            `self` maps `key` to one, prompt the user as if \
            `key is not in self`.
        :return: Any, the value mapped to `key` if one exists, else the \
                 value that the user interactively provided
        """
        return self.lazyget(key, prompt_fn, exclude, prompt)

    def setdefault_or_prompt_for(self, key: KT, prompt: str,
                                 prompt_fn: Callable[[str], VT] = input,
                                 exclude: Container[VT] = set()) -> VT:
        """ Return the value mapped to key in self if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str possibly mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, prompt the user as if `key is not in self`.
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazysetdefault(key, prompt_fn, exclude, prompt)


class Cryptionary(Promptionary, Bytesifier, Debuggable):
    """ Extended Promptionary that automatically encrypts values before \
        storing them and automatically decrypts values before returning them.
        Created to store user credentials slightly more securely, and to \
        slightly reduce the likelihood of accidentally exposing them. """

    def __init__(self, from_map: FromMap = None,
                 debugging: bool = False, **kwargs: Any) -> None:
        """ Create a new Cryptionary.

        :param from_map: MapParts to convert into a new Cryptionary.
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        :param kwargs: Mapping[str, Any] of values to encrypt and add.
        """
        try:  # Create encryption mechanism
            self.encrypted = set()
            self.cryptor = Fernet(Fernet.generate_key())

            # Define whether to raise any error(s) or pause and interact
            Debuggable.__init__(self, debugging)

            # Encrypt every value in the input mapping(s)/dict(s)
            self.update(from_map, **kwargs)

        except TypeError as err:
            self.debug_or_raise(err, locals())

    def __delitem__(self, key: Hashable) -> None:
        """ Delete self[key].

        :param key: Hashable, key to delete and to delete the value of.
        """
        self.encrypted.discard(key)
        del self[key]

    def __getitem__(self, key: Hashable) -> Any:
        """ `x.__getitem__(y)` <==> `x[y]`
        Explicitly defined to automatically decrypt encrypted values.

        :param key: Hashable, key mapped to the value to retrieve
        :return: Any, the decrypted value mapped to dict_key
        """
        try:
            retrieved = dict.__getitem__(self, key)
            if key in self.encrypted and retrieved is not None:
                retrieved = self.cryptor.decrypt(retrieved).decode("utf-8")
            return retrieved
        except (KeyError, TypeError) as e:
            self.debug_or_raise(e, locals())

    def __setitem__(self, key: Hashable, value: Any) -> None:
        """ Set `self[dict_key]` to `dict_value` after encrypting \
            `dict_value` if possible.

        :param key: Hashable, key mapped to the value to retrieve.
        :param value: Any, value to encrypt (if it `SupportsBytes`) and store.
        """
        try:
            bytesified = self.bytesify(value, errors="ignore")
            if value is not bytesified:
                bytesified = self.cryptor.encrypt(bytesified)
                self.encrypted.add(key)
            return super(Cryptionary, self).__setitem__(key, bytesified)
        except AttributeError as err:
            self.debug_or_raise(err, locals())

    def update(self, from_map: FromMap = None, **kwargs: Any) -> None:
        """ Add or overwrite items in this Mapping from other Mappings.

        :param from_map: Mapping | Iterable[tuple[Hashable, Any] ] | None, \
            `m` in `dict.update` method; defaults to None
        """
        map_iters: list[Iterable] = [kwargs.items()]
        match from_map:
            case Mapping():
                map_iters.append(from_map.items())
            case tuple():
                map_iters.append(from_map)
        for each_map_iter in map_iters:
            for k, v in each_map_iter:
                self[k] = v


class LazyDotDict[KT: str, VT](DotDict[KT, VT], LazyDict[KT, VT]):
    """ LazyDict with dot.notation item access. It can get/set items...

    ...as object-attributes: `self.item is self['item']`. Benefit: You can \
        get/set items by using '.' or by using variable names in brackets.

    ...and ignore the `default=` code until it's needed, ONLY evaluating it \
        after failing to get/set an existing key. Benefit: The `default=` \
        code does not need to be valid (yet) if self already has the key.

    Adapted from answers to https://stackoverflow.com/questions/2352181 and \
    `attrdict` from https://stackoverflow.com/a/45354473 and `dotdict` from \
    https://github.com/dmtlvn/dotdict/blob/main/dotdict/dotdict.py and then \
    combined with LazyButHonestDict from https://stackoverflow.com/q/17532929

    Keeps most core functionality of the Python `dict` type. """


class DotPromptionary[KT: str, VT](LazyDotDict[KT, VT], Promptionary[KT, VT]):
    """ Promptionary with dot.notation item access. """


class SubCryptionary[KT, VT](Cryptionary, Subsetionary[KT, VT]):
    """ Cryptionary with subset access/creation methods. """


class FancyDict[KT: str, VT: SupportsRichComparison
                ](DotPromptionary[KT, VT], Invertionary, Sortionary[KT, VT],
                  Subsetionary[KT, VT], Walktionary[KT, VT]):
    """ Custom dict combining as much functionality from the other classes \
        defined in this file as possible: enhanced default/update methods; \
        lazy methods; methods to invert, sort, or walk the dict; prompt \
        methods; to/from subset methods; and dot.notation item access. """
