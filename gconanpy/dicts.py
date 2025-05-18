#!/usr/bin/env python3

"""
Useful/convenient custom extensions of Python's dictionary class.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-05-17
"""
# Import standard libraries
from collections.abc import (Callable, Collection, Container,
                             Hashable, Iterable, Mapping)
from configparser import ConfigParser
from typing import Any, TypeVar

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from debug import Debuggable
    import dicts  # import self to define CustomDicts.CLASSES
    from extend import combine, module_classes_to_args_dict
    from maptools import Bytesifier, MapSubset, Traversible, WalkMap
    from metafunc import AttributesOf, DATA_ERRORS, name_of, rename_keys
    from trivial import always_none
except ModuleNotFoundError:
    from gconanpy.debug import Debuggable
    from gconanpy import dicts  # import self to define CustomDicts.CLASSES
    from gconanpy.extend import combine, module_classes_to_args_dict
    from gconanpy.maptools import Bytesifier, MapSubset, Traversible, WalkMap
    from gconanpy.metafunc import (AttributesOf, DATA_ERRORS,
                                   name_of, rename_keys)
    from gconanpy.trivial import always_none


class Explictionary(dict):
    """ Custom dict base class that explicitly includes its class name in \
        its string representation(s) via __repr__ method. """

    def __repr__(self) -> str:
        """
        :return: str, string representation of custom dict class including \
                 its class name: "Explictionary({...})"
        """
        return f"{name_of(self)}({dict.__repr__(self)})"

    def copy(self):
        """ `D.copy()` -> a shallow copy of `D`. Return another instance \
            of this same type of custom dictionary. """
        return self.__class__(self)


class Defaultionary(Explictionary):
    """ Custom dict class with extended functionality centered around the \
        `default=` option, functionality used by various other custom dicts. \
        The Defaultionary can ignore specified values as if they were blank \
        in its `get` method. It can also use `setdefault` on many different \
        elements at once via `setdefaults`. `LazyDict` base class.
    """

    def _will_getdefault(self, key: Hashable, exclude: Container = set()
                         ) -> bool:
        """
        :param key: Hashable
        :param exclude: Container of values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will return True as if `key is not in self`.
        :return: bool, True if `key` is not mapped to a value in `self` or \
            is mapped to something in `exclude`
        """
        return key not in self or self[key] in exclude

    def get(self, key: Hashable, default: Any = None,
            exclude: Container = set()) -> Any:
        """ Return the value mapped to `key` in `self`, if any; else return \
            `default`. Defined to add `exclude` option to `dict.get`.

        :param key: Hashable, key mapped to the value to return
        :param default: Any, object to return `if self.will_getdefault`, \
            i.e. `if key not in self or self[key] in exclude`
        :param exclude: Container of values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will return `default` as if `key is not in self`.
        :return: Any, value mapped to `key` in `self` if any, else `default`
        """
        return default if self._will_getdefault(key, exclude) else self[key]

    def setdefaults(self, exclude: Collection = set(), **kwargs: Any) -> None:
        """ Fill any missing values in self from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param exclude: Collection, values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key is not in self`.
        :param kwargs: Mapping[str, Any] of values to add to self if needed.
        """
        if exclude:
            example_exclude = next(iter(exclude))
            for key, value in kwargs.items():
                if self.get(key, example_exclude, exclude) is example_exclude:
                    self[key] = value
        else:
            for key, value in kwargs.items():
                self.setdefault(key, value)


class Invertionary(Explictionary):
    # Type variables for invert method
    _T = TypeVar("_T")
    CollisionHandler = Callable[[list[_T]], Iterable[_T]]

    def invert(self, keep_collisions_in: CollisionHandler | None = None,
               copy: bool = False):  # -> None | "Invertionary":
        """ Swap keys and values. `{1: 2, 3: 4}.invert()` -> `{2: 1, 4: 3}`.

        When 2+ keys are mapped to the same value, then that value will be \
        mapped either to a `keep_collisions_in` container of all of those \
        keys or (by default) to only the most recently-added key.

        :param keep_collisions_in: CollisionHandler, type of container to \
            map a value to when multiple keys were mapped to that value; \
            e.g. `list`, `tuple`, or `set`
        """
        # If we are NOT keeping all keys mapped to the same value, then
        # just keep whichever key was added most recently
        if keep_collisions_in is None:
            inverted = {v: k for k, v in self.items()}

        else:  # If we ARE keeping all keys mapped to the same value, then:
            inverted = dict()  # Avoid conflating keys & values
            collided = set()  # Keep track of which values collide

            # If values don't collide, just swap them with keys
            for key, value in self.items():
                if value not in inverted:
                    inverted[value] = key

                # If 2+ former values (now keys) collide, then map them to a
                # keep_collisions_in container holding all of the former keys
                else:
                    new_value = [*inverted[value], key] if value in collided \
                        else [inverted[value], key]
                    collided.add(value)
                    inverted[value] = keep_collisions_in(new_value)
        if copy:
            return self.__class__(inverted)
        else:
            self.clear()
            self.update(inverted)


class Subsetionary(Explictionary):

    @classmethod
    def from_subset_of(cls, from_map: Mapping, keys: Container[Hashable]
                       = set(), values: Container = set(), include_keys:
                       bool = False, include_values: bool = False):
        """ Convert a subset of `from_map` into a new `Subsetionary`.

        :param from_map: Mapping to create a new Subsetionary from a subset of.
        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True for `filter` to return a subset \
            with ONLY the provided `keys`; else False to return a subset \
            with NONE OF the provided `keys`.
        :param include_values: bool, True for `filter` to return a subset \
            with ONLY the provided `values`; else False to return a subset \
            with NONE OF the provided `values`.
        :return: Subsetionary including only the specified keys and values.       
        """
        return MapSubset(keys, values, include_keys, include_values
                         ).of(from_map, cls)

    def subset(self, keys: Container[Hashable] = set(),
               values: Container = set(), include_keys: bool = False,
               include_values: bool = False):
        """ Create a new `Subsetionary` including only a subset of this one.

        :param keys: Container[Hashable] of keys to (in/ex)clude.
        :param values: Container of values to (in/ex)clude.
        :param include_keys: bool, True for `filter` to return a subset \
            with ONLY the provided `keys`; else False to return a subset \
            with NONE OF the provided `keys`.
        :param include_values: bool, True for `filter` to return a subset \
            with ONLY the provided `values`; else False to return a subset \
            with NONE OF the provided `values`.
        :return: Subsetionary including only the specified keys and values.       
        """
        return MapSubset(keys, values, include_keys, include_values
                         ).of(self)


class Updationary(Explictionary):
    # Class type variable: `map`/`iterable` input arg in `dict.__init__`
    MapParts = TypeVar("MapParts", Mapping, Iterable[tuple[Hashable, Any]])

    def __init__(self, from_map: MapParts | None = None, **kwargs) -> None:
        """
        :param from_map: Mapping | Iterable[tuple[Hashable, Any]] | None, \
            Mapping to convert into a new instance of this class; `map` or \
            `iterable` in `dict.__init__` method; None by default to create \
            an empty dictionary (or create a dict from `kwargs` alone).
        :param kwargs: Mapping[str, Any] of values to add to this Updationary.
        """
        if from_map:
            self.update(from_map)
        self.update(kwargs)

    def copy_update(self, from_map: MapParts | None = None, **kwargs: Any
                    ) -> "Updationary":
        """
        :param from_map: Mapping | Iterable[tuple[Hashable, Any] ] | None, \
            `m` in `dict.update` method; defaults to None
        :param kwargs: Mapping, key-value pairs to include in returned copy.
        :return: Updationary, a copy of `self` with all key-value pairs \
            in `from_map` and in `kwargs`
        """
        copied = self.copy()
        copied.update(from_map, **kwargs)
        return copied

    def update(self, a_map: MapParts | None = None, **kwargs: Any) -> None:
        """ Add or overwrite items in this Mapping from other Mappings.

        :param a_map: Mapping | Iterable[tuple[Hashable, Any] ] | None, \
            `m` in `dict.update` method; defaults to None
        """
        run_update = super(Updationary, self).update
        run_update(**kwargs) if a_map is None else run_update(a_map, **kwargs)


class Walktionary(Explictionary):
    def walk(self) -> WalkMap:
        """ Recursively iterate over this dict and every dict inside it.

        :return: WalkMap with `keys`, `values`, and `items` methods to \
            recursively iterate over this FancyDict.
        """
        return WalkMap(self)


class DotDict(Updationary, Traversible):
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

    def __init__(self, from_map: Updationary.MapParts | None = None,
                 **kwargs: Any) -> None:
        """ 
        :param from_map: Mapping | Iterable[tuple[Hashable, Any]] | None, \
            Mapping to convert into a new instance of this class; `map` or \
            `iterable` in `dict.__init__` method; defaults to None.
        :param kwargs: Mapping[str, Any] of values to add to this DotDict.
        """
        # First, add all (non-item) custom methods and attributes
        super(DotDict, self).__init__(from_map, **kwargs)

        # Initialize self as a Traversible for self.homogenize() method
        self.traversed: set[int] = set()

        # Prevent overwriting method/attributes or treating them like items
        dict.__setattr__(self, self.PROTECTEDS,
                         set(AttributesOf(self.__class__).method_names()
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

    def __getstate__(self):
        """Required for pickling. From https://stackoverflow.com/a/36968114"""
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
        """ Required for pickling. From https://stackoverflow.com/a/36968114

        :param state: _type_, _description_
        """
        self.update(state)
        self.__dict__ = self

    def _is_ready_to(self, alter: str, attr_name: str, err_type:
                     type[BaseException] = AttributeError) -> bool:
        """ Check if an attribute of self is protected or if it's alterable

        :param alter: str, verb naming the alteration
        :param attribute_name: str, name of the attribute of self to alter
        :raises AttributeError: if the attribute is protected
        :return: bool, True if the attribute is not protected; \
                 else raise error
        """
        is_ready = False
        if hasattr(self, self.PROTECTEDS):
            if attr_name in getattr(self, self.PROTECTEDS):
                raise err_type(f"Cannot {alter} read-only "
                               f"'{name_of(self)}' object "
                               f"attribute '{attr_name}'")
            else:
                is_ready = True
        return is_ready

    @classmethod
    def fromConfigParser(cls, config: ConfigParser):
        """
        :param config: ConfigParser to convert into DotDict
        :return: DotDict with the key-value mapping structure of config
        """
        self = cls({section: {k: v for k, v in config.items(section)}
                    for section in config.sections()})
        self.homogenize()
        return self

    def get_subset_from_lookups(self, to_look_up: Mapping[str, str],
                                sep: str = ".", default: Any = None):
        """ `self.get_subset_from_lookups({"a": "b/c"}, sep="/")` \
            -> `DotDict({"a": self.b.c})`

        :param to_look_up: Mapping[str, str] of every key to put in the \
            returned DotDict to the path to its value in this DotDict (self)
        :param sep: str, separator between subkeys in to_look_up.values(), \
            defaults to "."
        :param default: Any, value to map to any keys not found in self; \
            defaults to None
        :return: self.__class__ mapping every key in to_look_up to the value \
            at its mapped path in self
        """
        return self.__class__({key: self.lookup(path, sep, default)
                               for key, path in to_look_up.items()})

    def homogenize(self, replace: type[dict] = dict):
        """ Recursively transform every dict contained inside this DotDict \
            into a DotDict itself, ensuring nested dot access to attributes.
            From https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param replace: type of element/child/attribute to change to DotDict.
        """
        for k, v in self.items():
            if self._will_traverse(v) and isinstance(v, replace):
                if not isinstance(v, self.__class__):
                    self[k] = self.__class__(v)
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
        return default if retrieved is self else retrieved


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
        & kwargs. Adapted from LazyButHonestDict.lazyget from \
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
        result. Adapted from LazyButHonestDict.lazysetdefault from \
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


class Promptionary(LazyDict):  # , Debuggable
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
        :param prompt_fn: Callable, function to interactively prompt the \
                          user to provide the value, such as `input` or \
                          `getpass.getpass`
        :param exclude: Container, True to return `prompt_fn(prompt)` if \
            key is mapped to None in self; else (by default) False to return \
            the mapped value instead
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazyget(key, prompt_fn, [prompt],
                            exclude=exclude)

    def setdefault_or_prompt_for(self, key: Hashable, prompt: str,
                                 prompt_fn: _Prompter = input,
                                 exclude: Container = set()) -> Any:
        """ Return the value mapped to key in self if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable, function to interactively prompt the \
                          user to provide the value, such as `input` or \
                          `getpass.getpass`
        :param exclude: Container, True to replace None mapped to key in \
            self with prompt_fn(prompt) and return that; else (by default) \
            False to return the mapped value instead
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazysetdefault(key, prompt_fn, [prompt],
                                   exclude=exclude)


class Cryptionary(Promptionary, Bytesifier, Debuggable):
    """ Extended Promptionary that automatically encrypts values before \
        storing them and automatically decrypts values before returning them.
        Created to store user credentials slightly more securely, and to \
        slightly reduce the likelihood of accidentally exposing them. """

    def __init__(self, from_map: Updationary.MapParts | None = None,
                 debugging: bool = False, **kwargs: Any):
        """ Create a new Cryptionary.

        :param from_map: MapParts to convert into a new Cryptionary.
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        """
        try:
            # Create encryption mechanism
            self.encrypted = set()
            self.cryptor = Fernet(Fernet.generate_key())

            # Define whether to raise any error(s) or pause and interact
            self.debugging = debugging

            # Encrypt every value in the input mapping(s)/dict(s)
            self.update(from_map, **kwargs)

        except TypeError as err:
            self.debug_or_raise(err, locals())

    def __delitem__(self, key: str) -> None:
        """ Delete self[key].

        :param key: str, key to delete and to delete the value of.
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
        return Explictionary({key: dict.__getitem__(self, key)
                              for key in self.keys()}).__repr__()

    def __setitem__(self, key: str, value: Any) -> None:
        """ Set self[dict_key] to dict_value after encrypting dict_value.

        :param key: str, key mapped to the value to retrieve.
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

    def update(self, from_map: Updationary.MapParts | None = None,
               **kwargs: Any) -> None:
        """ Add or overwrite items in this Mapping from other Mappings.

        :param from_map: Mapping | Iterable[tuple[Hashable, Any] ] | None, \
            `m` in `dict.update` method; defaults to None
        """
        for each_map in from_map, kwargs:
            if each_map:
                for k, v in dict(each_map).items():
                    self[k] = v


class CustomDicts:
    CLASSES: dict[str, type] = rename_keys(module_classes_to_args_dict(
        dicts, "Dict", "ionary", ignore={Explictionary}),
        walkt="walk", crypt="encrypt", updat="update")

    @classmethod
    def new(cls, class_name: str, from_map: Updationary.MapParts = None,
            features: Iterable[str] = list(), **kwargs: Any
            ) -> Explictionary:
        """
        :param class_name: str naming the new custom dictionary class.
        :param from_map: MapParts to convert into a new custom dict.
        :param features: Iterable[str] listing the features (methods and \
            attributes) to add to the returned custom dictionary class. All \
            acceptable `features` options are keys in `CustomDicts.CLASSES`.
        :return: Explictionary, dict of a new custom class.
        """
        CustomDict = cls.new_class(class_name, *features)
        return CustomDict(from_map, **kwargs)

    @classmethod
    def new_class(cls, name: str, *features: str) -> type[Explictionary]:
        """ Create a custom dictionary class by combining others in this file.

        :param name: str naming the new custom dictionary class.
        :param features: Iterable[str] listing the features (methods and \
            attributes) to add to the returned custom dictionary class. All \
            allowed features are in `CustomDicts.CLASSES`, which maps each \
            feature's name to the class with those features. The returned \
            custom dict class will be a subclass of every class mapped to \
            the indicated features.
        :raises ValueError: if any of the provided features are not included \
            in `CustomDicts.CLASSES`.
        :return: type[Explictionary], new custom dictionary class with the \
            specified `features`.
        """
        parents = list()
        for feature in features:
            if feature in cls.CLASSES:
                parents.append(cls.CLASSES[feature])
            else:
                raise ValueError(f"'{feature}' is not a possible feature "
                                 f"of a {name_of(cls)}")
        return combine(name, parents)
