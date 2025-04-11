#!/usr/bin/env python3

"""
Useful/convenient custom extensions of Python's dictionary class.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-04-09
"""
# Import standard libraries
from collections.abc import Callable, Hashable, Iterable, Mapping
from configparser import ConfigParser
import pdb
import sys
from typing import Any, SupportsBytes, TypeVar

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from debug import Debuggable
    from metafunc import KeepTryingUntilNoErrors, nameof
    from trivial import noop
except ModuleNotFoundError:
    from gconanpy.debug import Debuggable
    from gconanpy.metafunc import KeepTryingUntilNoErrors, nameof
    from gconanpy.trivial import noop


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


class Invertionary(Explictionary):
    _T = TypeVar("_T")
    CollisionHandler = Callable[[list[_T]], Iterable[_T]]

    def invert(self, keep_collisions_in: CollisionHandler | None = None) -> None:
        """ Swap keys and values. `{1: 2, 3: 4}.invert()` -> `{2: 1, 4: 3}`.

        When 2+ keys are mapped to the same value, then that value will be \
        mapped either to a `keep_collisions_in` container of all of those \
        keys or (by default) to only the most recently-added key.

        :param keep_collisions_in: CollisionHandler, type of container to \
            map a value to when multiple keys were mapped to that value; \
            e.g. `list`, `tuple`, or `set`
        """
        # Predefine to avoid RuntimeError(changed size during iteration)
        keys = [k for k in self.keys()]

        # If we are NOT keeping all keys mapped to the same value, then
        # just keep whichever key was added most recently
        if keep_collisions_in is None:
            for key in keys:
                self[self.pop(key)] = key

        # If we ARE keeping all keys mapped to the same value, then:
        else:  # Make new empty dict to avoid conflating keys & values
            inverted = self.__class__()
            collided = set()  # Keep track of which values collide

            # Remove every key-value pairing, swap them, and put into new dict
            for key in keys:
                value = self.pop(key)
                if value not in inverted:
                    inverted[value] = key

                # If 2+ former values (now keys) collide, then map them to a
                # keep_collisions_in container holding all of the former keys
                else:
                    if value in collided:
                        new_value = [*inverted[value], key]
                    else:
                        new_value = [inverted[value], key]
                        collided.add(value)
                    inverted[value] = keep_collisions_in(new_value)

            # Remove all old k-v pairs and replace them with new v-k pairs
            self.clear()
            self.update(inverted)


class Defaultionary(Invertionary):

    @classmethod
    def from_subset_of(cls, a_map: Mapping, *keys_to_keep: Hashable,
                       exclude_empties: bool = False):
        # No return type hint so VSCode can infer making subclass instances
        """ Construct an instance of this class by picking a subset of \
            key-value pairs to keep.

        :param a_map: Mapping to build an Defaultionary from a subset of.
        :param keys_to_keep: Iterable[Hashable] of a_map keys to copy into \
            the returned Defaultionary with their values.
        :param exclude_empties: bool, True to exclude keys mapped to None in \
            a_map from the returned Defaultionary, otherwise (by default) \
            False to include them.
        :return: Defaultionary mapping keys_to_keep to their a_map values.
        """
        return cls({k: a_map[k] for k in keys_to_keep if a_map[k] is not None}
                   if exclude_empties else {k: a_map[k] for k in keys_to_keep})

    def setdefaults(self, exclude_empties: bool = False, **kwargs: Any) -> None:
        """ Fill any missing values in self from kwargs.
            dict.update prefers to overwrite old values with new ones.
            setdefaults is basically dict.update that prefers to keep old values.

        :param exclude_empties: bool, False to exclude keys mapped to None \
            in a_map from the returned Defaultionary, otherwise (by default) \
            False to include them.
        :param kwargs: Mapping[str, Any] of values to add to self if needed
        """
        if exclude_empties:
            for key, value in kwargs.items():
                if self.get(key, None) is None:
                    self[key] = value
        else:
            for key, value in kwargs.items():
                self.setdefault(key, value)


class LazyDict(Defaultionary):
    """ Dict that can get/set items and ignore the default parameter \
    until/unless it is needed, ONLY evaluating it after failing to get/set \
    an existing key. Benefit: The `default=` code does not need to be valid \
    (yet) if self already has the key. If you pass a function to a "lazy" \
    method, then that function only needs to work if a value is missing.
    Keeps most core functionality of the Python dict type.
    Extended LazyButHonestDict from https://stackoverflow.com/q/17532929 """

    def get(self, key: str, default: Any = None,
            exclude_empties: bool = False) -> Any:
        """ Return the value mapped to key in this LazyDict, if any; else \
            return default. Explicitly defined to add exclude_empties option \
            to `dict.get`.

        :param key: str, key mapped to the value to return
        :param default: Any, object to return if key is not in the Cryptionary
        :param exclude_empties: bool, True to return default if key is \
            mapped to None in self; else (by default) False to return \
            mapped value instead
        :return: Any, (decrypted) value mapped to key in this Cryptionary if \
            any, else default
        """
        return default if self.will_getdefault(key, exclude_empties) \
            else self[key]

    def lazyget(self, key: str, get_if_absent: Callable = noop,
                getter_args: Iterable = list(),
                getter_kwargs: Mapping = dict(),
                exclude_empties: bool = False) -> Any:
        """ Return the value for key if key is in the dictionary, else \
        return the result of calling the `get_if_absent` parameter with args \
        & kwargs. Adapted from LazyButHonestDict.lazyget from \
        https://stackoverflow.com/q/17532929

        :param key: str to use as a dict key to map to value
        :param get_if_absent: function that returns the default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude_empties: bool, True to return \
            get_if_absent(*getter_args, **getter_kwargs) if key is mapped to \
            None in self; else (by default) False to return mapped value
        """
        return get_if_absent(*getter_args, **getter_kwargs) if \
            self.will_getdefault(key, exclude_empties) else self[key]

    def lazysetdefault(self, key: str, get_if_absent: Callable = noop,
                       getter_args: Iterable = list(),
                       getter_kwargs: Mapping = dict(),
                       exclude_empties: bool = False) -> Any:
        """ Return the value for key if key is in the dictionary; else add \
        that key to the dictionary, set its value to the result of calling \
        the `get_if_absent` parameter with args & kwargs, then return that \
        result. Adapted from LazyButHonestDict.lazysetdefault from \
        https://stackoverflow.com/q/17532929

        :param key: str to use as a dict key to map to value
        :param get_if_absent: Callable, function to set & return default value
        :param getter_args: Iterable[Any] of get_if_absent arguments
        :param getter_kwargs: Mapping[Any] of get_if_absent keyword arguments
        :param exclude_empties: bool, True to replace None mapped to key in \
            self with get_if_absent(*getter_args, **getter_kwargs) and \
            return that; else (by default) False to return the mapped value
        """
        if self.will_getdefault(key, exclude_empties):
            self[key] = get_if_absent(*getter_args, **getter_kwargs)
        return self[key]

    def will_getdefault(self, key: Any, exclude_empties: bool = False
                        ) -> bool:
        """
        :param key: Any
        :param exclude_empties: bool, what to return if key is None.
        :return: bool, True if key is "empty" (not mapped to a value in \
            self, or mapped to None if exclude_empties)
        """
        return ((self.get(key, None) is None) if exclude_empties else
                (key not in self))


class DotDict(Defaultionary):
    """ dict with dot.notation item access. Compare `sklearn.utils.Bunch`.
        DotDict can get/set items as attributes: `self.item is self['item']`.
        Benefit: You can get/set items by using '.' or key names in brackets.
        Keeps most core functionality of the Python dict type.

    Adapted from answers to https://stackoverflow.com/questions/2352181 and\
    attrdict from https://stackoverflow.com/a/45354473 and dotdict from\
    https://github.com/dmtlvn/dotdict/blob/main/dotdict/dotdict.py
    """
    # Enable tab-completion of dotdict items. From
    # https://stackoverflow.com/questions/2352181#comment114004924_23689767
    __dir__ = dict.keys

    # Name of set[str] of attributes, methods, and other keywords that should
    # not be accessible/modifiable as keys/values/items
    PROTECTEDS = "__protected_keywords__"

    def __init__(self, *args, **kwargs):
        # First, add all (non-item) custom methods and attributes
        super().__init__(*args, **kwargs)

        # Prevent overwriting method/attributes or treating them like items
        dict.__setattr__(self, self.PROTECTEDS, set(dir(__class__)))

    def __delattr__(self, name: str) -> None:
        """ Implement `delattr(self, name)`.
            Deletes item (key-value pair) or attribute.

        :param name: str naming the attribute of self to delete.
        """
        if self._is_ready_to("delete", name):
            self.__delitem__(name)
        else:
            dict.__delattr__(self, name)

    def __getattr__(self, name: str) -> Any:
        """ `__getattr__(self, name) == getattr(self, name) == self.<name>`
            If name is not protected, then `self.name == self["name"]`

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
        """ Implement `setattr(self, name, value)` and/or `self[name] = value`

        :param name: str naming the attribute/key to map the value to
        :param value: Any, the value of the new attribute/item
        """
        if self._is_ready_to("overwrite", name):
            self.__setitem__(name, value)
        else:
            dict.__setattr__(self, name, value)

    def __setitem__(self, key: str, value: Any) -> None:
        """ Set self[key] to value. Explicitly defined to include \
            `_is_ready_to` check preventing user from overwriting protected \
            attributes/methods.

        :param key: str naming the key to map the value to
        :param value: Any, the value of the new item
        """
        if self._is_ready_to("overwrite", key):
            super().__setitem__(key, value)
        else:  # TODO Are these `__setitem__`s meaningfully different?
            dict.__setitem__(self, key, value)

    def __setstate__(self, state):
        """ Required for pickling. From https://stackoverflow.com/a/36968114

        :param state: _type_, _description_
        """
        self.update(state)
        self.__dict__ = self

    def _is_ready_to(self, alter: str, attribute_name: str) -> bool:
        """ Check if a given attribute of self is protected, if it's \
            alterable, or if self is still being initialized.

        :param alter: str, verb naming the alteration
        :param attribute_name: str, name of the attribute of self to alter
        :raises AttributeError: if the attribute is protected
        :return: bool, True if the attribute is not protected; \
                 False if self is still being initialized; else raise error
        """
        is_protected = False
        try:
            is_protected = attribute_name in \
                dict.__getattribute__(self, self.PROTECTEDS)
        except AttributeError:  # Still initializing self => not ready yet
            is_ready = False
        if is_protected:  # Attribute is protected => can't alter; raise error
            raise AttributeError(f"Cannot {alter} read-only "
                                 f"'{nameof(self)}' object "
                                 f"attribute '{attribute_name}'")
        else:  # Attribute is not protected => it is ready to alter
            is_ready = True
        return is_ready

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


class Configtionary(DotDict):  # TODO Just put the method in DotDict?
    @classmethod
    def from_configparser(cls, config: ConfigParser):
        """
        :param config: ConfigParser to convert into Configtionary
        :return: Configtionary with the key-value mapping structure of config
        """
        self = cls({section: {k: v for k, v in config.items(section)}
                    for section in config.sections()})
        self.homogenize()
        return self


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
    ...


class Promptionary(LazyDict, Debuggable):
    """ LazyDict able to interactively prompt the user to fill missing values.
    """

    def __init__(self, *args, debugging: bool = False, **kwargs: Any) -> None:
        """ Initialize Promptionary from existing Mapping (*args) or from \
            new Mapping (**kwargs).

        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        """
        # This class can pause and debug when an exception occurs
        self.debugging = debugging
        super().__init__(*args, **kwargs)

    def get_or_prompt_for(self, key: str, prompt: str,
                          prompt_fn: Callable = input,
                          exclude_empties: bool = False) -> Any:
        """ Return the value mapped to key in self if one already exists; \
            else prompt the user to interactively provide it and return that.

        :param key: str mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable, function to interactively prompt the \
                          user to provide the value, such as `input` or \
                          `getpass.getpass`
        :param exclude_empties: bool, True to return `prompt_fn(prompt)` if \
            key is mapped to None in self; else (by default) False to return \
            the mapped value instead
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazyget(key, prompt_fn, [prompt],
                            exclude_empties=exclude_empties)

    def setdefault_or_prompt_for(self, key: str, prompt: str,
                                 prompt_fn: Callable = input,
                                 exclude_empties: bool = False) -> Any:
        """ Return the value mapped to key in self if one already exists; \
            otherwise prompt the user to interactively provide it, store the \
            provided value by mapping it to key, and return that value.

        :param key: str mapped to the value to retrieve
        :param prompt: str to display when prompting the user.
        :param prompt_fn: Callable, function to interactively prompt the \
                          user to provide the value, such as `input` or \
                          `getpass.getpass`
        :param exclude_empties: bool, True to replace None mapped to key in \
            self with prompt_fn(prompt) and return that; else (by default) \
            False to return the mapped value instead
        :return: Any, the value mapped to key if one exists, else the value \
                 that the user interactively provided
        """
        return self.lazysetdefault(key, prompt_fn, [prompt],
                                   exclude_empties=exclude_empties)


class Bytesifier(Debuggable):
    """ Class with a method to convert objects into bytes without knowing \
        what type those things are. """
    DEFAULTS = dict(encoding=sys.getdefaultencoding(), length=1,
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
        errs = None
        defaults = Defaultionary(kwargs)
        defaults.setdefaults(**self.DEFAULTS)
        encoding = defaults.pop("encoding")
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
        try:
            return bytesified
        except NameError:
            self.debug_or_raise(errs[-1], locals())


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

            # This class can pause and debug when an exception occurs
            super().__init__(debugging=debugging)

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
