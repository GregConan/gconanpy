# GConanPy

## Introduction

### Overview

`gconanpy` is a Python library providing data manipulation and debugging utilities for Python development, written to centralize the basic and lower-level Python tools that I reuse across multiple projects. I intend my projects to import these tools to prevent redundancy. 

The `gconanpy` package contains a collection of tools designed to simplify common programming tasks, streamline interactive debugging, and provide convenient ways to access and manipulate data. 

## Dependencies and Requirements

### Python Libraries

`gconanpy` uses [Python-Poetry](https://python-poetry.org/) for dependency management.

- `bs4` (BeautifulSoup): HTML/XML parsing
- `cryptography`: Encryption capabilities
- `inflection`: String manipulation
- `more_itertools`: Advanced iteration utilities
- `numpy`: Numerical operations
- `pandas`: Data analysis
- `pathvalidate`: File path validation
- `regex`: Advanced Regex pattern matching
- `requests`: HTTP operations
- `pytest`: Testing framework

See `pyproject.toml` for full list of dependencies and version requirements.

## Installation

```bash
pip install poetry
git clone https://github.com/GregConan/gconanpy.git
cd gconanpy
poetry install
```

## File Structure

### `gconanpy/`

The main package containing utility modules for Python development:

- **`bytesify.py`**: Conversion to/from bytes and encryption
- **`debug.py`**: Interactive debugging aids
- **`extend.py`**: Class and function extension utilities
- **`numpandas.py`**: NumPy/Pandas integration
- **`reg.py`**: Regular expression utilities and text parsing
- **`testers.py`**: Base testing framework
- **`trivial.py`**: Trivially simple utility functions
- **`wrappers.py`**: Class wrapping and string conversion utilities

#### `access/`

Object attribute and item access utilities for enhanced data manipulation.

- **`__init__.py`**: Unified interface(s) for low-level access and manipulation of items and attributes interchangeably
- **`access/attributes.py`**: Dynamic attribute access and manipulation utilities
- **`access/dissectors.py`**: Data structure inspection and debugging tools
- **`access/find.py`**: Classes and functions for finding items in iterables with early termination.

#### **`IO/`**

Web and local file system operations.

- **`IO/local.py`**: File loading and saving utilities.
- **`IO/web.py`**: Web document fetching and parsing utilities.

#### **`iters/`**

Advanced iteration utilities and collection manipulation.

- **`iters/__init__.py`**: Core iteration utilities and collection manipulation functions.
- **`iters/duck.py`**: Duck typing interface for collections with unified access patterns.
- **`iters/filters.py`**: Filter classes for data selection.

#### **`mapping/`**

Dictionary utilities and custom dictionary classes.

- **`mapping/__init__.py`** Standalone utility functions replicating the dictionary operations in `mapping/dicts.py` for general use
- **`mapping/dicts.py`**:  Custom dictionary classes with specialized functionality for a variety of use cases
- **`mapping/grids.py`**: Multidimensional custom dictionary classes.

#### **`meta/`**

Core utilities, meta-programming, and type-checking.

- **`meta/__init__.py`**: Core utilities and type-checking functionality.
- **`meta/metaclass.py`**: Metaclass creation utilities and advanced type checking. 
- **`meta/typeshed.py`**: Custom type classes.

### `tests/`

Comprehensive test suite for all modules:

- **`test_*.py`**: Individual test files for each module.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-19
- Current as of `v0.15.1`

### License

This free and open-source software is released into the public domain.
