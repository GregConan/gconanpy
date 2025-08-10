# `GConanPy`

## Overview

`gconanpy` is a Python library providing data manipulation and debugging utilities for Python development. The `gconanpy` package contains a collection of tools designed to simplify common programming tasks, streamline interactive debugging, and provide convenient ways to access and manipulate data. 

## Dependencies

This package requires the following dependencies:
- `bs4` (BeautifulSoup)
- `cryptography`
- `more_itertools`
- `pathvalidate`
- `requests`

## Modules

### `attributes.py`

Dynamically access and modify object attributes. Replicates certain `dict` methods, and certain `gconanpy.mapping` functions, for accessing/modifying attributes instead of elements/items.

#### Key Classes

- **`AttrsOf`**: Comprehensive attribute access and manipulation class
- **`Filter`**: Configurable filter for selecting specific attributes by name and value

### `wrappers.py`

Classes that wrap other classes to provide additional functionality.

#### Key Classes

- **`ClassWrapper`** is a base class for wrapping/subclassing other classes to add functionality.
- **`ToString`** is an enhanced `str` subclass with advanced formatting and conversion methods.
- **`BasicTree`** visually represents hierarchical tree data structures with pretty-printing.
- **`SoupTree`** visually represents `BeautifulSoup` objects as a tree.
- **`WrapFunction`** wraps functions with pre-defined parameters. It enhances `functools.partial` by allowing more specific positional parameter placement.
- **`Valid`** provides command-line argument validation tools to supplement `argparse`.
- **`ArgParser`** enhances `argparse.ArgumentParser` by adding default options for output directory arguments.

#### Key Features

- Specify string representation of various data types (`Collection`, `Mapping`, `datetime`, etc.)
- Tree structure visualization with customizable branches
- Function wrapping with parameter preservation
- Command-line input validation for file paths, directories, and numbers

### `dissectors.py`

Classes to inspect, examine, and access complex/nested data structures without already knowing their internal structure. Useful for interactive debugging.

#### Key Classes

- **`Corer`** can find the largest (or smallest) item in a nested data structure.
- **`DifferenceBetween`** identifies what makes any given Python objects differ from each other.
- **`Peeler`** removes unneeded outermost layers of nested containers.
- **`Shredder`** can "flatten" a nested container, extracting every contained value regardless of how deeply it is nested. It adds filtering capabilities to `gconanpy.iters.SimpleShredder`.
- **`Xray`** can list the attributes, keys, or outputs of any given Python object.

#### Key Features

- Object comparison with detailed difference reporting
- Recursive data extraction from complex structures
- Debug-friendly object inspection

### `reg.py`

Regular expression utilities and pattern matching tools.

#### Key Classes

- **`Regextract`** provides enhanced Regex data extraction with several pre-defined patterns.
- **`DunderParser`** can parse and manipulate Python "magic method"/"dunder method" names.

### `debug.py`

Debugging utilities and tools primarily to aid/ease interactive debugging during development.

#### Key Classes

- **`Debuggable`** is a base mixin class for objects with debugging capabilities.
- **`ShowTimeTaken`** provides basic timing functionality as a context manager, like `timeit` that uses existing code instead of accepting the code as string inputs.

#### `extend.py`

Extension utilities for subclassing existing classes.

#### `testers.py`

Classes for use in automated unit testing, especially using `pytest`. For use cases, see the `tests/test_*.py` files.

#### `trivial.py`

Basic/trivial functions to use as default values of optional callable parameters in other classes' methods.

## Usage Examples

### Attribute Manipulation
```python
from gconanpy.attributes import AttrsOf

# Get all public attributes of an object
attrs = AttrsOf(my_object)
public_attrs = attrs.public()

# Add attributes to an object
from gconanpy.attributes import add_to
obj = add_to(my_object, new_attr="value", another_attr=123)
```

### String Conversion
```python
from gconanpy.wrappers import ToString

# Convert any object to string
string_repr = ToString.fromAny(my_complex_object)

# Convert datetime with custom formatting
from datetime import datetime
dt_string = ToString.fromDateTime(datetime.now(), sep="_")
```

### Data Structure Analysis
```python
from gconanpy.dissectors import DifferenceBetween, Shredder

# Compare objects and find differences
diff = DifferenceBetween(obj1, obj2, obj3)
if diff.is_different:
    print(f"Differences: {diff.difference}")

# Extract all data from nested structure
shredder = Shredder()
all_data = shredder.shred(complex_nested_object)
```

### Iterable Manipulation
```python
from gconanpy.iters import are_all_equal, merge

# Check if all items are equal
if are_all_equal(my_list):
    print("All items are identical")

# Merge multiple dictionaries
merged = merge([dict1, dict2, dict3])
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Current as of `v0.13.2`

### License

This free and open-source software is released into the public domain.