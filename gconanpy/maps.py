#!/usr/bin/env python3

"""
Useful/convenient custom extensions of Python's dictionary class.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-04-29
"""
# Import standard libraries
from collections.abc import Callable, Container, Hashable, Iterable, Mapping
from configparser import ConfigParser
import sys
from typing import Any, SupportsBytes, TypeVar

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from debug import Debuggable
    from metafunc import AttributesOf, KeepTryingUntilNoErrors, nameof
    from trivial import always_none
except ModuleNotFoundError:
    from gconanpy.debug import Debuggable
    from gconanpy.metafunc import AttributesOf, KeepTryingUntilNoErrors, \
        nameof
    from gconanpy.trivial import always_none


class MapSubset:
    """ Filter object that can take a specific subset from any Mapping. """
    _M = TypeVar("_M", bound=Mapping)  # Type of Mapping to get subset(s) of
    _T = TypeVar("_T", bound=Mapping)  # Type of Mapping to return

    # Function that takes a key-value pair and returns True to include it
    # in the returned Mapping subset or False to exclude it; type(self.filter)
    Filter = Callable[[Hashable, Any], bool]

    def __init__(self, keys: Container[Hashable] = set(),
                 values: Container = set(), include_keys: bool = False,
                 include_values: bool = False) -> None:
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

        @staticmethod
        def passes_filter(k: Hashable, v: Any) -> bool:
            result = (k in keys) is include_keys
            try:
                return result and (v in values) is include_values

            # If v isn't Hashable and values can only contain Hashables,
            except TypeError:  # then v cannot be in values
                return result and not include_values

        self.filter = passes_filter

    def of(self, from_map: _M, as_type: type[_T] | None = None) -> _M | _T:
        """ Construct an instance of this class by picking a subset of \
            key-value pairs to keep.

        :param from_map: Mapping to return a subset of.
        :param as_type: type[Mapping], type of Mapping to return; or None to \
            return the same type of Mapping as `from_map`.
        :return: Mapping, `from_map` subset including only the specified \
            keys and values
        """
        if as_type is None:
            as_type = type(from_map)
        return as_type({k: v for k, v in from_map.items()
                        if self.filter(k, v)})


class Explictionary(dict):
    """ Custom dict base class that explicitly includes its class name in \
        its string representation(s) via __repr__ method. """

    def __repr__(self) -> str:
        """
        :return: str, string representation of custom dict class including\
                 its class name: "CustomDict({...})"
        """
        return f"{nameof(self)}({dict.__repr__(self)})"

    def copy(self):
        """ `D.copy()` -> a shallow copy of `D`. Return another instance \
            of this same type of custom dictionary. """
        return self.__class__(self)


class Defaultionary(Explictionary):

    def _will_getdefault(self, key: Any, exclude: Container = set()
                         ) -> bool:
        """
        :param key: Any
        :param exclude: Container of values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will return True as if `key is not in self`.
        :return: bool, True if `key` is not mapped to a value in `self` or \
            is mapped to something in `exclude`
        """
        return key not in self or self[key] in exclude

    def get(self, key: str, default: Any = None, exclude: Container = set()
            ) -> Any:
        """ Return the value mapped to `key` in `self`, if any; else return \
            `default`. Defined to add `exclude` option to `dict.get`.

        :param key: str, key mapped to the value to return
        :param default: Any, object to return `if self.will_getdefault`, \
            i.e. `if key not in self or self[key] in exclude`
        :param exclude: Container of values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will return `default` as if `key is not in self`.
        :return: Any, value mapped to `key` in `self` if any, else `default`
        """
        return default if self._will_getdefault(key, exclude) else self[key]

    def setdefaults(self, exclude: Iterable = set(), **kwargs: Any) -> None:
        """ Fill any missing values in self from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param exclude: Iterable, values to overlook/ignore such that if \
            `self` maps `key` to one of those values, then this function \
            will try to overwrite that value with a value mapped to the \
            same key in `kwargs`, as if `key is not in self`.
        :param kwargs: Mapping[str, Any] of values to add to self if needed
        """
        if exclude:
            example_exclude = next(iter(exclude))
            for key, value in kwargs.items():
                if self.get(key, example_exclude, exclude) is example_exclude:
                    self[key] = value
        else:
            for key, value in kwargs.items():
                self.setdefault(key, value)

    def update(self, a_map: Mapping | Iterable[tuple[Hashable, Any]
                                               ] | None = None,
               copy: bool = False, **kwargs: Any):
        # No return type hint so VSCode can infer subclass instances' types
        """ Add or overwrite items in this Mapping from other Mappings.

        :param a_map: Mapping | Iterable[tuple[Hashable, Any] ] | None, \
            `m` in `dict.update` method; defaults to None
        :param copy: bool, True to return a copy of `self` including all \
            items in `a_map` and in `kwargs`; else False to return None
        :return: Defaultionary updated with all values from `a_map` and \
            `kwargs` if `copy=True`; else None
        """
        updated = self.copy() if copy else self
        run_update = super(Defaultionary, updated).update
        run_update(**kwargs) if a_map is None else run_update(a_map, **kwargs)
        if copy:
            return updated


class Invertionary(Defaultionary):
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


class DotDict(Defaultionary):
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

    def __init__(self, *args, **kwargs):
        # First, add all (non-item) custom methods and attributes
        super().__init__(*args, **kwargs)

        # Prevent overwriting method/attributes or treating them like items
        dict.__setattr__(self, self.PROTECTEDS,  # set(dir(self.__class__)))
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
                               f"'{nameof(self)}' object "
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

    def homogenize(self, replace: type = dict):
        """ Recursively transform every dict contained inside this DotDict \
            into a DotDict itself, ensuring nested dot access to attributes.
            From https://gist.github.com/miku/dc6d06ed894bc23dfd5a364b7def5ed8

        :param replace: type of element/child/attribute to change to DotDict.
        """
        for k, v in self.items():
            if isinstance(v, replace) and not isinstance(v, self.__class__):
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
        except (KeyError, TypeError, ValueError):
            pass
        return default if retrieved is self else retrieved


class LazyDict(Defaultionary):
    """ Dict that can get/set items and ignore the default parameter \
    until/unless it is needed, ONLY evaluating it after failing to get/set \
    an existing key. Benefit: The `default=` code does not need to be valid \
    (yet) if self already has the key. If you pass a function to a "lazy" \
    method, then that function only needs to work if a value is missing.
    Keeps most core functionality of the Python `dict` type.
    Extended `LazyButHonestDict` from https://stackoverflow.com/q/17532929 """

    def lazyget(self, key: str, get_if_absent: Callable = always_none,
                getter_args: Iterable = list(),
                getter_kwargs: Mapping = dict(),
                exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from LazyButHonestDict.lazyget from \
        https://stackoverflow.com/q/17532929

        :param key: str to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude: set of possible values which (if they are mapped to \
            `key` in `self`) will not be returned; instead returning \
            `get_if_absent(*getter_args, **getter_kwargs)`
        """
        return get_if_absent(*getter_args, **getter_kwargs) if \
            self._will_getdefault(key, exclude) else self[key]

    def lazysetdefault(self, key: str, get_if_absent: Callable = always_none,
                       getter_args: Iterable = list(),
                       getter_kwargs: Mapping = dict(),
                       exclude: Container = set()) -> Any:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from LazyButHonestDict.lazysetdefault from \
        https://stackoverflow.com/q/17532929

        :param key: str to use as a dict key to map to value
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


class LazyDotDict(DotDict, LazyDict):
    """ LazyDict with dot.notation item access. It can get/set items...

    ...as object-attributes: `self.item is self['item']`. Benefit: You can \
       get/set items by using '.' or by using variable names in brackets.

    ...and ignore the `default=` code until it's needed, ONLY evaluating it \
       after failing to get/set an existing key. Benefit: The `default=` \
       code does not need to be valid (yet) if self already has the key.

    Adapted from answers to https://stackoverflow.com/questions/2352181 and \
    attrdict from https://stackoverflow.com/a/45354473 and dotdict from\
    https://github.com/dmtlvn/dotdict/blob/main/dotdict/dotdict.py and then\
    combined with LazyButHonestDict from https://stackoverflow.com/q/17532929

    Keeps most core functionality of the Python dict type. """


class Promptionary(LazyDict, Debuggable):
    """ LazyDict able to interactively prompt the user to fill missing values.
    """

    def __init__(self, from_map: Mapping, debugging: bool = False,
                 **kwargs: Any) -> None:
        """ Initialize Promptionary from existing Mapping (from_map) or from \
            new Mapping (**kwargs).

        :param from_map: Mapping to convert into Promptionary.
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        :param kwargs: Mapping[str, Any] of key-value pairs to add to this \
            Promptionary.
        """
        # This class can pause and debug when an exception occurs
        self.debugging = debugging
        super().__init__(from_map, **kwargs)

    def get_or_prompt_for(self, key: str, prompt: str,
                          prompt_fn: Callable = input,
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

    def setdefault_or_prompt_for(self, key: str, prompt: str,
                                 prompt_fn: Callable = input,
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


class Bytesifier(Debuggable):
    """ Class with a method to convert objects into bytes without knowing \
        what type those things are. """
    DEFAULTS = Defaultionary(encoding=sys.getdefaultencoding(), length=1,
                             byteorder="big", signed=False)

    @staticmethod
    def can_bytesify(an_object: Any) -> bool:
        """
        :return: bool, True if self.bytesify(an_object) will work, else \
                       False if it will raise an exception
        """  # TODO No, just use try: self.bytesify(an_object) ?
        return isinstance(an_object, bytes) or hasattr(an_object, "encode") \
            or hasattr(an_object, "to_bytes")

    def bytesify(self, an_obj: SupportsBytes, **kwargs) -> bytes:
        """
        :param an_obj: SupportsBytes, something to convert to bytes
        :raises AttributeError: if an_obj has no 'to_bytes' or 'encode' method
        :return: bytes, an_obj converted to bytes
        """
        # Get default values for encoder methods' input options
        defaults = self.DEFAULTS.update(kwargs, copy=True)
        encoding = defaults.pop("encoding")

        # Define these outside the context manager to preserve them afterwards
        bytesified = None
        errs = None

        with KeepTryingUntilNoErrors(TypeError) as next_try:
            with next_try():
                bytesified = str.encode(an_obj, encoding=encoding)
            with next_try():
                bytesified = int.to_bytes(an_obj, **defaults)
            with next_try():
                bytes.decode(an_obj, encoding=encoding)
                bytesified = an_obj
            with next_try():
                errs = next_try.errors
        if bytesified is None:
            self.debug_or_raise(errs[-1], locals())
        else:
            return bytesified


class Cryptionary(Promptionary, Bytesifier):
    """ Extended Promptionary that automatically encrypts values before \
        storing them and automatically decrypts values before returning them.
        Created to store user credentials slightly more securely, and to \
        slightly reduce the likelihood of accidentally exposing them. """

    def __init__(self, from_map: Mapping = dict(),
                 debugging: bool = False, **kwargs):
        try:
            # Create encryption mechanism
            self.encrypted = set()
            self.cryptor = Fernet(Fernet.generate_key())

            super(Cryptionary, self).__init__(
                from_map=from_map, debugging=debugging, **kwargs)

            # Encrypt every value in the input mapping(s)/dict(s)
            for prev_mapping in from_map, kwargs:
                for k, v in prev_mapping.items():
                    self[k] = v

        except TypeError as e:
            self.debug_or_raise(e, locals())

    def __delitem__(self, key: str) -> None:
        """ Delete self[key].

        :param key: str, key to delete and to delete the value of.
        """
        self.encrypted.discard(key)
        del self[key]

    def __getitem__(self, dict_key: Hashable) -> Any:
        """ `x.__getitem__(y)` <==> `x[y]`
        Explicitly defined to automatically decrypt encrypted values.

        :param dict_key: Hashable, key mapped to the value to retrieve
        :return: Any, the decrypted value mapped to dict_key
        """
        try:
            retrieved = dict.__getitem__(self, dict_key)
            if dict_key in self.encrypted and retrieved is not None:
                retrieved = self.cryptor.decrypt(retrieved).decode("utf-8")
            return retrieved
        except (KeyError, TypeError) as e:
            self.debug_or_raise(e, locals())

    def __setitem__(self, dict_key: str, dict_value: SupportsBytes) -> None:
        """ Set self[dict_key] to dict_value after encrypting dict_value.

        :param dict_key: str, key mapped to the value to retrieve.
        :param dict_value: SupportsBytes, value to encrypt and store.
        """
        try:
            if self.can_bytesify(dict_value):
                dict_value = self.cryptor.encrypt(self.bytesify(dict_value))
                self.encrypted.add(dict_key)
            return super(Cryptionary, self).__setitem__(dict_key, dict_value)
        except AttributeError as err:
            self.debug_or_raise(err, locals())
