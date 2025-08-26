#!/usr/bin/env python3

"""
Custom multidimensional dictionaries extending dicts.py classes.
Greg Conan: gregmconan@gmail.com
Created: 2025-08-23
Updated: 2025-08-25
"""
# Import standard libraries
from collections.abc import Hashable, Iterable, Mapping, Sequence
import random
import string
from typing import cast, overload, TypeVar
from typing_extensions import Self

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

# Import local custom libraries
try:
    from bytesify import Bytesifiable, Bytesifier, \
        DEFAULT_ENCODING
    from debug import Debuggable
    from iters import Randoms
    from mapping.dicts import Cryptionary, Explictionary, \
        Invertionary, MapParts
    from meta.typeshed import SupportsItemAccess
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from gconanpy.bytesify import Bytesifiable, Bytesifier, \
        DEFAULT_ENCODING
    from gconanpy.debug import Debuggable
    from gconanpy.iters import Randoms
    from gconanpy.mapping.dicts import Cryptionary, Explictionary, \
        Invertionary, MapParts

# Type variable for .__init__(...) and .update(...) method input parameters
FromMap = TypeVar("FromMap", Mapping, MapParts, None)


class NameDimension:  # for HashGrid
    def __init__(self) -> None:
        self.names = ("x", "y", "z", *string.ascii_lowercase[:-3])
        self.ix = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> str:
        try:
            to_return = self.names[self.ix]
        except IndexError:
            nextlen = self.ix // 26
            to_return = "".join(random.choices(
                string.ascii_lowercase, k=nextlen))
        self.ix += 1
        return to_return


class HashGrid[KT: Hashable, VT](Explictionary[int, VT]):
    """ `dict` mapping combinations of keys to specific values.

    Called a "Grid" because it maps 1 group of multiple keys to 1 value in \
    the same way that a grid maps 1 set of multiple dimensional coordinates \
    to 1 point. Each `HashGrid` has a specific number of dimensions; i.e., \
    a certain number of keys that must be provided together in the correct \
    order to access or modify the corresponding items.

    `HashGrid` does not know its own `keys`, so calling the `.keys()` \
    method on a `HashGrid` will return hash `int`s instead of anything \
    meaningful. This may have cryptographic use.

    For example, calling `creds = HashGrid.for_creds()` (equivalent to \
    `creds = HashGrid(dim_names=("username", "password"))`) creates a \
    `HashGrid` with two dimensions ("username" and "password"). It lets only \
    a user with the correct "username" and "password" credentials access the \
    value mapped to them, but no one else.

    After calling `creds["myuser", "mypass"] = "myvalue"` to add a value for \
    the given user, `creds` will not store (or otherwise be able to produce) \
    the values "myuser" or "mypass" even though a user could get or alter \
    "myvalue" by accessing `creds["myuser", "mypass"]`.
    """
    _D = TypeVar("_D")  # Type hint for "default" parameter

    @overload
    def __init__(self, *pairs: tuple[Iterable[KT], VT]) -> None: ...

    @overload
    def __init__(self, *pairs: tuple[Iterable[KT], VT],
                 dim_names: Sequence[str]) -> None: ...

    @overload
    def __init__(self, *, values: Sequence[VT],
                 **dimensions: Iterable[KT]) -> None: ...

    @overload
    def __init__(self, *, dim_names: Sequence[str], values: Sequence[VT],
                 **dimensions: Iterable[KT]) -> None: ...

    def __init__(self, *pairs, dim_names=tuple(), values=tuple(), **dimensions
                 ) -> None:
        """ Mapping of an arbitrary number of dimensions to specific values.

        `hg = HashGrid(([1,2,3], "foo"), ([7,8,9], "bar"))` is the same as \
        `hg = HashGrid(values=["foo", "bar"], x=[1, 7], y=[2, 8], z=[3, 9])` \
        and both mean that `hg[1, 2, 3] == "foo"` and `hg[7, 8, 9] == "bar"`.

        Initialize with either `pairs` or `values`, not both.

        :param pairs: tuple[Iterable[KT], VT], a tuple of 2 items: the keys, \
            and the value to assign to the combination of those keys.
        :param dim_names: Iterable[str] naming each dimension/coordinate in \
            this HashGrid. By default, the the dimensions are named in this \
            order: "x", "y", "z", the rest of the lowercase letters in \
            alphabetical order, & then random lowercase letter \
            combinations of increasing length.
        :param values: Iterable[VT], values to assign to the provided \
            dimensions in order. Include `values` and `dimensions` to create \
            a `HashGrid` where each value in `values` is mapped to the key \
            (coordinate) at the same index in each of the `dimensions`.
        :param dimensions: Mapping[str, Sequence[KT]] of each dimension's \
            name to the coordinate of each element of `values` in/along that \
            dimension. `HashGrid(values=[1,2], x=[3, 4], y=[5, 6])`, for \
            example, maps the coordinate (x=3, y=5) to the value 1 and maps \
            the coordinate (x=4, y=6) to the value 2.
        """
        # Save the dimension names in the correct order
        if not dim_names:
            if dimensions:
                dim_names = dimensions
            else:
                if pairs:
                    n_items = len(pairs)
                elif values:
                    n_items = len(values)
                else:
                    n_items = 0

                # Dynamically assign default dimension names if none are given
                namer = NameDimension()
                dim_names = (next(namer) for _ in range(n_items))
        self.dim_names = tuple(dim_names)

        # Each dimension's place/index in the right order
        self.dim_ix = {v: k for k, v in enumerate(self.dim_names)}

        # If groups of keys/coordinates are given as parallel sequences,
        # then line up the dimensions in the right order to convert them
        # into (keys, value) pairs to add to this HashGrid
        if dimensions:
            for pair in zip(values, *dimensions.values()):
                self[pair[1:]] = pair[0]

        # Add all coordinates-to-value mappings/pairs into this HashGrid
        for keys, value in pairs:
            self[keys] = value

    def __contains__(self, keys: Iterable[KT] | Mapping[str, KT], /) -> bool:
        """ Return `bool(keys in self)`.

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: bool, True if the `keys` are mapped to a value in this \
            `HashGrid`; else False if they aren't.
        """
        return super().__contains__(self._hash_keys(keys))

    def __getitem__(self, keys: Iterable[KT] | Mapping[str, KT],
                    /) -> VT:
        """ Return `self[keys]`.

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: VT, `self[keys]`; the value mapped to the `keys`
        """
        return super().__getitem__(self._hash_keys(keys))

    def __setitem__(self, keys: Iterable[KT] | Mapping[str, KT],
                    value: VT, /) -> None:
        """ Set `self[keys]` to `value`.

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :param value: VT, new value to map to `keys` in this `HashGrid`.
        """
        return super().__setitem__(self._hash_keys(keys), value)

    def _hash_keys(self, keys: Iterable[KT] | Mapping[str, KT]) -> int:
        """
        :param keys: Iterable[KT] | Mapping[str, KT], the coordinates \
            that are (or will be) mapped to a value in this `HashGrid`; one \
            key for every dimension
        :raises KeyError: if the `keys` cannot be converted into a valid \
            hash value mapped to a value in this `HashGrid`, especially if \
            the `keys` are of the wrong number or type.
        :return: int, the hash number mapped to a value in this `HashGrid`.
        """
        try:
            return hash(keys)
        except TypeError:
            return hash(self._sort_keys(keys))

    def _sort_keys(self, keys: Iterable[KT] | Mapping[str, KT]
                   ) -> tuple[KT, ...]:
        """ 
        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: tuple[KT, ...], the `keys` as a tuple sorted in the \
            correct order to access values stored in this `HashGrid`.
        """
        if isinstance(keys, Mapping):
            keys = (cast(Mapping[str, KT], keys)[dim]
                    for dim in self.dim_names)
        return tuple(keys)

    def _sort_mixed_keys(self, *keys: KT, **kwargs: KT) -> tuple[KT, ...]:
        """
        :param keys: tuple[KT], positional keys
        :param kwargs: Mapping[str, KT], keyword-mapped keys
        :raises KeyError: if some of the required keys (AKA dimensional \
            coordinates) in this `HashGrid` are in neither `keys` nor `kwargs`
        :return: tuple[KT, ...], the `keys` and `kwargs` as a tuple sorted \
            in the correct order to access values stored in this `HashGrid`.
        """
        try:
            if kwargs:
                keys_iter = iter(keys)
                keys = tuple(kwargs.get(dim, next(keys_iter))
                             for dim in self.dim_names)
            return keys

        # If keys are missing from args & kwargs, then raise KeyError
        except StopIteration:
            raise KeyError  # Don't expose keys in err?

    @classmethod
    def for_creds(cls) -> Self:
        """ Make a new `HashGrid` to map username-password pairs to values.

        :return: Self, `HashGrid(dim_names=("username", "password"))` """
        return cls(dim_names=("username", "password"))

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT]) -> VT: ...

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT],
            default: VT) -> VT: ...

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT],
            default: _D = None) -> VT | _D: ...

    def pop(self, keys, default=None):
        """ D.pop(k[,d]) -> v, remove specified keys/coordinates and return \
            the corresponding value.

        If the keys are not found, return the `default` value if given; \
        otherwise, raise a `KeyError`.

        :param keys: Iterable[KT] | Mapping[str, KT], the coordinates/keys \
            mapped to a value in this `HashGrid`; one key for every dimension
        :param default: _D: Any, what to return if the `keys` are not found; \
            defaults to None
        :return: VT | _D, the value mapped to `keys`, if any; else `default`
        """
        return super().pop(self._hash_keys(keys), default)

    def setdefault(self, keys: Iterable[KT] | Mapping[str, KT],
                   default: VT = None) -> VT:
        return super().setdefault(self._hash_keys(keys), default)


class Grid[XT: Hashable, YT: Hashable, VT](Invertionary):  # 2D Grid
    _D = TypeVar("_D")

    @overload
    def __init__(self): ...
    @overload
    def __init__(self, *tuples: tuple[XT, YT, VT]): ...

    @overload
    def __init__(self, *, x: Iterable[XT], y: Iterable[YT],
                 values: Iterable[VT]): ...

    def __init__(self, *tuples, x=tuple(), y=tuple(), values=tuple()) -> None:
        self.X: Explictionary[XT, Explictionary[YT, VT]] = Explictionary()
        self.Y: Explictionary[YT, Explictionary[XT, VT]] = Explictionary()
        if tuples:
            triples = tuples
        elif x and y and values:  # and len(x) == len(y) == len(values):
            triples = zip(x, y, values)
        else:
            triples = tuple()
        for xkey, ykey, val in triples:
            self.X[xkey][ykey] = val
            self.Y[ykey][xkey] = self.X[xkey][ykey]


class Locktionary[KT: str, VT: Bytesifiable
                  ](HashGrid[KT, bytes | None], Bytesifier, Debuggable):
    """ Multidimensional dictionary ("grid") that only allows item access, \
        storage, and modification with a valid set of keys. On its own, \
        the `Locktionary` exposes neither its keys nor its values. \
        Neither keys nor values are recoverable from the data in this \
        `Locktionary` alone (without already possessing a valid set of \
        keys) unless keys are numeric. """

    def __init__(self, *pairs: tuple[Iterable[KT], VT],
                 dim_names: Sequence[str] = tuple(),
                 values: Sequence[KT] = tuple(),
                 debugging: bool = False, salt_len: int = 16,
                 **dimensions: Sequence[KT]) -> None:
        """ Dictionary with an arbitrary number of keys ("dimensions") \
            that only allows item access, storage, and modification with a \
            valid set of keys, exposing neither its keys nor its values.

        :param pairs: tuple[Iterable[KT], VT], a tuple of 2 items: the keys, \
            and the value to assign to the combination of those keys.
        :param dim_names: Iterable[str] naming each dimension/coordinate in \
            this `Locktionary`. By default, the the dimensions are named in \
            this order: "x", "y", "z", the rest of the lowercase letters in \
            alphabetical order, & then random lowercase letter \
            combinations of increasing length.
        :param values: Iterable[VT], values to assign to the given \
            dimensions in order. Include `values` and `dimensions` to create \
            a `Locktionary` where each value in `values` is mapped to the \
            keys at the same index in each of the `dimensions`.
        :param dimensions: Mapping[str, Sequence[KT]] of each dimension's \
            name to the coordinate of each element of `values` in/along that \
            dimension.
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        """
        try:  # Create encryption mechanism
            self.encrypted: set[int] = set()
            self.salt = Randoms.randstr(min_len=salt_len, max_len=salt_len)

            # Define whether to raise any error(s) or pause and interact
            Debuggable.__init__(self, debugging=debugging)

            HashGrid.__init__(self, *pairs, dim_names=dim_names, values=values,
                              **dimensions)

        except TypeError as err:
            self.debug_or_raise(err, locals())

    def __delitem__(self, keys: Iterable[KT] | Mapping[str, KT]) -> None:
        """ Delete self[key].

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates to \
            remove and to remove the value of from this `Locktionary`.
        """
        hashkey = self._hash_keys(keys)
        self.encrypted.discard(hashkey)
        dict.__delitem__(self, hashkey)

    def __getitem__(self, keys: Iterable[KT] | Mapping[str, KT]):  # -> VT:
        """ `x.__getitem__(y)` <==> `x[y]`
        Explicitly defined to automatically decrypt encrypted values.

        :param keys: Iterable[KT] | Mapping[str, KT], the coordinates/keys \
            mapped to the value in this `Locktionary` to retrieve
        :return: Any, the decrypted value that was mapped to `keys`
        """
        try:
            sortedkeys = self._sort_keys(keys)
            hashkey = hash(sortedkeys)
            retrieved = dict.__getitem__(self, hashkey)
            if hashkey in self.encrypted:
                retrieved = self._keys2Fernet(sortedkeys).decrypt(
                    retrieved).decode(DEFAULT_ENCODING)
            return retrieved
        except (KeyError, TypeError) as err:
            self.debug_or_raise(err, locals())

    def __setitem__(self, keys: Iterable[KT] | Mapping[str, KT], value: VT
                    ) -> None:
        """ Set `self[keys]` to `value` after encrypting `value` if possible.

        :param keys: Iterable[KT] | Mapping[str, KT], keys to map to `value`.
        :param value: VT, value to encrypt (if it `SupportsBytes`) and store.
        """
        try:
            sortedkeys = self._sort_keys(keys)
            hashkey = hash(sortedkeys)
            try:
                bytesified = self._keys2Fernet(sortedkeys).encrypt(
                    self.bytesify(value, errors="raise"))
                self.encrypted.add(hashkey)
            except TypeError:
                bytesified = value
                self.encrypted.discard(hashkey)
            return dict.__setitem__(self, hashkey, bytesified)
            # return super(Locktionary, self).__setitem__(keys, bytesified)
        except AttributeError as err:
            self.debug_or_raise(err, locals())

    def _keys2Fernet(self, keys: tuple[KT, ...], encoding: str =
                     DEFAULT_ENCODING) -> Fernet:
        """
        :param keys: tuple[str, ...], keys/coordinates mapped to the value \
            to encrypt or decrypt. The keys are used in (en/de)cryption.
        :param encoding: str, the encoding with which to encode values from \
            `str` to `bytes`; defaults to the system default (usually "utf-8")
        :return: cryptography.fernet.Fernet to (en/de)crypt values.
        """  # TODO: This is waaay overcustomized. Do it in a standard way.
        salted_keys = [keys[0], self.salt, *keys[1:]]
        i = 0
        chars: list[str] = list()
        complete = False
        while not complete:
            try:
                for key in salted_keys:
                    if len(chars) < 32:  # Fernet key must be 32 chars
                        chars.append(str(key)[i])
                    else:
                        complete = True
                        break
                i += 1
            except IndexError:
                i = 0

        return Fernet(self.encode("".join(chars), encoding))

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT]) -> VT: ...

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT],
            default: VT) -> VT: ...

    @overload
    def pop(self, keys: Iterable[KT] | Mapping[str, KT],
            default: HashGrid._D = None) -> VT | HashGrid._D: ...

    def pop(self, keys, default=None):
        """ D.pop(k[,d]) -> v, remove specified keys/coordinates and return \
            the corresponding value.

        If the keys are not found, return the `default` value if given; \
        otherwise, raise a `KeyError`.

        Defined separately from `HashGrid.pop` to add decryption capabilities.

        :param keys: Iterable[KT] | Mapping[str, KT], the coordinates/keys \
            mapped to a value in this `HashGrid`; one key for every dimension
        :param default: _D: Any, what to return if the `keys` are not found; \
            defaults to None
        :return: VT | _D, the value mapped to `keys`, if any; else `default`
        """
        popped = self[keys]
        dict.pop(self, self._hash_keys(keys), default)
        return popped
