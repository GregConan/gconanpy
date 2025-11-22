"""
Class that forces type checker to understand dot notation item access.
Greg Conan: gregmconan@gmail.com
Created: 2025-11-21
Updated: 2025-11-21
"""
# Import standard libraries
from collections.abc import Callable, Generator
from typing import Any, get_args, Literal, overload, TypeVar


class StringBall(object):
    """ Simple `Mapping[str, str]` that can store, access, and modify items \
        as attributes using dot notation, recognizably by type checkers. """
    # Attributes, methods, and other keywords that should not be
    # mutable/modifiable as items/key-value pairs. Define them all explicitly
    # so static type checkers can distinguish between using dot notation to
    # get a named attribute and using it as shorthand to get a value/item.
    _METHOD = Literal[
        "__class_getitem__", "__contains__", "__delattr__", "__delitem__",
        "__dir__", "__eq__", "__format__", "__ge__", "__getattr__",
        "__getattribute__", "__getitem__", "__getstate__", "__gt__",
        "__init__", "__init_subclass__", "__ior__", "__iter__", "__le__",
        "__len__", "__lt__", "__ne__", "__new__", "__or__", "__reduce__",
        "__reduce_ex__", "__repr__", "__reversed__", "__ror__",
        "__setattr__", "__setitem__", "__setstate__", "__sizeof__",
        "__str__", "__subclasshook__", "__weakref__",
        "_will_now_traverse", "clear", "copy", "fromkeys", "get",
        "items", "keys", "pop", "popitem", "setdefault", "update", "values"]
    _MISC_ATTR = Literal["__weakref__", "__hash__"]
    _STR_SET = Literal["__protected_keywords__", "names"]
    _TUP_ATTR = Literal["__orig_bases__", "__parameters__", "__type_params__"]
    _TYPE_VAR = Literal["_METHOD", "_MISC_ATTR", "_STR_SET",
                        "_TUP_ATTR", "_TYPE_VAR"]

    __dict__: dict[str, str]
    __protected_keywords__: set[str] = {
        "__dict__", "__protected_keywords__", *get_args(_METHOD),
        *get_args(_MISC_ATTR), *get_args(_TUP_ATTR), *get_args(_TYPE_VAR)}
    names: set[str]

    def __init__(self, **kwargs: str) -> None:
        self.names = set[str]()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __contains__(self, name: str) -> bool:
        return hasattr(self, name)

    def __delattr__(self, name: str, /) -> None:
        if name in getattr(self, "__protected_keywords__", set()
                           ) or name == "names":
            raise AttributeError("Cannot delete protected attribute")
        super().__delattr__(name)
        self.names.discard(name)

    def __delitem__(self, name: str) -> None:
        delattr(self, name)

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
    def __getattribute__(self, name: Literal["__dict__"]
                         ) -> dict[str, str]: ...

    @overload
    def __getattribute__(self, name: str) -> str: ...

    def __getattribute__(self, name):
        # Overloaded instead of __getattr__ because otherwise static type
        # checkers won't recognize value types when accessed with dot notation
        return super().__getattribute__(name)

    def __getitem__(self, name: str) -> str:
        return getattr(self, name)

    def __setattr__(self, name: str, value: Any, /) -> None:
        if name in getattr(self, "__protected_keywords__", set()):
            raise AttributeError("Cannot change protected attribute")
        elif name != "names":
            self.names.add(name)
        super().__setattr__(name, value)

    def __setitem__(self, name: str, value: str) -> None:
        setattr(self, name, value)

    def get(self, name: str, default: str) -> str:
        return self[name] if name in self else default

    def items(self) -> Generator[tuple[str, str], None, None]:
        for name in self:
            yield name, self[name]

    keys = __iter__

    def setdefault(self, name: str, default: str) -> str:
        if name in self:
            return self[name]
        else:
            self[name] = default
            return default

    def values(self) -> Generator[str, None, None]:
        for name in self:
            yield self[name]
