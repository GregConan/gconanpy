# Tests

Comprehensive test suite for the `gconanpy` library.

## Overview

The `tests` directory contains the complete test suite for the `gconanpy` library, including unit tests, integration tests, and test utilities. Each test file corresponds to a specific module in the main library (although this correspondence needs to be updated) and provides comprehensive coverage of functionality.

## Test Files

### `test_dicts.py`

Tests for the mapping/dictionary classes and utilities.

#### Test Coverage

- `Cryptionary` class encryption/decryption
- `Defaultionary` class with extended defaults
- `DotDict` class dot notation item access and modification
- `Invertionary` class inversion capabilities
- `LazyDict` class lazy loading
- `Promptionary` class interactive prompting
- `Sortionary` class sorting functionality
- `Subsetionary` class subset operations
- `Updationary` class update methods
- `Walktionary` class walking capabilities
- Advanced dictionary combinations

#### `test_dissectors.py`

Tests for data structure inspection and analysis utilities.

#### Test Coverage

- `Corer` class item extraction
- `DifferenceBetween` class object comparison
- `Peeler` class item extraction
- `Shredder` class recursive data collection
- `Xray` class deep inspection

#### Key Test Areas

- Object comparison and difference detection
- Nested data structure traversal
- Statistical analysis of collections
- Debug-friendly object inspection
- Error handling for complex structures

#### `test_IO.py`

Tests for Input/Output utilities.

#### Test Coverage

- Web I/O operations (`web.py`)
- Local file operations (`local.py`)
- URL parsing and manipulation
- File reading and writing
- Template loading and processing

#### `test_meta.py`

Tests for meta-programming utilities and type checking.

#### Test Coverage

- Meta-programming functions
- Type checking utilities
- Exception handling classes
- Iterator and comparison utilities
- Metaclass creation tools

#### Key Test Areas

- Method availability checking
- Object name and type utilities
- Exception handling patterns
- Type checking mechanisms
- Metaclass functionality
- Lazy access patterns

#### `test_reg.py`

Tests for regular expression utilities.

#### Test Coverage

- `Regextract` class pattern extraction
- `DunderParser` class name parsing
- Regex pattern matching
- String manipulation utilities

#### Key Test Areas

- Pattern extraction and matching
- Dunder method name parsing
- Regex compilation and execution
- Error handling for invalid patterns

#### `test_seq.py`

Tests for sequence manipulation utilities.

#### Test Coverage

- `Sequence` processing functions
- Unique item detection
- `Sequence` transformation utilities

#### Key Test Areas

- `Sequence` iteration and processing
- Unique element identification
- `Sequence` transformation operations
- Error handling for `Sequence` operations

#### `test_ToString.py`

Tests for the `ToString` wrapper class.

#### Test Coverage

- String conversion from various types
- Formatting and quotation options
- Tree structure stringification
- `datetime` string conversion
- `Iterable` and `Mapping` stringification

#### Key Test Areas

- Object to string conversion
- Custom formatting options
- Tree structure visualization
- `datetime` formatting
- `Collection` stringification
- Error handling for conversion

#### `test_find.py`

Tests for search and finder utilities.

#### Test Coverage

- Finding utilities for complex structures
- Pattern matching functionality

#### Key Test Areas

- Search accuracy
- Pattern matching performance
- Complex structure traversal
- Error handling for search operations

#### `test_extend.py`

Tests for subclass extension utilities.

#### Test Coverage

- Class extension functionality
- Enhancement utilities
- Extension pattern implementations

#### Key Test Areas

- Object extension mechanisms
- Class enhancement utilities
- Extension pattern validation
- Error handling for extensions

## Test Structure

### Organization

- Each test file corresponds to a main library module
- Tests are organized by functionality
- Edge case and error condition testing

### Test Patterns

- Unit tests for individual functions and classes
- Integration tests for module interactions
- Error handling and exception testing
- Performance testing

### Test Data

- Sample files for I/O testing
- Mock objects for complex scenarios
- Generated test data for comprehensive coverage
- Edge case data for robustness testing

## Running Tests

I use the integrated Cursor and VS Code `pytest` extensions for automated unit testing of the `gconanpy` library using these files. However, the tests can be run directly from the command line.

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_dicts.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=gconanpy
```

## Issues

TODO:

- Reorganize test files to restore 1-to-1 correspondence with `.py` files in `gconanpy/` directory.
- Add explanatory comments and docstrings to ensure that all methods of all tester classes are well-documented.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Current as of `v0.13.2`

### License

This free and open-source software is released into the public domain.