# Iters

Advanced iteration utilities and `Collection` manipulation tools.

## Overview

Utilities for manipulating `Iterable` objects, especially nested ones. The `iters` module includes operations to find elements in `Iterables`, sequence manipulation, and advanced iteration patterns. This module serves as the foundation for many higher-level operations in the `gconanpy` library.

## Dependencies

- `more_itertools`: For advanced iteration utilities
- `numpy`: For numerical array operations
- `pandas`: For DataFrame operations
- Standard library modules: `collections.abc`, `itertools`, `typing`

## Modules

### `__init__.py`

Core iteration and manipulation utilities. Includes functions to combine, compare, copy, inspect, iterate, and transform `Iterable` and `Collection` data containers. Also includes highly useful classes extending builtin functionality for data generation (e.g. `Randoms`) and filtering (e.g. `Combinations`).

#### Key Classes

- `Randoms` randomly selects and/or randomly generates data. Useful for testing.
- `MapSubset` filters and extracts subsets of `Mapping` objects.
- `SimpleShredder` recursively collects values from nested structures.
- `Combinations` generates various combinations of data containers.
- `IterableMap` is a base class for `Mapping`-like iteration.
- `MapWalker` recursively iterates over nested `Mapping` objects.

### `duck.py`

Duck typing interface for unified `Collection` access patterns: the `DuckCollection` class. It can access and modify any `Collection` without knowing its exact type.

Following the Pythonic principle of "duck typing," `DuckCollection` is inspired by the adage "If it looks like a duck, and it quacks like a duck, then it's a duck." Paradoxically, most of the `DuckCollection`'s implementation relies on type checking, which may limit its applicability.

The intended use case is for functions/methods that do not need to know what type of `Collection` they are accessing/modifying, only that they are accessing/modifying *a* `Collection`.

#### Key Features

- Unified interface for lists, sets, dictionaries, and other `Collections`
- Automatic method selection based on `Collection` type
- Support for immutable `Collection`s like tuples and strings

### `find.py`

Classes and functions for finding items in iterables with early termination.

I initially wrote these to answer the question, "Is it reasonably possible to never `break` (or `return`) out of a `for` loop in Python?" Because the widely accepted answer is "no," some of these classes may be superfluous.

**Key Classes**:

- `BasicRange` is a base class for custom range-like iterators to add functionality.
- `ErrIterChecker` is like `ReadyChecker`, but its satisfaction condition is no exceptions being raised.
- `ReadyChecker` is a context manager to replicate functionality interrupting `for` loops upon satisfaction of a given condition, like `for ... if ... break` and `for ... if ... return`, without using a `for` loop or a `break` clause. It may be superfluous.
- `Spliterator` splits and recombines strings iteratively until satisfaction of a condition.
- `UntilFound` calls a function on each item in an iterable until one of them returns a result satisfying a specified condition.

## Usage Examples

### Duck Typing with Collections

Adding the same item to different types of `Collections`: 

```python
from gconanpy.iters.duck import DuckCollection

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
from gconanpy.iters.duck import DuckCollection

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

### Advanced Iteration Patterns

```python
from gconanpy.iters import MapWalker, SimpleShredder

# Walk nested mappings
nested_data = {"a": {"b": {"c": 1}}, "d": {"e": 2}}
walker = MapWalker(nested_data)
for key, mapping in walker.items():
    print(f"Key: {key}, Mapping: {mapping}")

# Extract all data from nested structure
shredder = SimpleShredder()
nums = shredder.shred(nested_data) # -> {1, 2}
```

### Sequence Manipulation
```python
from gconanpy.iters.seq import uniqs_in, seq_startswith

# Get unique items
unique_items = uniqs_in([1, 2, 2, 3, 1, 3, 3, 2])  # -> [1, 2, 3]

# Check sequence prefix
starts_with = seq_startswith([1, 2, 3, 4], [1, 2])  # -> True
```

### Random Data Generation

Below are very basic examples of generating random data using the `Randoms` class. For additional usage examples, see the files in the `tests/` directory. Most of them use `Randoms` to generate arbitrary test data covering a variety of types and possible values.

```python
from gconanpy.iters import Randoms

# Generate test data
random_dict = Randoms.randict(min_len=3, max_len=5)
random_ints = list(Randoms.randints(min_n=5, max_n=10))
random_sets = Randoms.randintsets(min_n=2, max_n=3)
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Updated by @[GregConan](https://github.com/GregConan) on 2025-10-11
- Current as of `v0.21.6`

### License

This free and open-source software is released into the public domain.