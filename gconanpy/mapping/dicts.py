#!/usr/bin/env python3

"""
Useful/convenient custom extensions of Python's dictionary class.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-07-07
"""
# Import standard libraries
from collections import defaultdict
from collections.abc import (Callable, Collection, Container, Generator,
                             Hashable, Iterable, Mapping, Sequence)
from configparser import ConfigParser
from typing import Any, overload, TypeVar
from typing_extensions import Self

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from .. import attributes, mapping
    from ..debug import Debuggable
    from ..meta.funcs import DATA_ERRORS, name_of
    from ..trivial import always_none
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy import attributes, mapping
    from gconanpy.debug import Debuggable
    from gconanpy.meta.funcs import DATA_ERRORS, name_of
    from gconanpy.trivial import always_none

# Type variables for .__init__(...) and .update(...) method input parameters
MapParts = Iterable[tuple[Hashable, Any]]
FromMap = TypeVar("FromMap", Mapping, MapParts, None)


class Explictionary(dict):
    """ Custom dict base class that explicitly includes its class name in \
        its string representation(s) via __repr__ method. """

    def __repr__(self) -> str:
        """
        :return: str, string representation of custom dict class including \
                 its class name: "Explictionary({...})"
        """
        return f"{name_of(self)}({super()})"

    def copy(self) -> Self:
        """ `D.copy()` -> a shallow copy of `D`. Return another instance \
            of this same type of custom dictionary. """
        return self.__class__(self)

    def to_dict(self) -> dict:
        """
        :return: `dict` with all of the key-value pairings from this custom \
            dictionary. Retrieves values exclusively using `dict` methods. \
            Used by (e.g.) `Cryptionary.__repr__` to skip decryption.
        """
        return {key: dict.__getitem__(self, key) for key in dict.keys(self)}


class Defaultionary(Explictionary):
    """ Custom dict class with extended functionality centered around the \
        `default=` option, functionality used by various other custom dicts. \
        The Defaultionary can ignore specified values as if they were blank \
        in its `get` method. It can also use `setdefault` on many different \
        elements at once via `setdefaults`. `LazyDict` base class.
    """
    _K = TypeVar("_K", bound=Hashable)

    def _will_getdefault(self, key: Hashable, exclude: Container = set()
                         ) -> bool:
        """
        :param key: Hashable
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, then return True as if `key is not in self`.
        :return: bool, True if `key` is not mapped to a value in `self` or \
            is mapped to something in `exclude`
        """
        return key not in self or self[key] in exclude

    def chain_get(self, keys: Sequence[Hashable], default: Any = None,
                  exclude: Container = set()) -> Any:
        """ Return the value mapped to the first key if any, else return \
            the value mapped to the second key if any, ... etc. recursively. \
            Return `default` if this dict doesn't contain any of the `keys`.

        :param keys: Sequence[Hashable], keys mapped to the value to return
        :param default: Any, object to return if no `keys` are in this dict
        :param exclude: Container, values to ignore or overwrite. If one \
            of the `keys` is mapped to a value in `exclude`, then skip that \
            key as if `key is not in self`.
        :return: Any, value mapped to the first key (of `keys`) in this dict \
            if any; otherwise `default` if no `keys` are in this dict.
        """
        return self.get(keys[0], self.chain_get(keys[1:], default), exclude
                        ) if keys else default

    def get(self, key: Hashable, default: Any = None,
            exclude: Container = set()) -> Any:
        """ Return the value mapped to `key` in `self`, if any; else return \
            `default`. Defined to add `exclude` option to `dict.get`.

        :param key: Hashable, key mapped to the value to return
        :param default: Any, object to return `if self.will_getdefault`, \
            i.e. `if key not in self or self[key] in exclude`
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, then return True as if `key is not in self`.
        :return: Any, value mapped to `key` in `self` if any, else `default`
        """
        return default if self._will_getdefault(key, exclude) else self[key]

    def has_all(self, keys: Iterable, exclude: Collection = set()) -> bool:
        """
        :param keys: Iterable[_K], keys to find in this Defaultionary.
        :param exclude: Collection, values to overlook/ignore such that if \
            `self` maps a key to one of those values, then this function \
            will return False as if `key is not in self`.
        :return: bool, True if every key in `keys` is mapped to a value that \
            is not in `exclude`; else False.
        """
        try:
            next(self.missing_keys(keys, exclude))
            return False
        except StopIteration:
            return True

    def missing_keys(self, keys: Iterable[_K], exclude: Collection = set()
                     ) -> Generator[_K, None, None]:
        """
        :param keys: Iterable[_K], keys to find in this Defaultionary.
        :param exclude: Collection, values to overlook/ignore such that if \
            `self` maps a key to one of those values, then this function \
            will yield that key as if `key is not in self`.
        :yield: Generator[_K, None, None], all `keys` that either are not in \
            this Defaultionary or are mapped to a value in `exclude`.
        """
        if exclude:
            example_exclude = next(iter(exclude))
            for key in keys:
                if self.get(key, example_exclude, exclude) is example_exclude:
                    yield key
        else:
            for key in keys:
                if key not in self:
                    yield key

    @overload
    def setdefaults(self, **kwargs: Any) -> None: ...
    @overload
    def setdefaults(self, exclude: Collection, **kwargs: Any) -> None: ...

    def setdefaults(self, exclude=set(), **kwargs) -> None:
        """ Fill any missing values in self from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param exclude: Collection, values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key is not in self`.
        :param kwargs: Mapping[str, Any] of values to add to self if needed.
        """
        for key in self.missing_keys(kwargs.keys(), exclude):
            self[key] = kwargs[key]


class Invertionary(Explictionary):
    # Type variables for invert method
    _T = TypeVar("_T")
    # _KeyBag = type[Collection] | None  # TODO

    # def invert(self, keep_keys_in: _KeyBag = None) -> None: ...  # TODO

    @overload
    def invert(self, keep_keys: bool = False) -> None: ...
    @overload
    def invert(self, keep_keys: bool = False, copy: bool = True) -> Self: ...

    def invert(self, keep_keys=False, copy=False):
        """ Swap keys and values. Inverting {1: 2, 3: 4} returns {2: 1, 4: 3}.

        When 2+ keys are mapped to the same value, then that value will be \
        mapped either to a `keep_collisions_in` container of all of those \
        keys or (by default) to only the most recently-added key.

        :param keep_collisions_in: CollisionHandler, type of container to \
            map a value to when multiple keys were mapped to that value; \
            e.g. `list`, `tuple`, or `set`
        """
        # If we are NOT keeping all keys mapped to the same value, then
        # just keep whichever key was added most recently
        if not keep_keys:
            inverted = {v: k for k, v in self.items()}

        else:  # If we ARE keeping all keys mapped to the same value, then:
            inverted = defaultdict(list)  # Avoid conflating keys & values

            for key, value in self.items():  # Swap values with keys
                inverted[value].append(key)
        if copy:
            return self.__class__(inverted)
        else:
            self.clear()
            self.update(inverted)


class Subsetionary(Explictionary):

    @classmethod
    def from_subset_of(cls, from_map: Mapping, keys: Container[Hashable]
                       = set(), values: Container = set(), include_keys:
                       bool = False, include_values: bool = False) -> Self:
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
        return mapping.Subset(keys, values, include_keys, include_values
                              ).of(from_map, cls)

    def subset(self, keys: Container[Hashable] = set(),
               values: Container = set(), include_keys: bool = False,
               include_values: bool = False) -> Self:
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
        return mapping.Subset(keys, values, include_keys, include_values
                              ).of(self)


class Updationary(Explictionary):
    def __init__(self, from_map: FromMap = None, **kwargs) -> None:
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
                run_update(each_map)
        if copy:
            return updated


class Walktionary(Explictionary):
    def walk(self, only_yield_maps: bool = True) -> mapping.Walk:
        """ Recursively iterate over this dict and every dict inside it.

        :param only_yield_maps: bool, True for this iterator to return \
            key-value pairs only if the value is also a Mapping; else False \
            to return every item iterated over. Defaults to True.
        :return: mapping.Walk with `keys`, `values`, and `items` methods to \
            recursively iterate over this Walktionary.
        """
        return mapping.Walk(self, only_yield_maps)


class DotDict(Updationary, mapping.Traversible):
    """ dict with dot.notation item access. Compare `sklearn.utils.Bunch`.
        DotDict can get/set items as attributes: if `name` is not protected, \
        then `self.name is self["name"]`.

    Benefit: You can get/set items by using '.' or key names in brackets.
    Keeps most core functionality of the Python dict type.

    Adapted from answers to https://stackoverflow.com/questions/2352181 and \
    `attrdict` from https://stackoverflow.com/a/45354473 and `dotdict` from \
    https://github.com/dmtlvn/dotdict/blob/main/dotdict/dotdict.py
    """
    # Name of set[str] of attributes, methods, and other keywords that should
    # not be accessible/modifiable as keys/values/items
    PROTECTEDS = "__protected_keywords__"

    def __init__(self, from_map: FromMap = None, **kwargs: Any) -> None:
        """ 
        :param from_map: Mapping | Iterable[tuple[Hashable, Any]] | None, \
            Mapping to convert into a new instance of this class; `map` or \
            `iterable` in `dict.__init__` method; defaults to None.
        :param kwargs: Mapping[str, Any] of values to add to this DotDict.
        """
        # Fill this DotDict by initializing as an Updationary
        Updationary.__init__(self, from_map, **kwargs)

        # Initialize self as a Traversible for self.homogenize() method
        mapping.Traversible.__init__(self)

        # Prevent overwriting method/attributes or treating them like items
        dict.__setattr__(self, self.PROTECTEDS,
                         set(attributes.Of(self.__class__).method_names()
                             ).union({self.PROTECTEDS}))

    def __delattr__(self, name: str) -> None:
        """ Implement `delattr(self, name)`. Same as `del self[name]`.
            Deletes item (key-value pair) instead of attribute.

        :param name: str naming the item in self to delete.
        """
        _delattr = self.__delitem__ \
            if self._is_ready_to("delete", name, AttributeError) \
            else super(DotDict, self).__delattr__
        return _delattr(name)

    def __getattr__(self, name: str) -> Any:
        """ `__getattr__(self, name) == getattr(self, name) == self.<name>`
            If name is not protected, then `self.name is self["name"]`

        Effectively the same as `__getattr__ = dict.__getitem__` except that \
        `hasattr(self, <not in dict>)` works; it does not raise a `KeyError`.

        :param name: str naming the attribute/element of self to return.
        :raises AttributeError: if name is not an item or attribute of self.
        :return: Any, `getattr(self, name)` and/or `self[name]`
        """
        try:  # First, try to get an attribute (e.g. a method) of this object
            return dict.__getattribute__(self, name)
        except AttributeError as err:

            try:  # Next, get a value mapped to the key, if any
                return dict.__getitem__(self, name)

            # If neither exists, then raise AttributeError
            except KeyError:  # Don't raise KeyError; it breaks hasattr
                raise err from None  # Only show 1 exception in the traceback

    def __getstate__(self) -> Self:
        """ Required for pickling per https://stackoverflow.com/a/36968114 """
        return self

    def __setattr__(self, name: str, value: Any) -> None:
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

    def __setitem__(self, key: str, value: Any) -> None:
        """ Set self[key] to value. Explicitly defined to include \
            `_is_ready_to` check preventing user from overwriting \
            protected attributes/methods.

        :param key: str naming the key to map the value to
        :param value: Any, the value of the new item
        """
        self._is_ready_to("overwrite", key, KeyError)
        return super(DotDict, self).__setitem__(key, value)

    def __setstate__(self, state: Mapping) -> None:
        """ Required for pickling per https://stackoverflow.com/a/36968114

        :param state: Mapping, _description_
        """
        self.update(state)
        self.__dict__ = self

    def _is_ready_to(self, alter: str, attr_name: str, err_type:
                     type[BaseException]) -> bool:
        """ Check if an attribute of self is protected or if it's alterable

        :param alter: str, verb naming the alteration
        :param attribute_name: str, name of the attribute of self to alter
        :raises err_type: if the attribute is protected
        :return: bool, True if the attribute is not protected; \
                 else raise error
        """
        protecteds = getattr(self, self.PROTECTEDS, set())
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

    def get_subset_from_lookups(self, to_look_up: Mapping[str, str],
                                sep: str = ".", default: Any = None) -> Self:
        """ `self.get_subset_from_lookups({"a": "b/c"}, sep="/")` \
            -> `DotDict({"a": self.b.c})`

        :param to_look_up: Mapping[str, str] of every key to put in the \
            returned DotDict to the path to its value in this DotDict (self)
        :param sep: str, separator between subkeys in to_look_up.values(), \
            defaults to "."
        :param default: Any, value to use map to any keys not found in self; \
            defaults to None
        :return: self.__class__ mapping every key in to_look_up to the value \
            at its mapped path in self
        """
        return self.__class__({key: self.lookup(path, sep, default)
                               for key, path in to_look_up.items()})

    def homogenize(self, replace: type[dict] = dict) -> None:
        """ Recursively transform every dict contained inside this DotDict \
            into a DotDict itself, ensuring nested dot access to attributes.
            From https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param replace: type of element/child/attribute to change to DotDict.
        """
        cls = self.__class__
        for k, v in self.items():
            if self._will_now_traverse(v) and isinstance(v, replace):
                if not isinstance(v, cls):
                    self[k] = cls(v)
                self[k].homogenize()

    def lookup(self, path: str, sep: str = ".", default: Any = None) -> Any:
        """ Get the value mapped to a key in nested structure. Adapted from \
            https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param path: str, path to key in nested structure, e.g. "a.b.c"
        :param sep: str, separator between keys in path; defaults to "."
        :param default: Any, value to return if key is not found
        :return: Any, the value mapped to the nested key
        """
        keypath = list(reversed(path.split(sep)))
        retrieved = self
        try:
            while keypath:
                key = keypath.pop()
                try:
                    retrieved = retrieved[key]
                except KeyError:
                    retrieved = retrieved[int(key)]

        # If value is not found, then return the default value
        except DATA_ERRORS:
            pass
        return default if keypath else retrieved


class LazyDict(Updationary, Defaultionary):
    """ Dict that can get/set items and ignore the default parameter \
        until/unless it is needed, ONLY evaluating it after failing to \
        get/set an existing key. Benefit: The `default=` code does not \
        need to be valid (yet) if self already has the key. If you pass a \
        function to a "lazy" method, then that function only needs to work \
        if a value is missing.

    Keeps most core functionality of the Python `dict` type.
    Extended `LazyButHonestDict` from https://stackoverflow.com/q/17532929 """

    def lazyget(self, key: Hashable, get_if_absent: Callable = always_none,
                getter_args: Iterable = list(),
                getter_kwargs: Mapping = dict(),
                exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from `LazyButHonestDict.lazyget` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to \
            `key` in `self`) will not be returned; instead returning \
            `get_if_absent(*getter_args, **getter_kwargs)`
        """
        return get_if_absent(*getter_args, **getter_kwargs) if \
            self._will_getdefault(key, exclude) else self[key]

    def lazysetdefault(self, key: Hashable, get_if_absent:
                       Callable = always_none, getter_args: Iterable = list(),
                       getter_kwargs: Mapping = dict(),
                       exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from `LazyButHonestDict.lazysetdefault` from \
        https://stackoverflow.com/q/17532929

        :param key: Hashable to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: Container of possible values to replace with \
            `get_if_absent(*getter_args, **getter_kwargs)` and return if \
            they are mapped to `key` in `self`
        """
        if self._will_getdefault(key, exclude):
            self[key] = get_if_absent(*getter_args, **getter_kwargs)
        return self[key]


class Promptionary(LazyDict):
    """ LazyDict able to interactively prompt the user to fill missing values.
    """
    _Prompter = Callable[[str], str]  # Prompt function to use as lazy getter

    def get_or_prompt_for(self, key: Hashable, prompt: str,
                          prompt_fn: _Prompter = input,
                          exclude: Container = set()) -> Any:
        """ Return the value mapped to key in self if one already exists; \
            else prompt the user to interactively provide it and return that.

        :param key: str mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, prompt the user as if `key is not in self`.
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazyget(key, prompt_fn, [prompt], exclude=exclude)

    def setdefault_or_prompt_for(self, key: Hashable, prompt: str,
                                 prompt_fn: _Prompter = input,
                                 exclude: Container = set()) -> Any:
        """ Return the value mapped to key in self if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable that interactively prompts the user to \
                          get a string, like `input` or `getpass.getpass`.
        :param exclude: Container, values to ignore or overwrite. If `self` \
            maps `key` to one, prompt the user as if `key is not in self`.
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazysetdefault(key, prompt_fn, [prompt], exclude=exclude)


class Cryptionary(Promptionary, mapping.Bytesifier, Debuggable):
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

    def __repr__(self) -> str:
        """
        :return: str, string representation of Cryptionary including its \
            class name without decrypting the encrypted values first.
        """
        return f"{name_of(self)}({self.to_dict()})"

    def __setitem__(self, key: Hashable, value: Any) -> None:
        """ Set self[dict_key] to dict_value after encrypting dict_value.

        :param key: Hashable, key mapped to the value to retrieve.
        :param value: SupportsBytes, value to encrypt and store.
        """
        try:
            bytesified = self.try_bytesify(value)
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
            case dict():
                map_iters.append(from_map.items())
            case tuple():
                map_iters.append(from_map)
        for each_map_iter in map_iters:
            for k, v in each_map_iter:
                self[k] = v


class LazyDotDict(DotDict, LazyDict):
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


class DotPromptionary(DotDict, Promptionary):
    """ Promptionary with dot.notation item access. """


class SubCryptionary(Cryptionary, Subsetionary):
    """ Cryptionary with subset access/creation methods. """


class FancyDict(DotPromptionary, Invertionary, Subsetionary, Walktionary):
    """ Custom dict combining as much functionality from the other classes \
        defined in this file and in `maptools.py` as possible: lazy methods, \
        enhanced default/update methods, prompt methods, invert method, \
        to/from subset methods, walk method, and dot.notation item access. """
