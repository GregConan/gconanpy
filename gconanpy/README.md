# GConanPy

## Overview

`gconanpy` is a Python library providing data manipulation and debugging utilities for Python development, written to centralize the basic and lower-level Python tools that I reuse across multiple projects. I intend my projects to import these tools to prevent redundancy. 

The `gconanpy` package contains a collection of tools designed to simplify common programming tasks, streamline interactive debugging, and provide convenient ways to access and manipulate data. 

## Dependencies

`gconanpy` uses [Python-Poetry](https://python-poetry.org/) for dependency management, and uses the following libraries:

- [bs4](https://beautiful-soup-4.readthedocs.io/en/latest/) (BeautifulSoup): HTML/XML parsing
- [cryptography](https://cryptography.io/en/latest/): Encryption capabilities
- [html-to-markdown](https://pypi.org/project/html-to-markdown/): HTML to Markdown conversion
- [inflection](https://inflection.readthedocs.io/en/latest/): String manipulation and case conversion
- [makefun](https://smarie.github.io/python-makefun/): Dynamic function creation with signatures
- [more-itertools](https://more-itertools.readthedocs.io/en/stable/): Advanced iteration utilities
- [numpy](https://numpy.org/doc/stable/): Numerical operations
- [pandas](https://pandas.pydata.org/docs/): Data analysis
- [pathvalidate](https://pathvalidate.readthedocs.io/en/latest/): File path validation
- [pydantic](https://docs.pydantic.dev/latest/): Data validation and settings management
- [pympler](https://pympler.readthedocs.io/en/latest/): Memory profiling
- [pytest](https://docs.pytest.org/en/stable/): Testing framework
- [regex](https://github.com/mrabarnett/mrab-regex): Advanced Regex pattern matching
- [requests](https://requests.readthedocs.io/en/latest/): HTTP operations

See `pyproject.toml` for full list of dependencies and version requirements.

## Modules

For more details, see the `README.md` file in each subdirectory.

### `gconanpy/`

The main package containing utility modules for Python development:

- `bytesify.py`: Conversion to/from bytes and encryption
- `cli.py`: Command-line argument parsing and validation utilities
- `debug.py`: Interactive debugging aids
- `extend.py`: Class and function extension utilities
- `numpandas.py`: NumPy/Pandas integration
- `reg.py`: Regular expression utilities and text parsing
- `strings.py`: Enhanced string handling, formatting, and case conversion
- `testers.py`: Base testing framework
- `trivial.py`: Trivially simple utility functions
- `wrappers.py`: Class wrapping, tree visualization, and tuple-based collection utilities

#### `access/`

Object attribute and item access utilities for enhanced data manipulation.

- `access/__init__.py`: Unified interface(s) for low-level access and manipulation of items and attributes polymorphically/interchangeably.
- `access/attributes.py`: Dynamic attribute access and manipulation utilities.
- `access/find.py`: Classes and functions with early termination for finding items in iterables.
- `access/nested.py`: Data structure inspection tools. Useful for interactive debugging.

#### `collection/`

Unified interface for polymorphic `Collection` accessor and mutator functions.

- `collection/__init__.py`: Accessor/mutator functions that work on lists, sets, and dicts polymorphically/type-agnostically.
- `collection/classes.py`: Duck typing interface providing unified access patterns for collections.

#### `IO/`

Web and local file system operations.

- `IO/local.py`: File loading and saving utilities.
- `IO/web.py`: Web document fetching and parsing utilities.

#### `iters/`

Advanced iteration utilities and collection manipulation.

- `iters/__init__.py`: Core iteration utilities and collection manipulation functions.
- `iters/filters.py`: Filter classes for data selection.

#### `mapping/`

Mapping utilities and custom dictionary-like classes.

- `mapping/__init__.py`: Standalone utility functions replicating the dictionary operations in `mapping/dicts.py` for general use.
- `mapping/attrmap.py`: Basic `MutableMapping` classes that store items as attributes for simple dot notation access.
- `mapping/bases.py`: Custom `Mapping` base classes inherited by classes in `dicts.py` and `attrmap.py`.
- `mapping/dicts.py`: Custom dictionary classes with specialized functionality for a variety of use cases.
- `mapping/grids.py`: Multidimensional custom dictionary classes. In progress.

#### `meta/`

Core utilities, meta-programming, and type-checking.

- `meta/__init__.py`: Core utilities and type-checking functionality.
- `meta/metaclass.py`: Metaclass creation utilities and advanced type checking. 
- `meta/typeshed.py`: Custom type classes.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
