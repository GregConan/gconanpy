# Iters

Advanced iteration utilities and `Collection` manipulation tools.

## Overview

The `iters` module provides comprehensive utilities for manipulating `Iterable` objects, especially nested ones. It includes specialized classes for duck typing, operations to find elements in `Iterables`, sequence manipulation, and advanced iteration patterns. This module serves as the foundation for many higher-level operations in the `gconanpy` library.

## Dependencies

- `more_itertools`: For advanced iteration utilities
- `numpy`: For numerical array operations
- `pandas`: For DataFrame operations
- Standard library modules: `collections.abc`, `itertools`, `typing`

## Modules

### `__init__.py`

Core iteration utilities and collection manipulation functions.

#### Key Classes

- `Bytesifier` convert objects to bytes with error handling.
- `Randoms` generates random data for testing and development.
- `MapSubset` filters and extracts subsets from `Mapping` objects.
- `SimpleShredder` recursively collects values from nested structures.
- `Combinations` generates various combinations of data.
- `IterableMap` is a base class for `Mapping`-like iteration.
- `MapWalker` recursively iterates over nested `Mapping` objects.

### `duck.py`

Duck typing interface for collections with unified access patterns. This file is for one class: the `DuckCollection` interface. It can access and modify any `Collection` without knowing its exact type.

Following the Pythonic principle of "duck typing," `DuckCollection` is inspired by the adage "If it looks like a duck, and it quacks like a duck, then it's a duck." Paradoxically, most of the `DuckCollection`'s implementation relies on type checking, which may limit its applicability.

The intended use case is for functions/methods that do not need to know what type of `Collection` they are accessing/modifying, only that they are accessing/modifying *a* `Collection`.

#### Key Features

- Unified interface for lists, sets, dictionaries, and other collections
- Automatic method selection based on collection type
- Support for immutable collections (tuples, strings)

### `find.py`

Classes and functions for finding items in iterables with early termination.

I initially wrote these to answer the question, "Is it reasonably possible to never `break` (or `return`) out of a `for` loop in Python?" Because the widely accepted answer is "no" or "why," some of these classes may be superfluous.

**Key Classes**:

- `BasicRange` is a base class for custom range-like iterators to add functionality.
- `ErrIterChecker` is like `ReadyChecker`, but its satisfaction condition is no exceptions being raised.
- `ReadyChecker` is a context manager to replicate functionality interrupting `for` loops upon satisfaction of a given condition, like `for ... if ... break` and `for ... if ... return`, without using a `for` loop. It may be superfluous.
- `Spliterator` splits and recombines strings iteratively until satisfaction of a condition.
- `UntilFound` calls a function on each item in an iterable until one of them returns a result satisfying a specified condition.

### `seq.py`

`Sequence` manipulation functions and NumPy/Pandas integration.

## Usage Examples

### Duck Typing with Collections

Adding the same item to different types of `Collections`: 

```python
from gconanpy.iters.duck import DuckCollection

# Work with any collection type
list_collection = DuckCollection([1, 2, 3])
set_collection = DuckCollection({1, 2, 3})
dict_collection = DuckCollection({1: "a", 2: "b", 3: "c"})

# Same basic operations work across different types
for ducks in [list_collection, set_collection, dict_collection]:
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

### Finding Items in Iterables

```python
from gconanpy.iters.find import iterfind, modifind

# Find first item matching condition
numbers = [1, 2, 3, 4, 5]
first_even = iterfind(numbers, lambda x: x % 2 == 0)  # 2

# Find item after modification
def double(x): return x * 2
first_large = modifind(numbers, modify=double, found_if=lambda x: x > 6)  # 4
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
all_data = shredder.shred(complex_nested_object)
```

### Sequence Manipulation
```python
from gconanpy.iters.seq import uniqs_in, seq_startswith

# Get unique items
unique_items = uniqs_in([1, 2, 2, 3, 3, 3])  # [1, 2, 3]

# Check sequence prefix
starts_with = seq_startswith([1, 2, 3, 4], [1, 2])  # True
```

### Random Data Generation

Below is a basic example of generating random data using the `Randoms` class. For additional usage examples, see the files in the `tests/` directory.

```python
from gconanpy.iters import Randoms

# Generate test data
random_dict = Randoms.randict(min_len=3, max_len=5)
random_ints = list(Randoms.randints(min_n=5, max_n=10))
random_sets = Randoms.randintsets(min_n=2, max_n=3)
```

## Advanced Features

All classes have the following beneficial features.

### Type-Safe Operations

Proper type hints and generic types for type safety:

- `DuckCollection` for type-safe collection operations
- `MapSubset` with configurable key and value types
- `Combinations` with hashable type constraints

### Error Handling

Comprehensive error handling throughout:

- `SimpleShredder` handles various data types gracefully
- `ErrIterChecker` provides exception-safe iteration
- `DuckCollection` raises appropriate exceptions for unsupported operations

### Performance Optimizations

- Lazy evaluation in `MapWalker` and `Combinations`
- Efficient traversal tracking in `SimpleShredder`
- Optimized NumPy operations in `seq.py`

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Current as of `v0.13.2`

### License

This free and open-source software is released into the public domain.