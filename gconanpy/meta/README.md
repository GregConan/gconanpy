# Meta

Low-level utilities, custom types, and metaclass functionality.

## Overview

The `meta` module provides utilities for object introspection, creating custom metaclasses, and implementing advanced type checking mechanisms.

## Dependencies

- Standard library modules: `abc`, `collections.abc`, `typing`, `typing_extensions`
- No external dependencies required

## Modules

### `__init__.py`

Core utilities, as well as meta-programming and type checking functionality.

#### Key Functions

- **`areinstances`**: Check if objects are instances of specified types
- **`bool_pair_to_cases`**: Convert boolean pair to case number
- **`count_digits_of`**: Count digits in a number
- **`divmod_base`**: Create divmod function for specific base
- **`full_name_of`**: Get full qualified name of object
- **`geteverything`**: Get all local variables
- **`has_method`**: Check if object has specific method
- **`hashable`**: Check if object is hashable
- **`method`**: Create method callable
- **`name_of`**: Get name of object (class, module, etc.)
- **`names_of`**: Get names of multiple objects
- **`tuplify`**: Convert object to tuple
- **`which_of`**: Find which conditions are true

#### Utility Classes

- **`HumanBytes`** defines methods for human-readable byte formatting. 
- **`TimeSpec`** calculates time specification conversion factors, especially to support `datetime` library operations.

#### Exception Logic Classes

In some cases, it can be useful to write patterns that apply `if-then` logic or iterative `for`/`while` logic to exception handling. One example is, "If code block 1 raises an exception, then try code block 2; if block 2 raises an exception, then try block 3; ... then try block `n`." The following classes support this pattern: 

- **`SkipException`**: Custom exception for skipping operations
- **`ErrCatcher`**: Base exception catcher
- **`IgnoreExceptions`**: Context manager for ignoring exceptions
- **`SkipOrNot`**: Abstract base for skip/don't skip logic
- **`Skip`**: Skip exceptions in context
- **`DontSkip`**: Don't skip exceptions in context
- **`KeepSkippingExceptions`**: Keep trying until no errors
- **`KeepTryingUntilNoErrors`**: Retry operations until success

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

Typically, there are better ways to implement (or avoid) this and similar patterns. However, *if* it is needed, then I like having a easy and concise-but-readable way to write it in a pinch.

The `IgnoreExceptions` class functions as shorthand for `try`/`except` blocks like this:

```python
try:
    ...  # code block
except ERR_TYPES:
    pass
```

The equivalent would be a code block nested under the line `with IgnoreExceptions(ERR_TYPES):`. I may rename the class, because it doesn't truly *ignore* exceptions; it skips the code blocks that raise them.

#### Iterator and Comparison Base Classes

These classes provide general reusable functionality used later by the `Corer` class in `gconanpy/dissectors.py`.

- **`IteratorFactory`** is a base class providing iterator creation methods.
- **`Comparer`** is a base class providing value comparison methods.

### `typeshed.py`

`meta/typeshed.py` includes custom type classes, especially protocols and abstract base classes, to support type hinting. Many of them are defined only for type hints to indicate that an object has a specific method or attribute.

- `Boolable` means "supports `bool(x)`"
- `BytesOrStr` means "`bytes | str | bytearray`"
- `Poppable` means "supports `x.pop()`"
- `Updatable` means "supports `x.update(...)`"
- `HasClass` means "has a `__class__` attribute"
- `HasSlots` means "has a `__slots__` attribute"

A few more complicated examples subclass existing types, but *exclude* others. They specify that an object "is an X, but not a Y."

- `PureIterable` means "`Iterable`, but not `str`, `bytes`, or `Mapping`."
- `NonTxtCollection` means "`Collection`, but not `str` or `bytes`."

Others combine class-checking and method-checking:

- `AddableSequence` means "`Sequence` that supports `+` (`__add__`)"

#### Usage Examples

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

# Format bytes readably
formatted = HumanBytes.format(1024 * 1024)  # -> "1.0 MB"
```

### `metaclass.py`

Metaclass creation utilities and advanced type checking.

#### Key Functions

- **`name_type_class`**: Create type-checking metaclass
- **`combinations_of_conditions`**: Generate combinations of conditions

#### Key Classes

- **`MakeMetaclass`**: Factory for creating custom metaclasses
- **`MatcherBase`**: Base class for `combinations_of_conditions`
- **`NonIterable`**: Metaclass for non-iterable types
- **`TypeFactory`**: Factory for creating type-checking metaclasses

**Usage Examples**:
```python
from gconanpy.meta.metaclass import MakeMetaclass

# Create metaclass for objects with specific methods
SupportsSave = MakeMetaclass.for_methods("save", include=True)

# Create metaclass for specific types
IsStringOrInt = MakeMetaclass.for_classes(is_all_of=(str, int),
                                          name="StringOrInt")
```

## Use Case Examples

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

### Exception Logic Patterns

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

### Type Checking

```python
from gconanpy.meta import Boolable, NonTxtCollection

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

### Graceful Error Handling

```python
from gconanpy.meta import IgnoreExceptions, KeepTryingUntilNoErrors

def robust_operation():
    with KeepTryingUntilNoErrors(ConnectionError):
        with IgnoreExceptions(AttributeError):
            # Try to access optional attributes
            result = obj.optional_method()
            return result
        return None
```

### Inspecting Objects

```python
from gconanpy.meta import name_of, names_of

def log_objects(*objects):
    names = names_of(objects)
    for obj, name in zip(objects, names):
        print(f"Processing {name}: {obj}")
```

## Error Handling

The `meta` module provides sophisticated error handling:
- Custom exception types for specific scenarios
- Context managers for exception suppression
- Retry mechanisms with configurable conditions
- Type-safe operations with fallbacks

## Best Practices

- Use metaclasses sparingly and document their purpose clearly
- Implement proper error handling with specific exception types
- Use type checking for runtime safety
- Consider performance implications of meta-programming
- Follow Python's type hinting conventions
- Use context managers for resource management 

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-11-03
- Current as of `v0.22.0`

### License

This free and open-source software is released into the public domain.