# Tests

Unit test suite for the `gconanpy` library.

## Overview

The `tests` directory contains the complete test suite for the `gconanpy` library, including unit tests, integration tests, and test utilities. Each test file corresponds to a specific module in the 
main library and provides coverage of essential functionality. The Python files all validate library behavior through test classes.

### Organization

- Each test file corresponds to a main library module
- Tests are organized by functionality
- Edge case and error condition testing

## Dependencies

- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [pandas](https://pandas.pydata.org/docs/)
- [pydantic](https://docs.pydantic.dev/latest/)

## Modules

### `test_access.py`

Tests for `access/` utilities, combining coverage of the earlier attributes, finder, and nested/dissector files.

- `TestAccessSpeed`: Benchmarks selected access and traversal operations for relative performance.
- `TestAttributesFunctions`: Tests attribute filtering, selection, and introspection helpers defined in `access/attributes.py`.
- `TestAttrsOf`: Tests `AttrsOf` behavior, including method/variable and visibility distinctions.
- `TestCorers`: Tests nested item extraction behavior from `Corer` in `access/nested.py`.
- `TestDifferenceBetween`: Tests object comparison and difference detection behavior from `DifferenceBetween` class in `access/nested.py`.
- `TestIterFind`: Tests search behavior over iterables using the `iterfind` function in `access/find.py`.
- `TestModifind`: Tests matching behavior for modified search patterns using the `modifind` function in `access/find.py`.
- `TestReadyChecker`: Tests readiness-checking behavior used by `ReadyChecker` class in `access/find.py`.
- `TestShredders`: Tests recursive data collection and shredding behavior by the `Shredder` class in `access/nested.py` and the `SimpleShredder` class in `iters/__init__.py`.
- `TestSpliterator`: Tests string splitting/iteration behavior of the `Spliterator` class in `access/find.py`.
- `TestXray`: Tests the complex objects deep-inspection behavior of the `Xray` class in `access/nested.py`.  

### `test_cli.py`

Tests for CLI argument parsing and validation utilities.

- `CLIArgs`: Dummy `pydantic` model used as a typed fixture for CLI parser tests.
- `get_cli_args()`: Helper that builds parsed `CLIArgs` objects from argument strings.
- `TestArgumentParser`: Tests  the `ArgumentParser`, `Arg`, and `Valid` classes in `cli.py` plus output-directory argument handling.

### `test_collection.py`

Tests for collection classes and collection-level helper functionality.

- `TestDuckCollection`: Tests duck-typed collection behavior and related methods of the `DuckCollection` class in `collection/classes.py`.
- `TestCollectionFunctions`: Tests standalone collection utilities and combinational helper functions in `collection/__init__.py`.

### `test_extend.py`

Tests for class extension utilities.

- `TestExtend`: Tests dynamic extension behavior, especially the `weak_dataclass` function in `extend.py`.

### `test_iters.py`

Tests for iteration utilities and collection manipulation.

- `TestMapSubset`: Tests subset filtering and matching behavior for mappings using the `MapSubset` class in `iters/filters.py`.
- `TestMerge`: Tests merging and list-combination functions in `iters/__init__.py`, with time test benchmarking.
- `TestRandoms`: Tests random-data generation behavior from the `Randoms` class in `iters/__init__.py`.
- `TestRangeFunctions`: Tests range inversion function, and potentially related range/list functions, in `iters/__init__.py`.

### `test_mapping.py`

Tests for the mapping/dictionary classes and utilities.

- `DictTester`: Shared base tester for mapping-focused fixtures and assertions.
- `TestAttrMap`: Tests attribute-style mapping behavior of the `AttrMap` class and its variants in `mapping/attrmap.py`. Ensures that `AttrMap`s can replicate all needed `dict`-like functionality, including that of the `mapping/dicts.py` `CustomDict`s.
- `TestCryptionary`: Tests encryption/decryption mapping behavior of the `Cryptionary` class in `mapping/dicts.py`.
- `TestDictFunctions`: Tests basic uses and advanced combinations of the standalone mapping utility functions in `mapping/__init__.py`. 
- `TestAccessor`: Compares the speed of accessor functions and methods to benchmark their performance, especially of lazy accessors, using the `Accessor` class in `access/__init__.py`.
- `TestExcluDict`: Tests exclusionary/default-extending dictionary behavior of the `ExcluDict` class in `mapping/dicts.py`.
- `TestDotDicts`: Tests dot-notation key access and modification behavior of the `DotDict` class in `mapping/dicts.py`.
- `TestInvertionary`: Tests inversion behavior of the `Invertionary` class in `mapping/dicts.py`.
- `TestLazyDict`: Tests lazy-loading behavior of the `LazyDict` class in `mapping/dicts.py`.
- `TestMathDict`: Tests math-oriented dictionary operations and value transforms of the `MathDict` class in `mapping/dicts.py` and the `MathAttrMap` class in `mapping/attrmap.py`.
- `TestSortionary`: Tests sorting behavior of the `Sortionary` class in `mapping/dicts.py`.
- `TestUpdationary`: Tests update/merge-focused behavior of the `Updationary` class in `mapping/dicts.py`.
- `TestWalktionary`: Tests nested traversal and walking behavior of the `Walktionary` class in `mapping/dicts.py`.
- `TestOOPvsFunctions`: Compares the speed of object-oriented methods and mapping functions to benchmark their performance.

### `test_meta.py`

Tests for meta-programming utilities and type-checking behavior.

- `TestMetaClasses`: Tests metaclass creation, metaclass behavior, and related type machinery defined in `meta/typeshed.py` and `meta/metaclass.py`.
- `TestMetaFunctions`: Tests object name/type helpers and broader meta utility functions defined in `meta/*.py`.
- `TestRecursively`: Tests recursive type and structure utilities of the `Recursively` class in `meta/__init__.py`.

### `test_numpandas.py`

Tests for pandas-focused numeric/dataframe helper behavior. Incomplete as of `v0.32.3`.

- `TryFilterDFTester`: Tests dataframe filtering helpers, namely the `try_filter_df` function and `TryFilterDF` class defined in `numpandas.py`.

### `test_reg.py`

Tests for regular expression and parser utilities.

- `TestDunderParser`: Tests dunder-name parsing behavior of `DunderParser` class in `reg.py`.
- `TestRegextract`: Tests regex-based extraction and pattern matching behavior of `Regextract` class in `reg.py`.
- `TestAbbreviator`: Tests abbreviation and compact string-pattern behavior of `Abbreviator` and `Abbreviations` classes in `reg.py`.

### `test_strings.py`

Tests for string-formatting and string-conversion utilities.

- `TestFancyString`: Tests behavior, case/style conversions, and stringification helpers of `FancyString` class in `strings.py`.

### `test_wrappers.py`

Tests for wrapper and tree/URL utility classes defined in `wrappers.py`.

- `TestSets`: Tests behavior and functionality of the `Sets` wrapper class in `wrappers.py`.
- `TestSoupTree`: Tests BeautifulSoup tree representation behavior of the `SoupTree` class in `wrappers.py`.
- `TestURL`: Tests URL parsing/normalization behavior of the `URL` class defined in `IO/web.py`.

### `test_z_grids.py`

Tests for multi-dimensional "Grid" mapping structures. Named "z_grids.py" to ensure that when running all tests alphabetically, every other test can run before finishing the long-running `Locktionary` tests.

- `TestHashGrid`: Tests behavior of `HashGrid` class in `mapping/grids.py` and its subclasses, including mapping operations and encryption/"lock" behavior.

## Usage Examples

I use the integrated Cursor and VS Code `pytest` extensions for automated unit testing of the `gconanpy` library using these files. However, the tests can be run directly from the command line.

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_mapping.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=gconanpy
```

## Issues

TODO:

- Add explanatory comments and docstrings to all classes in tester files to ensure that all of their methods are well-documented.
- Ensure that every tester class is in the correct tester file corresponding to the module it is testing. For examlpe, move `TestAccessor` from `test_mapping.py` to `test_access.py`, and move the `TestURL` class from `test_wrappers.py` into a new `test_IO.py` file.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-29
- Current as of `v0.32.3`

### License

This free and open-source software is released into the public domain.