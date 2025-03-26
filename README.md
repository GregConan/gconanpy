# GConanPy

## Introduction

### Summary

Centralized repository containing the basic and lower-level Python tools that I reuse across multiple projects. I intend my projects to import from here to prevent redundancy.

## File Structure

### cli.py

Functions and classes primarily to define, accept, and validate command-line input arguments. Base-level (no local imports).

### debug.py

Functions and classes only needed to ease/aid debugging. Convenient and useful.

### dissectors.py

Classes to inspect/examine/unwrap complex data structures. *Extremely* useful and convenient for debugging.

### finders.py

Iterator classes that break once they find what they're looking for. Like `dissectors.py`, useful to unwrap complex data structures.

### io/

Functions and classes primarily to import data from, and export data to...

#### local.py

...files on the user's local filesystem. Base-level (no local imports).

#### web.py

...remote files/pages/apps accessible only through the Web. Base-level (no local imports).

### maps.py

Classes that are useful/convenient custom extensions of Python's dictionary class. Primarily `LazyDict`, `DotDict`, derivatives thereof, and combinations thereof.

### seq.py

Functions primarily to manipulate Sequences, especially strings.

### ToString.py

Class to convert objects into strings. Base-level (no local imports).

### typevars.py

Classes and metaclasses to define generic types in other classes. Primarily to specify type hints in `finders.py` as of `v0.2.0`.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2025-03-25
- Current as of `v0.2.0`