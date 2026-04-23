# Iters

## Overview

Utilities for manipulating `Iterable` objects, especially nested ones. The `iters` module includes operations to find elements in `Iterables`, sequence manipulation, and advanced iteration patterns. This module serves as the foundation for many higher-level operations in the `gconanpy` library.

## Dependencies

- [more-itertools](https://more-itertools.readthedocs.io/en/stable/): Advanced iteration utilities

## Modules

### `__init__.py`

Core iteration and manipulation utilities. Includes functions to combine, compare, copy, inspect, iterate, and transform `Iterable` and `Collection` data containers. Also includes highly useful classes extending builtin functionality for data generation (e.g. `Randoms`) and filtering (e.g. `Combinations`).

#### Functions

- `are_all_equal`: Check if all items in an iterable are equal, with optional custom comparison methods.
- `combine_lists`: Combine multiple lists into one.
- `copy_range`: Return a new copy of a `range` that has not been iterated yet.
- `deduplicate_keep_order`: Remove duplicate elements from a `Sequence` without changing order.
- `default_pop`: Pop an item from a collection, with a default value if the pop fails.
- `duplicates_in`: Return everything that appears more than once in a `Sequence`.
- `exhaust`: Exhaust an `Iterator` by iterating it until it has no values left.
- `exhaust_wrapper`: Wrap a generator function to exhaust it when called.
- `filter_sequence_generator`: `operator.itemgetter` for `Sequence`s yielded by `Generator`s.
- `has_any`: Check if an `Iterable` contains any of the specified items.
- `invert_range`: Return an inverted (reversed) copy of a `range`.
- `merge`: Merge dicts, sets, or any objects with an `update` method.
- `powers_of_ten`: Return a list of powers of 10 up to a specified order of magnitude.
- `seq_startswith`: Check if a `Sequence` starts with a given prefix.
- `seq_truncate`: Cut off the end of a `Sequence` if it exceeds a maximum length.
- `seq_rtruncate`: Cut off the beginning of a `Sequence` if it exceeds a maximum length.
- `subseq_indices`: Get the start and end indices of one `Sequence` within another.
- `startswith`: Type-agnostic extension of `str.startswith` and `bytes.startswith`.
- `uniqs_in`: List the unique elements of an iterable, sorted as strings.
- `update_return`: Update an `Updatable` with values from another and return it.

#### Classes

- `ColumnNamer`: Iterator that converts column numbers into their corresponding letter combinations in the manner used by Microsoft Excel.
- `Combinations`: Generate various combinations of data containers, including bools, objects, maps, and unique elements.
- `IterableMap`: Base class for a custom object to emulate `Mapping` iteration methods (`items`, `keys`, `values`).
- `MapWalker`: Recursively iterate over a `Mapping` and the `Mapping`s nested in it.
- `Randoms`: Various methods using the `random` library to randomly select or generate values. Useful for generating arbitrary test data.
- `SimpleShredder`: Recursively extract data from nested containers, collecting only hashable non-container data.

### `filters.py`

Classes to iterate and/or extract only certain elements of an iterable, those that are explicitly indicated or satisfy certain conditions.

- `BaseFilter`: Abstract base class for filter functionality shared by `Filter` and `MapSubset`.
- `Filter`: Filter and extract elements of an iterable based on their attribute names and/or values.
- `MapSubset`: Filter and extract subsets of `Mapping` objects based on key and/or value membership.

## Usage Examples

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
shredder.shred(nested_data) # -> {1, 2}
```

### Random Data Generation

Below are very basic examples of generating random data using the `Randoms` class. For additional usage examples, see the files in the `tests/` directory. Many of them use `Randoms` to generate arbitrary test data covering a variety of types and possible values.

```python
from gconanpy.iters import Randoms

# Generate test data
Randoms.randict(min_n=3, max_n=5)  # -> {327.8677066998597: 214, 'QISu42i#PPQ"fp>NN[1R\x0b4v1IxgbTy': 'I9yNs', 489.2352006242098: 'wjNEVf!wv)?u`&TI;#ITQrDiArt58f`0(4Gmqz}x?_^E\rMXqQ8Rqw'}
list(Randoms.randints(min_n=5, max_n=10))  # -> [-655847, 377589, -671636, 805760, 536369, -184018]
Randoms.randintsets(min_n=2, max_n=3)  # -> [{-1002332, -656475, -609401, 357575, -8920, -237622, -954293, -845683, -1031954, 1113233, 855826, 64406, 59323}, {-953464}]
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
