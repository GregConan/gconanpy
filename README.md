# GConanPy

## Overview

`gconanpy` is a Python library providing data manipulation and debugging utilities for Python development, written to centralize the basic and lower-level Python tools that I reuse across multiple projects. I intend my projects to import these tools to prevent redundancy. 

The `gconanpy` package contains a collection of tools designed to simplify common programming tasks, streamline interactive debugging, and provide convenient ways to access and manipulate data. 

## Installation

```bash
pip install poetry
git clone https://github.com/GregConan/gconanpy.git ./gconanpy
cd gconanpy
poetry install
```

## Dependencies and Requirements

### Python Libraries

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

## File Structure

For more details, see the `README.md` file in each subdirectory.

### `gconanpy/`

The main package contains utility modules for Python development:

#### Subdirectories

- `access/`: Object attribute and item access utilities for enhanced data manipulation.
- `collection/`: Unified interface for polymorphic `Collection` accessor and mutator functions.
- `IO/`: Web and local file system operations.
- `iters/`: Advanced iteration utilities and Collection manipulation.
- `mapping/`: Mapping utilities and custom dictionary-like classes.
- `meta/`: Core utilities, meta-programming, and type-checking.

#### Files

- `bytesify.py`: Encryption and conversion to/from bytes.
- `debug.py`: Interactive debugging aids.
- `extend.py`: Class and function extension utilities.
- `numpandas.py`: NumPy/Pandas integration.
- `reg.py`: Regular expression utilities and text parsing.
- `testers.py`: Base PyTest testing framework.
- `trivial.py`: Trivially simple utility functions.
- `wrappers.py`: Class wrapping and string conversion utilities.

### `tests/`

Comprehensive PyTest testing suite for all modules:

- `test_*.py`: Individual test files for each module.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
