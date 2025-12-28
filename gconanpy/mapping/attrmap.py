"""
Class that forces type checker to understand dot notation item access.
Greg Conan: gregmconan@gmail.com
Created: 2025-11-21
Updated: 2025-12-05
"""
# Import standard libraries
from collections.abc import Callable, Generator, Mapping, MutableMapping
from typing import Any, get_args, Literal, overload, Self, TypeVar

# Import local custom libraries
try:
    from gconanpy.meta import error_changer
except (ImportError, ModuleNotFoundError):
    from meta import error_changer

# Wrapper function that takes a method that can raise AttributeError and
# returns a copy identical except that it can raise KeyError.
wrap_attr2key = error_changer(AttributeError, KeyError)


class AttrMap[T](MutableMapping[str, T]):
    """ Simple `MutableMapping[str, T]` that can store, access, and modify \
        items as attributes using dot notation, in a manner that is \
        recognizable by type checkers. """
    # Attributes, methods, and other keywords that should not be
    # mutable/modifiable as items/key-value pairs. Define them all explicitly
    # so static type checkers can distinguish between using dot notation to
    # get a named attribute and using it as shorthand to get a value/item.
    _METHOD = Literal[  # TODO ADD ALL INHERITED FROM MUTABLEMAPPING
        "__class_getitem__", "__contains__", "__delattr__", "__delitem__",
        "__dir__", "__eq__", "__format__", "__ge__", "__getattr__",
        "__getattribute__", "__getitem__", "__getstate__", "__gt__",
        "__init__", "__init_subclass__", "__ior__", "__iter__", "__le__",
        "__len__", "__lt__", "__ne__", "__new__", "__or__", "__reduce__",
        "__reduce_ex__", "__repr__", "__reversed__", "__ror__",
        "__setattr__", "__setitem__", "__setstate__", "__sizeof__",
        "__str__", "__subclasshook__", "__weakref__", "asdict",
        "clear", "copy", "fromkeys", "get", "items", "keys", "pop", "popitem",
        "setdefault", "update", "values"]
    _MISC_ATTR = Literal["__base__", "__bases__", "__basicsize__", "__hash__",
                         "__orig_class__", "__weakref__"]
    _STR_SET = Literal["__mutable__", "__protected_keywords__", "names"]
    _TUP_ATTR = Literal["__orig_bases__", "__parameters__", "__type_params__"]
    _TYPE_VAR = Literal["_METHOD", "_MISC_ATTR", "_STR_SET",
                        "_TUP_ATTR", "_TYPE_VAR"]

    __dict__: dict[str, T]
    __mutable__: set[str] = {"names", }
    __protected_keywords__: set[str] = {
        "__dict__", *get_args(_STR_SET), *get_args(_METHOD),
        *get_args(_MISC_ATTR), *get_args(_TUP_ATTR), *get_args(_TYPE_VAR)}
    names: set[str]

    def __init__(self, from_map: Mapping[str, T] = {}, **kwargs: T
                 ) -> None:
        self.names = set[str]()
        kwargs.update(from_map)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __contains__(self, name: str) -> bool:
        return hasattr(self, name)

    def __delattr__(self, name: str, /) -> None:
        if name in getattr(self, "__protected_keywords__", ()):
            raise AttributeError("Cannot delete protected attribute")
        super().__delattr__(name)
        self.names.discard(name)

    def __iter__(self) -> Generator[str, None, None]:
        yield from self.names

    def __len__(self) -> int:
        return len(self.names)

    @overload
    def __getattribute__(self, name: _METHOD) -> Callable: ...
    @overload
    def __getattribute__(self, name: _STR_SET) -> set[str]: ...
    @overload
    def __getattribute__(self, name: _TUP_ATTR) -> tuple: ...
    @overload
    def __getattribute__(self, name: _TYPE_VAR) -> TypeVar: ...
    @overload
    def __getattribute__(self, name: Literal["__hash__"]) -> None: ...
    @overload
    def __getattribute__(self, name: Literal["__weakref__"]) -> Any: ...
    @overload
    def __getattribute__(self, name: Literal["__orig_class__"]) -> type: ...

    @overload
    def __getattribute__(self, name: Literal["__dict__"]
                         ) -> dict[str, T]: ...

    @overload
    def __getattribute__(self, name: str) -> T: ...

    def __getattribute__(self, name):
        # Overloaded instead of __getattr__ because otherwise static type
        # checkers won't recognize value types when accessed with dot notation
        return super().__getattribute__(name)

    def __repr__(self) -> str:
        return str(self.asdict())

    def __setattr__(self, name: str, value: T, /) -> None:
        if name in getattr(self, "__protected_keywords__", ()):
            if name not in getattr(self, "__mutable__", ()):
                raise AttributeError("Cannot change protected attribute")
        else:
            self.names.add(name)
        super().__setattr__(name, value)

    # The (g/s)etitem and delitem methods are identical to their respective
    # attribute access methods, except raising KeyError not AttributeError
    __delitem__ = wrap_attr2key(__delattr__)
    __getitem__ = wrap_attr2key(__getattribute__)
    __setitem__ = wrap_attr2key(__setattr__)

    def asdict(self) -> dict[str, T]:
        return {n: getattr(self, n) for n in self.names}

    def clear(self) -> None:
        for name in self.names:
            delattr(self, name)

    def copy(self) -> Self:
        return type(self)(self.asdict())


class DefaultAttrMap[T](AttrMap[T]):
    """ `DefaultAttrMap` is to `AttrMap` what `defaultdict` is to `dict`. """

    __mutable__: set[str] = {"_default_factory", "names"}
    __protected_keywords__: set[str] = {"_default_factory",
                                        *AttrMap.__protected_keywords__}

    def __init__(self, default_factory: Callable[[str], T],
                 from_map: Mapping[str, T] = {}, **kwargs: T) -> None:
        self._default_factory = default_factory
        super().__init__(from_map, **kwargs)

    def __getattr__(self, name: str):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            value = self._default_factory(name)
            setattr(self, name, value)
            return value

    # Ensure that trying to access a missing item will create a new item
    __getitem__ = wrap_attr2key(__getattr__)
