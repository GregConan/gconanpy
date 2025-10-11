# `GConanPy`

## Overview

`gconanpy` is a Python library providing data manipulation and debugging utilities for Python development. The `gconanpy` package contains a collection of tools designed to simplify common programming tasks, streamline interactive debugging, and provide convenient ways to access and manipulate data. 

## Dependencies

This package uses the following Python libraries:

- `bs4` (BeautifulSoup)
- `cryptography`
- `inflection`
- `more_itertools`
- `numpy`
- `pandas`
- `pathvalidate`
- `regex`

See `pyproject.toml` in the top-level directory for full list of dependencies and version requirements.

## Modules

### `access/`

Object attribute and item access utilities for enhanced data manipulation.

- **`__init__.py`**: Low-level utilities providing unified interfaces to access and manipulate items and attributes interchangeably.
- **`attributes.py`**: Dynamic attribute manipulation and introspection utilities including filtering, lazy access, and comprehensive object analysis.
- **`dissectors.py`**: Classes to inspect, traverse, examine, and compare complex/nested data structures without already knowing their internal structure. Very useful for interactive debugging.
- **`find.py`**: Search and finder utilities with early termination patterns, including with integrated string manipulation.

Several `access/` and `mapping/` files share several identically named access and manipulation functions/methods to provide the same functionality for different use cases:

- `access/attributes.py` for object attributes,
- `mapping/__init__.py` for any `Mapping`s, 
- `mapping/dicts.py` for custom `dict`s (object-oriented), and
- `access/__init__.py` for object attributes *or* `Collection` items.

### `wrappers.py`

Classes that wrap other classes to provide additional functionality. Includes enhanced string handling, tree visualization, function wrapping, and command-line argument validation utilities.

#### Key Classes

- **`ToString`** is an enhanced `str` subclass with advanced formatting and conversion methods.
- **`BasicTree`** visually represents hierarchical tree data structures with pretty-printing.
- **`SoupTree`** visually represents `BeautifulSoup` objects as a tree.
- **`WrapFunction`** wraps functions with pre-defined parameters. It enhances `functools.partial` by allowing more specific positional parameter placement.
- **`Valid`** provides command-line argument validation tools to supplement `argparse`.
- **`ArgParser`** enhances `argparse.ArgumentParser` by adding default options for output directory arguments.

### `iters/`

Advanced iteration utilities and `Collection` manipulation tools.

- **`__init__.py`**: Core iteration utilities and collection manipulation functions including equality checking, merging, filtering, and random data generation.
- **`duck.py`**: Duck typing interface for collections with unified access patterns, allowing type-agnostic collection manipulation.
- **`filters.py`**: Filter classes for data selection and manipulation with configurable name and value filtering capabilities.

### `mapping/`

Advanced dictionary utilities and custom dictionary classes.

- **`__init__.py`**: Standalone utility functions for dictionary operations including safe access, lazy loading, inversion, and nested lookups.
- **`dicts.py`**: Custom dictionary classes with specialized functionality including encryption, dot notation, lazy loading, prompting, and multidimensional mapping.
- **`grids.py`**: Multidimensional custom dictionary classes mapping *combinations* of specific numbers of keys to specific values. 

### `meta/`

Low-level utilities, custom types, and metaclass functionality.

#### Files

- **`__init__.py`**: Core utilities for meta-programming, type checking, exception handling, and object introspection with comprehensive type hint support.
- **`metaclass.py`**: Metaclass creation utilities and advanced type checking with factory classes for custom metaclass generation.

### `IO/`

Input/Output utilities for web requests and local file operations.

- **`local.py`**: Local file system operations including JSON handling, template loading, file copying, and directory traversal with validation.
- **`web.py`**: Web-based I/O operations including HTTP requests, URL parsing, and web content handling with enhanced URL and link manipulation.

### `bytesify.py`

Classes to convert objects to/from bytes. Byte conversion utilities with error handling, encryption support, and human-readable bytes formatting.

#### Key Classes

- **`Bytesifier`**: Convert various data types to bytes with error handling
- **`Encryptor`**: Encrypts data. Incomplete; may be removed.

### `debug.py`

Debugging utilities and tools primarily to aid/ease interactive debugging during development. Includes timing, memory profiling, and logging.

#### Key Classes

- **`Debuggable`** is a base mixin class for objects with debugging capabilities.
- **`ShowTimeTaken`** provides basic timing functionality as a context manager, like `timeit` that uses existing code instead of accepting the code as string inputs.

### `extend.py`

Extension utilities for subclassing existing classes and dynamic class creation. Dynamic class creation and extension utilities including annotation handling, module introspection, and class manipulation for advanced Python programming.

#### Key Functions

- **`all_annotations_of`**: Get all annotations from a class and its parents
- **`classes_in_module`**: Get all classes defined in a module
- **`extend_class`**: Extend existing classes with new functionality

### `testers.py`

Base classes for unit tests with common testing patterns, including some basic arbitrary test data. Also includes timing utilities. 

### `trivial.py`

Basic/trivial/simple functions to use as default values of optional callable parameters in other classes' methods.

### `reg.py`

Regular expression utilities and pattern matching tools including enhanced regex extraction and Python dunder method name parsing.

#### Key Classes

- **`Regextract`** provides enhanced Regex data extraction with several pre-defined patterns.
- **`DunderParser`** can parse and manipulate Python "magic method"/"dunder method" names.

### `numpandas.py`

Utility functions and classes to manipulate NumPy and Pandas data. NumPy and Pandas data manipulation utilities including DataFrame analysis, array searching, and data filtering operations.

## Usage Examples

### String Conversion
```python
from datetime import datetime
from gconanpy.wrappers import ToString

# Convert any object to string
string_repr = ToString.fromAny(my_complex_object)

# Convert datetime with custom formatting
dt_string = ToString.fromDateTime(datetime.now(), sep="_")
```

### NumPy/Pandas Operations
```python
from gconanpy.numpandas import count_uniqs_in_cols, nan_rows_in, search_sequence_numpy
import pandas as pd
import numpy as np

# Count unique values in DataFrame columns
df = pd.DataFrame({'A': [1, 2, 2, 3], 'B': ['x', 'y', 'y', 'z']})
unique_counts = count_uniqs_in_cols(df)

# Find rows with NaN values
nan_rows = nan_rows_in(df)

# Search for sequence in NumPy array
arr = np.array([1, 2, 3, 4, 5, 6])
subseq = np.array([3, 4, 5])
indices = search_sequence_numpy(arr, subseq)
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Current as of `v0.21.4`

### License

This free and open-source software is released into the public domain.