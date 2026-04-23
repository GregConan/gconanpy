# Collection

## Overview

Unified polymorphic interface for `Collection` accessor and mutator functions. The intended use case is for functions/methods that do not need to know what type of `Collection` they are accessing/modifying, only that they are accessing/modifying *a* `Collection`.

The `collection` module provides polymorphic operations on `Collection` objects (especially `list`, `set`, and `dict`) using `functools.singledispatch` to automatically select the appropriate method based on the `Collection` type. It also includes the `DuckCollection` class, named after duck typing, for object-oriented polymorphic collection manipulation by wrapping any `Collection`.

## Dependencies

- [more-itertools](https://more-itertools.readthedocs.io/en/stable/): Advanced iteration utilities

## Modules

### `__init__.py`

Accessor/mutator functions that work on lists, sets, and dicts polymorphically via `functools.singledispatch`.

- `add`: Add an element to a `MutableSequence`, `set`, or `MutableMapping`.
- `combine`: Combine multiple `Collection`s into one (union for sets, concatenation for lists, merge for dicts).
- `delete`: Remove an element from a `MutableSet`, `MutableSequence`, or `MutableMapping`.
- `difference`: Return elements in the first `Collection` but not in the others.
- `difference_update`: Remove all elements of other `Iterable`s from the first `Collection` in place.
- `discard`: Remove an element if present; do nothing if not.
- `extend`: Extend a `Collection` by adding elements from an iterable.
- `intersect`: Return elements common to all `Collection`s.
- `intersection`: Return the intersection of `Collection`s, preserving order for `Sequence`s.
- `intersection_update`: Update a `Collection` in place, keeping only elements found in all others.
- `isdisjoint`: Return True if two `Collection`s have no elements in common.
- `issubset`: Return True if all elements of the first `Collection` are in the second.
- `issuperset`: Return True if all elements of the second `Collection` are in the first.
- `symmetric_difference`: Return elements in either `Collection` but not both.
- `symmetric_difference_update`: Update a `Collection` in place with the symmetric difference.

### `classes.py`

Duck typing interface for unified `Collection` access patterns.

Following the Pythonic principle of "duck typing," `DuckCollection` is inspired by the adage "If it looks like a duck, and it quacks like a duck, then it's a duck." Paradoxically, most of the `DuckCollection`'s implementation relies on type checking, which may limit its applicability.

- `DuckCollection`: Interface to access and modify a `Collection` without knowing exactly what type of `Collection` it is. Provides unified `add`, `append`, `clear`, `copy`, `difference_update`, `discard`, `extend`, `get`, `index`, `insert`, `intersection`, `isdisjoint`, `pop`, `remove`, `replace`, and `set_to` methods.

## Usage Examples

### Type-Agnostic Collection Operations

```python
from gconanpy.collection import add, combine, difference, intersection

# Add elements to different collection types
my_list = [1, 2, 3]
add(my_list, 4)  # -> [1, 2, 3, 4]

my_set = {1, 2, 3}
add(my_set, 4)  # -> {1, 2, 3, 4}

# Combine collections
combined = combine(my_set, {4, 5})  # -> {1, 2, 3, 4, 5}
```

### Duck Typing with Collections

Adding the same item to different types of `Collections`: 

```python
from gconanpy.collection.classes import DuckCollection

# Work with various Collection types
nums_list = DuckCollection([1, 2, 3])
nums_set = DuckCollection({1, 2, 3})
nums_dict = DuckCollection({1: "a", 2: "b", 3: "c"})

# Same basic operations work across different types
for ducks in [nums_list, nums_set, nums_dict]:
    print(len(ducks))  # -> 3
    print(4 in ducks)  # -> False

    # Add an item to the Collection without knowing their types
    ducks.add(4, key="c")  # Uses list.append, set.add, or dict["c"]=...

    # Successfully modified different collections type-agnostically
    print(len(ducks))  # -> 4
    print(4 in ducks)  # -> True
```

```python
# Import standard libraries
from collections.abc import Collection
from typing import TypeVar

# Import custom libraries
from gconanpy.collection.classes import DuckCollection

C = TypeVar("C", bound=Collection)  # Return the same type of Collection
def add_msg_to(objects: C) -> C:
    """
    :param objects: Collection to append (or add) the string "hello world" to.
    :return: Collection, `objects` with the string "hello world" appended.
    """
    duckcol = DuckCollection(objects)
    duckcol.add("hello world")
    return duckcol.ducks

add_msg_to(["I", "said"])  # -> ["I", "said", "hello world"]
add_msg_to(("I", "said"))  # -> ("I", "said", "hello world")
add_msg_to({"I", "said"})  # -> {"hello world", "I", "said"}
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2026-04-17
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-17
- Current as of `v0.32.0`

### License

This free and open-source software is released into the public domain.
