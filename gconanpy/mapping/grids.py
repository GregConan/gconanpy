#!/usr/bin/env python3

"""
Custom multidimensional dictionaries extending dicts.py classes.
Greg Conan: gregmconan@gmail.com
Created: 2025-08-23
Updated: 2025-11-03
"""
# Import standard libraries
import abc
from collections.abc import Collection, Generator, Hashable, \
    Iterable, Mapping, Sequence
import string
from typing import Any, cast, overload, Self, TypeVar

# Import local custom libraries
try:
    from gconanpy.bytesify import Bytesifiable, DEFAULT_ENCODING, Encryptor
    from gconanpy.debug import Debuggable
    from gconanpy.iters import ColumnNamer
    from gconanpy.mapping.dicts import CustomDict
    from gconanpy.meta import name_of
    from gconanpy.meta.typeshed import ComparableHashable
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from bytesify import Bytesifiable, DEFAULT_ENCODING, Encryptor
    from iters import ColumnNamer
    from debug import Debuggable
    from mapping.dicts import CustomDict
    from meta import name_of
    from meta.typeshed import ComparableHashable


class BaseHashGrid[KT: Hashable, VT](abc.ABC, CustomDict[int, VT]):
    _D = TypeVar("_D")

    @abc.abstractmethod
    def _sort_keys(self, keys) -> tuple[KT, ...]: ...

    # TODO Use a method to wrap every dict method to insert _hash_keys(...)?
    # def _wrap(func: Callable[...]) -> Callable[...]:

    def __contains__(self, keys: Iterable[KT] | Mapping[str, KT], /) -> bool:
        """ Return `bool(keys in self)`.

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: bool, True if the `keys` are mapped to a value in this \
            `HashGrid`; else False if they aren't.
        """
        return super().__contains__(self._hash_keys(keys))

    def __getitem__(self, keys: Iterable[KT] | Mapping[str, KT], /) -> VT:
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
        :raises ValueError: if `strict=True` and `keys` is the wrong length \
            (its length should equal the number of dimensions).
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


class UnorderedHashGrid[KT: ComparableHashable, VT
                        ](BaseHashGrid[KT, VT]):
    def __init__(self, *pairs: tuple[Iterable[KT], VT]) -> None:
        super().__init__(*pairs)

    def _sort_keys(self, keys: Iterable[KT]) -> tuple[KT, ...]:
        """ 
        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: tuple[KT, ...], the `keys` as a tuple sorted in the \
            correct order to access values stored in this `HashGrid`.
        """
        return tuple(sorted(tuple(keys)))


class HashGrid[KT: Hashable, VT](BaseHashGrid[KT, VT]):
    """ `dict` mapping combinations of keys to specific values.

    Called a "Grid" because it maps 1 group of multiple keys to 1 value in \
    the same way that a grid maps 1 set of multiple dimensional coordinates \
    to 1 point. Each `HashGrid` has a specific number of dimensions; i.e., \
    a certain number of keys that must be provided together in the correct \
    order to access or modify the corresponding items.

    `HashGrid` does not know its own combinations of `keys`, so calling the \
    `.keys()` method on a `HashGrid` will return hash `int`s instead of \
    anything meaningful. This may have cryptographic use.

    For example, calling `creds = HashGrid.for_creds()` (equivalent to \
    `creds = HashGrid(names=("username", "password"))`) creates a \
    `HashGrid` with two dimensions ("username" and "password"). It lets only \
    a user with the correct "username" and "password" credentials access the \
    value mapped to them, but no one else.

    After calling `creds["myuser", "mypass"] = "myvalue"` to add a value for \
    the given user, `creds` will not store (or otherwise be able to produce) \
    the values "myuser" or "mypass" even though a user could get or alter \
    "myvalue" by accessing `creds["myuser", "mypass"]`.
    """
    _D = TypeVar("_D")  # Type hint for "default" parameter

    # By default, name the dimensions like lowercase MS Excel columns:
    # (a, b, c, ..., x, y, z, aa, ab, ac, ..., ax, ay, az, ba, bb, bc, ...)
    DEFAULT_DIMS = string.ascii_lowercase  # Used in _name_dims

    @overload
    def __init__(self, *pairs: tuple[Collection[KT], VT]) -> None: ...

    @overload
    def __init__(self, *pairs: tuple[Collection[KT], VT],
                 strict: bool) -> None: ...

    @overload
    def __init__(self, *pairs: tuple[Collection[KT], VT],
                 dim_names: Sequence[str]) -> None: ...

    @overload
    def __init__(self, *pairs: tuple[Collection[KT], VT], strict: bool,
                 dim_names: Sequence[str]) -> None: ...

    @overload
    def __init__(self, *, values: Sequence[VT], strict: bool,
                 **dimensions: Iterable[KT]) -> None: ...

    @overload
    def __init__(self, *, dim_names: Sequence[str], values: Sequence[VT],
                 strict: bool = True, **dimensions: Iterable[KT]) -> None: ...

    def __init__(self, *pairs, dim_names=tuple(), values=tuple(),
                 strict=True, **dimensions) -> None:
        """ Mapping of an arbitrary number of dimensions to specific values.

        `hg = HashGrid(([1,2,3], "foo"), ([7,8,9], "bar"))` is the same as \
        `hg = HashGrid(values=["foo", "bar"], x=[1, 7], y=[2, 8], z=[3, 9])` \
        and both mean that `hg[1, 2, 3] == "foo"` and `hg[7, 8, 9] == "bar"`.

        Initialize with either `pairs` or `values`, not both.

        :param pairs: tuple[Collection[KT], VT], a tuple of 2 items: the \
            keys, and the value to assign to the combination of those keys.
        :param dim_names: Iterable[str] naming each dimension/coordinate in \
            this HashGrid. By default, the the dimensions are named in this \
            order: "x", "y", "z", the rest of the lowercase letters in \
            alphabetical order, & then random lowercase letter \
            combinations of increasing length.
        :param values: Iterable[VT], values to assign to the provided \
            dimensions in order. Include `values` and `dimensions` to create \
            a `HashGrid` where each value in `values` is mapped to the key \
            (coordinate) at the same index in each of the `dimensions`.
        :param strict: bool, True to raise a ValueError if the number of \
            dimensions is not specified during initialization or if someone \
            provides the wrong number of keys; else False to try to use the \
            keys anyway; defaults to True
        :param dimensions: Mapping[str, Iterable[KT]] of each dimension's \
            name to the coordinate of each element of `values` in/along that \
            dimension. `HashGrid(values=[1,2], x=[3, 4], y=[5, 6])`, for \
            example, maps the coordinate (x=3, y=5) to the value 1 and maps \
            the coordinate (x=4, y=6) to the value 2.
        """
        self.strict = strict

        # Save the dimension names in the correct order
        self.dim_names = tuple(dim_names if dim_names else
                               dimensions if dimensions else
                               self._name_dims(pairs, strict))

        self._fill(*pairs, values=values, **dimensions)

    def __setitem__(self, keys: Collection[KT] | Mapping[str, KT],
                    value: VT, /) -> None:
        """ Set `self[keys]` to `value`.

        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :param value: VT, new value to map to `keys` in this `HashGrid`.
        :raises ValueError: if `strict=True` and `keys` is the wrong length \
            (its length should equal the number of dimensions).
        """
        if self.strict:
            self._validate_n_keys(keys)

        return super().__setitem__(keys, value)

    def _fill(self, *pairs, values=tuple(), **dimensions):

        # Each dimension's place/index in the right order
        self.dim_ix = {v: k for k, v in enumerate(self.dim_names)}

        # If groups of keys/coordinates are given as parallel sequences,
        # then line up the dimensions in the right order to convert them
        # into (keys, value) pairs to add to this HashGrid
        if bool(values) != bool(dimensions):
            raise TypeError("Must provide `dimensions` and `values`.")
        elif values:  # and dimensions:
            for pair in zip(values, *dimensions.values()):
                self[pair[1:]] = pair[0]

        # Add all coordinates-to-value mappings/pairs into this HashGrid
        for keys, value in pairs:
            self[keys] = value

    @classmethod
    def _name_dims(cls, pairs: Iterable[tuple[Collection[KT], Any]] = (),
                   strict: bool = True) -> Generator[str, None, None]:
        """ 
        :param pairs: tuple[Collection[KT], VT], a tuple of 2 items where \
            the first item is the keys (dimensional coordinates).
        :param strict: bool, True to raise a ValueError if the number of \
            dimensions is not specified during initialization or if someone \
            provides the wrong number of keys; else False to try to use the \
            keys anyway; defaults to True
        :raises ValueError: _description_
        :return: Generator[str, None, None], the dimension names in the \
            correct order.
        """
        err_msg = f"Cannot initialize {name_of(cls)} if strict=True "
        if pairs:  # Count how many keys are in each pair
            lens = {len(p[0]) for p in pairs}
            if strict and len(lens) != 1:
                raise ValueError(err_msg + "and the number of keys "
                                 f"given is inconsistent: {lens}")
            n_items = max(lens)
        elif strict:
            raise ValueError(err_msg + "without specifying the "
                             "names or number of dimensions.")
        else:
            n_items = 0

        # Dynamically assign default dimension names if none are given
        namer = ColumnNamer(cls.DEFAULT_DIMS)
        return (next(namer) for _ in range(n_items))

    def _sort_keys(self, keys: Mapping[str, KT] | Iterable[KT]
                   ) -> tuple[KT, ...]:
        """ 
        :param keys: Iterable[KT] | Mapping[str, KT], keys/coordinates
        :return: tuple[KT, ...], the `keys` as a tuple sorted in the \
            correct order to access values stored in this `HashGrid`.
        """
        if isinstance(keys, Mapping):
            # Split these 2 lines to avoid "generator not subscriptable" err
            cast_keys = cast(Mapping[str, KT], keys)
            keys = (cast_keys[dim] for dim in self.dim_names)
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

    def _validate_n_keys(self, keys: Collection[KT] | Mapping[str, KT]) -> None:
        n_given = len(keys)
        n_dims = len(self.dim_names)
        if n_given != n_dims:
            raise ValueError(f"{n_given} keys provided instead of the "
                             f"correct number for this {name_of(self)} "
                             f"({n_dims} keys)")

    @classmethod
    def for_creds(cls, *pairs: tuple[Iterable[KT], VT],
                  values: Sequence[VT] = (),  strict: bool = True,
                  usernames: Sequence[KT] = (),
                  passwords: Sequence[KT] = ()) -> Self:
        """ Make a new `HashGrid` to map username-password pairs to values.

        :return: Self, `HashGrid(names=("username", "password"))` """
        kwargs = {}
        if usernames:
            kwargs["usernames"] = usernames
        if passwords:
            kwargs["passwords"] = passwords
        if not pairs:
            kwargs["values"] = values
        return cls(*pairs, dim_names=("username", "password"), strict=strict,
                   **kwargs)


class Grid[KT: Hashable, VT]:  # (Invertionary):  # 2D Grid
    _D = TypeVar("_D")

    @overload
    def __init__(self): ...
    @overload
    def __init__(self, *tuples: tuple[KT, KT, VT]): ...

    @overload
    def __init__(self, *, x: Iterable[KT], y: Iterable[KT],
                 values: Iterable[VT]): ...

    def __init__(self, *tuples, x=tuple(), y=tuple(), values=tuple()) -> None:
        self.X: dict[KT, dict[KT, VT]] = {}
        self.Y: dict[KT, dict[KT, VT]] = {}
        if tuples:
            triples = tuples
        elif x and y and values:  # and len(x) == len(y) == len(values):
            triples = zip(x, y, values, strict=True)
        else:
            triples = ()
        for xkey, ykey, val in triples:
            self.X[xkey][ykey] = val
            self.Y[ykey][xkey] = self.X[xkey][ykey]

    def invert(self) -> None:
        self.X, self.Y = self.Y, self.X


class Locktionary[KT: str, VT: Bytesifiable
                  ](HashGrid[KT, bytes | None], Encryptor, Debuggable):
    """ Multidimensional dictionary ("grid") that only allows item access, \
        storage, and modification with a valid set of keys. On its own, \
        the `Locktionary` exposes neither its keys nor its values. \
        Neither keys nor values are recoverable from the data in this \
        `Locktionary` alone (without already possessing a valid set of \
        keys) unless keys are numeric. """

    def __init__(self, *pairs: tuple[Collection[KT], VT],
                 dim_names: Sequence[str] = (),
                 values: Sequence[KT] = (), strict: bool = True,
                 debugging: bool = False,
                 iterations: int = 500,  # TODO Increase after optimizing?
                 **dimensions: Iterable[KT]) -> None:
        """ Dictionary with an arbitrary number of keys ("dimensions") \
            that only allows item access, storage, and modification with a \
            valid set of keys, exposing neither its keys nor its values.

        :param pairs: tuple[Collection[KT], VT], a tuple of 2 items: the \
            keys, and the value to assign to the combination of those keys.
        :param dim_names: Iterable[str] naming each dimension/coordinate in \
            this `Locktionary`. By default, the the dimensions are named in \
            this order: "x", "y", "z", the rest of the lowercase letters in \
            alphabetical order, & then random lowercase letter \
            combinations of increasing length.
        :param values: Iterable[VT], values to assign to the given \
            dimensions in order. Include `values` and `dimensions` to create \
            a `Locktionary` where each value in `values` is mapped to the \
            keys at the same index in each of the `dimensions`.
        :param strict: bool, True to raise a ValueError if the number of \
            dimensions is not specified during initialization or if someone \
            provides the wrong number of keys; else False to try to use the \
            keys anyway; defaults to True
        :param dimensions: Mapping[str, Iterable[KT]] of each dimension's \
            name to the coordinate of each element of `values` in/along that \
            dimension.
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        """
        try:
            self.strict = strict

            # Save the dimension names in the correct order
            self.dim_names = tuple(dim_names if dim_names else
                                   dimensions if dimensions else
                                   self._name_dims(pairs, strict))

            # Create encryption mechanism
            Encryptor.__init__(self, len(dim_names), iterations)

            # Define whether to raise any error(s) or pause and interact
            Debuggable.__init__(self, debugging=debugging)

            self._fill(*pairs, values=values, **dimensions)

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

    def __repr__(self) -> str:
        """ Summarize this `Locktionary` without providing any specific \
            details about any of its contents in particular.

        :return: str, a Python-valid representation of the input parameters \
            that define this `Locktionary`: the dimensions' names, `strict`, \
            and `debugging`.
        """
        return (f"{name_of(self)}(dim_names={self.dim_names}, "
                f"strict={self.strict}, debugging={self.debugging})")

    def __setitem__(self, keys: Collection[KT] | Mapping[str, KT], value: VT
                    ) -> None:
        """ Set `self[keys]` to `value` after encrypting `value` if possible.

        :param keys: Collection[KT] | Mapping[str, KT], keys to map to `value`.
        :param value: VT, value to encrypt (if it `SupportsBytes`) and store.
        :raises ValueError: if the wrong number of keys is given.
        :raises AttributeError: if _description_ TODO
        """
        if self.strict:
            self._validate_n_keys(keys)
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
