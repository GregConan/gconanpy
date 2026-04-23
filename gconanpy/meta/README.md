# Meta

## Overview

Low-level utilities, custom types, and metaclass functionality. The `meta` module provides utilities for object introspection, creating custom metaclasses, and implementing advanced type checking mechanisms.

## Dependencies

This module has no third-party dependencies.

## Modules

### `__init__.py`

Core utilities, as well as meta-programming and type checking functionality.

#### Functions

- `areinstances`: Check if all objects are instances of specified types.
- `bool_pair_to_cases`: Convert a boolean pair to a case number (0-3) to represent multiplying two binary conditions together: (False, False), (True, False), (False, True), and (True, True).
- `error_changer`: Create a wrapper to change which exception a `Callable` raises.
- `count_digits_of`: Count digits in a number.
- `divmod_base`: Create a `divmod` function for a specific numerical base.
- `full_name_of`: Get the fully qualified name of an object (module + name).
- `geteverything`: Get all local, global, and built-in variables.
- `has_method`: Check if an object has a specific callable attribute (method).
- `hashable`: Check if an object is hashable.
- `method`: Create a callable that retrieves and calls a named method of its first argument.
- `name_of`: Get the name of an object or of its type/class.
- `names_of`: Get names of multiple objects.
- `tuplify`: Convert an object to a tuple or place it into a tuple.
- `which_of`: Find which conditions are true, returning their indices.

#### Key Classes

- `Boolable`: Any object that you can call `bool()` on is a `Boolable`.
- `cached_property`: Parameterized property that is only computed once per instance and then replaces itself with an ordinary attribute.
- `Comparer`: Base class providing value comparison methods to find the biggest or smallest item in an iterable.
- `ErrCatcher`: Base exception catcher class.
- `IgnoreExceptions`: Context manager for ignoring specified exceptions.
- `IteratorFactory`: Base class providing iterator creation methods (`first_element_of`, `iterate`).
- `KeepSkippingExceptions`: Base class for retrying until success.
- `KeepTryingUntilNoErrors`: Context manager that tries code blocks in sequence until one succeeds without raising specified errors.
- `MethodWrappingMeta`: Metaclass to wrap all instance methods of a class so methods returning the superclass type return the subclass type instead.
- `Recursively`: Static methods for recursive item and attribute access (`getitem`, `getattribute`, `setitem`).
- `TimeSpec`: Calculates time specification conversion factors, especially to support `datetime` library operations.
- `Traversible`: Base class for recursive iterators that can visit all items in a nested container data structure.

### `metaclass.py`

Metaclass creation utilities and advanced type checking.

#### Functions

- `combinations_of_conditions`: Generate a `dict` mapping all combinations of named boolean conditions to values.
- `name_type_class`: Generate a descriptive name for a type-checking metaclass.

#### Classes

- `MakeMetaclass`: Factory for creating custom metaclasses with configurable `__instancecheck__` and `__subclasscheck__` methods.
- `MatcherBase`: Base class for mapping boolean condition combinations to values.
- `NonIterable`: Metaclass-based type for objects that lack an `__iter__` method.
- `PrivateAttrNameMeta`: Metaclass for `PrivateAttrName`, which identifies strings starting with `__`.
- `PrivateAttrName`: A `str` subclass whose `isinstance` check returns True for strings starting with `__`.
- `TypeFactory`: Factory for creating type-checking metaclasses based on method presence/absence.

### `typeshed.py`

Custom type classes, especially protocols and abstract base classes, to support type hinting. Many of them already exist in Python's builtin `_typeshed` library, but that cannot be imported at runtime, so I defined them here. Most of the classes in `typeshed.py` are defined only for type-checking to indicate that an object has a specific method or attribute:

- `Boolable` means "supports `bool(x)`"
- `BytesOrStr` means "`bytes | str | bytearray`"
- `HasClass` means "has a `__class__` attribute"
- `HasSlots` means "has a `__slots__` attribute"
- `Poppable` means "supports `x.pop(...)`"
- `SupportsAdd`means "supports `+` (`__add__`)"
- `SupportsAnd`means "supports `&` (`__and__`)"
- `SupportsContains`means "supports `x in obj`"
- `SupportsGetItem`means "supports `obj[key]`"
- `SupportsGetSlice`means "supports both index and slice access."
- `SupportsRichComparison`means "supports all six comparison operators."
- `Updatable` means "supports `x.update(...)`"

Some combine multiple Protocols:

- `ComparableHashable` combines `SupportsRichComparison` and `Hashable`.
- `CollectionFromIterable` combines `Collection` and an `__init__` method allowing construction from an `Iterable`.
- `ProtoSequence` combines `Iterable`, `SupportsLenAndGetSlice`, and `SupportsContains` with `.count()` and `index(...)` support to expose the full `Sequence` interface except for `__reversed__`.
- `SupportsLenAndGetItem` combines `SupportsGetItem` with `len()` support.
- `SupportsLenAndGetSlice` combines `SupportsGetSlice` with `__len__` support.
- `SupportsHashAndGetItem` combines `SupportsGetSlice` with `Hashable`.
- `SupportsItemAccess` combines `SupportsContains` and `SupportsGetItem` with `__delitem__` and `__setitem__` support.

Some `Protocol` classes *exclude* certain types or functionality:

- `Unhashable`: Metaclass-based type for unhashable objects.

A few more complicated examples exclude existing types and subclass others. They specify that an object "is an X, but not a Y":

- `PureIterable` means "`Iterable`, but not `str`, `bytes`, or `Mapping`."
- `NonTxtCollection` means "`Collection`, but not `str` or `bytes`."

Some are metaclasses to implement other classes or `Protocol`s:

- `BytesOrStrMeta`: Metaclass for `BytesOrStr`.
- `MultiTypeMeta`: Abstract metaclass supporting combined type checking (is-a AND is-not-a).
- `NonTxtColMeta`: Metaclass for `NonTxtCollection`.
- `PureIterableMeta`: Metaclass for `PureIterable`.

Others combine class-checking and method-checking:

- `HashableSequence` means `Sequence`s that are `Hashable` (support `hash`).
- `AddableSequence` means "`Sequence` that supports `+` (`__add__`)"

Finally, others are custom exceptions or groups of exceptions:

- `DATA_ERRORS` is simply a tuple of common data-related exception types `(AttributeError, IndexError, KeyError, TypeError, ValueError)` that are occasionally useful to catch and handle simultaneously.
- `SkipException` is raised by `ErrCatcher` subclasses to skip a block of code.

## Usage Examples

### Exception Logic Patterns

In some cases, it can be useful to write patterns that apply `if-then` logic or iterative `for`/`while` logic to exception handling. One example is, "If code block 1 raises an exception, then try code block 2; if block 2 raises an exception, then try block 3; ... then try block `n`." The following classes support this pattern: 

Only two of these classes should be necessary in practice: `IgnoreExceptions` and `KeepTryingUntilNoErrors`. Applying the pattern is simple and (in my opinion) intuitive:

```python
code_block_failure = (KeyError, ValueError)
with KeepTryingUntilNoErrors(*code_block_failure) as next_try:
    with next_try():
        ...  # code block 1
    with next_try():
        ...  # code block 2
    with next_try():
        ...  # code block 3
```

Python will execute the code blocks in sequence until one of them works (i.e., does not raise any of the specified errors), and then skip the rest of the blocks. Read it as "Keep trying until one code block raises none of those errors: first try code block 1; next, try code block 2; next, try..." 

Unlike repeated nested `try`/`except` blocks, the `KeepTryingUntilNoErrors` class does not require increasing the indentation level once per case.

The `IgnoreExceptions` class functions as shorthand for `try`/`except` blocks like this:

```python
try:
    ...  # code block
except ERR_TYPES:
    pass
```

The equivalent would be a code block nested under the line `with IgnoreExceptions(ERR_TYPES):`. I may rename the class, because it doesn't *ignore* exceptions per se; it skips the code blocks that raise them.

```python
from gconanpy.meta import has_method, HumanBytes, IgnoreExceptions, name_of

# If risky_operation fails, then abort it but keep executing this file
with IgnoreExceptions(TypeError, ValueError):
    result = risky_operation()

# Check if object has method (hasattr + callable)
if has_method(obj, "save"):
    obj.save()

# Get an object's class name
obj_name = name_of(my_object)
```

### Custom Metaclass Creation

```python
from gconanpy.meta.metaclass import MakeMetaclass

# Create metaclass that checks for specific methods
SupportsSerialize = MakeMetaclass.for_methods("serialize", include=True)

class MyClass(metaclass=SupportsSerialize):
    def serialize(self):
        return "serialized data"

isinstance(MyClass(), SupportsSerialize)  # -> True

def a_func(an_object: SupportsSerialize):
    ...
    an_object.serialize()
    ...
```

### Type Checking

```python
from gconanpy.meta.typeshed import Boolable, NonTxtCollection

# Type hint indicates that conditions will be used as booleans
def bools(*conditions: Boolable) -> list[str]:
    return ["X" if cond else "Y" for cond in conditions]

def recursive_extract(nested_iterable: Iterable) -> list:
    data = []

    # Traverse a nested container and extract its data
    for item in nested_iterable:

        # If it's a data container, then extract its elements' data
        if isinstance(item, NonTxtCollection):
            recursive_extract(item)

        else:  # If it's data (int, float, *or str*), then extract it
            data.append(item)
```

### Retry Until Success

```python
from gconanpy.meta import IgnoreExceptions, KeepTryingUntilNoErrors

# Retry until success
with KeepTryingUntilNoErrors(ConnectionError, TimeoutError) as next_try:
    with next_try():  # First, try to get it from the first source
        result = get_from_first_source()
    with next_try():  # If the first source fails, then try the next
        result = get_from_second_source()
    with next_try():  # If both sources fail, then try a third
        result = get_from_tertiary_source()

# Ignore specific exceptions
with IgnoreExceptions(AttributeError, KeyError):
    value = obj.missing_attribute
```

### Comparison Utilities

```python
from gconanpy.meta import Comparer

# Find smallest item by custom criteria
smallest = Comparer.compare(
    items=my_list,
    compare_their=len,  # Compare by length
    make_comparable=str,  # Convert to string for comparison
    smallest=True  # Return the shortest, not the longest
)
```

### Method Availability Checking

```python
from gconanpy.meta import has_method

def process_object(obj):
    if has_method(obj, "validate"):
        obj.validate()
    
    return obj.serialize() if has_method(obj, "serialize") else str(obj)
```

### Inspecting Objects

```python
from gconanpy.meta import names_of

def log_objects(*objects):
    names = names_of(objects)
    for obj, name in zip(objects, names):
        print(f"Processing {name}: {obj}")
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-17
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
