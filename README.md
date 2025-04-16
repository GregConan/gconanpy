# GConanPy

## Introduction

### Summary

Centralized repository containing the basic and lower-level Python tools that I reuse across multiple projects. I intend my projects to import from here to prevent redundancy.

## File Structure

### gconanpy/

#### cli.py

Functions and classes primarily to define, accept, and validate command-line input arguments.

#### debug.py

Functions and classes only needed to ease/aid debugging. Convenient and useful.

#### dissectors.py

Classes to inspect/examine/unwrap complex data structures. *Extremely* useful and convenient for debugging.

#### find.py

Classes and functions that iterate and break once they find what they're looking for. Like `dissectors.py`, useful to unwrap complex data structures.

#### io/

Functions and classes primarily to import data from, and export data to...

##### local.py

...files on the user's local filesystem. Base-level (no local imports).

##### web.py

...remote files/pages/apps accessible only through the Web. Base-level (no local imports).

#### maps.py

Classes that are useful/convenient custom extensions of Python's dictionary class. Primarily `LazyDict`, `DotDict`, derivatives thereof, and combinations thereof.

#### metafunc.py

Functions and classes to manipulate, define, and/or be manipulated by other functions and classes. Includes type variables for other files' type hints. Base-level (no local imports).

#### seq.py

Functions and classes primarily to manipulate Sequences, especially strings. Base-level (no local imports).

#### trivial.py

Totally redundant/trivial functions to use as callable default values of optional parameters in other classes' methods. 

### tests/

#### testers.py

Base-level `Tester` class. 

#### test_*.py

The `test_*.py` files define subclasses of `tests/testers.Tester` with methods to run automated `pytest` tests validating the various functions and classes defined in this `gconanpy` module. Each `tests/test_*.py` file corresponds to, and tests, a specific `gconanpy/*.py` file.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2025-04-15
- Current as of `v0.3.0`