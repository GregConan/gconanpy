# GConanPy

## Introduction

### Summary

Centralized repository containing the basic and lower-level Python tools that I reuse across multiple projects, like [emailbot](https://github.com/GregConan/emailbot) and [Knower](https://github.com/GregConan/Knower). I intend my projects to import these tools to prevent redundancy.

## File Structure

### gconanpy/

#### cli.py

Functions and classes primarily to define, accept, and validate command-line input arguments.

#### debug.py

Functions and classes only needed to ease/aid interactive debugging.

#### dissectors.py

Classes to inspect/examine/unwrap complex data structures:

- A `DifferenceBetween` identifies what makes any given Python objects differ from each other.
- A `Peeler` can remove unneeded outermost layers of nested containers.
- A `Shredder` can "flatten" a nested container, extracting every contained item regardless of how deeply it is nested.
- An `Xray` can list the attributes, keys, or outputs of any given Python object.

*Extremely* useful and convenient for interactive debugging, especially with `pdb`. 

#### extend.py

Classes and functions to extend, combine, and wrap other classes and functions.

#### find.py

Functions and classes that iterate and break once they find what they're looking for. Like `dissectors.py`, useful to unwrap complex data structures.

#### io/

Functions and classes primarily to import data from, and export data to...

##### local.py

...files on the user's local filesystem. Base-level (no local imports).

##### web.py

...remote files/pages/apps accessible only through the Web. Base-level (no local imports).

#### dicts.py

Classes that are useful/convenient custom extensions of Python's dictionary class:

- A `Cryptionary` encrypts the values that it stores.
- A `Defaultionary` can fill default values for many keys and overwrite specified values.
- A `DotDict` can access items as attributes using dot`.`notation.
- An `Invertionary` can swap its keys and values.
- A `LazyDict` can delay execution of code to get/set default values until needed.
- A `Promptionary` can interactively prompt the user to fill missing values.
- A `Subsetionary` can be initialized from, or get, a subset of a dictionary.
- A `Walktionary` can recursively traverse dictionaries nested anywhere inside of it.

#### maptools.py

Classes that are useful when working with (especially nested) Python dicts/Mappings:

- A `Bytesifier` can convert various data types to bytes. Used by `Cryptionary`.
- A `MapSubset` can get a precisely defined subset of a dict/Mapping. Used by `Subsetionary`.
- A `WalkMap` can traverse nested dicts/Mappings. Used by `Walktionary`.

Base-level (no local imports).

#### metafunc.py

Functions and classes to manipulate, define, and/or be manipulated by other functions and classes:

- `combine_*` functions can merge containers.
- `AttributesOf` can select, iterate over, and/or copy the attributes of any Python object.
- `KeepTryingUntilNoErrors` and `IgnoreExceptions` are context managers that ease writing nested `try`-`except` blocks.
- `metaclass_*` functions can dynamically create/define metaclasses to dynamically create/define custom type classes.
- `MethodWrapper` has methods that can be used to decorate other classes' methods.
- `name*` functions can easily get any objects' class/type names.
- `WrapFunction` can predefine input parameters for a function in order to call that function with those parameters later.

Also includes custom type variables for type hints in other files.

#### reg.py

Classes that use Regex to parse strings and text data:

- `DunderParser` can convert and parse the names of Python's double-underscore ("dunder") methods/variables.
- `Regextract` can extract letters, parentheticals, and other kinds of text.

#### seq.py

Functions and classes primarily to manipulate Sequences, especially strings. 

#### ToString.py

Class extending the Python `str` type, including convenient methods with many precise options to convert various Python data types to strings.

#### trivial.py

Totally redundant/trivial functions to use as default values of optional callable parameters in other classes' methods. Base-level (no local imports).

### tests/

#### testers.py

Base-level `Tester` class. 

#### test_*.py

The `test_*.py` files define subclasses of `tests/testers.Tester` with methods to run automated `pytest` tests validating the various functions and classes defined in this `gconanpy` module. Each `tests/test_*.py` file corresponds to, and tests, a specific `gconanpy/*.py` file.

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-03-13
- Updated by @[GregConan](https://github.com/GregConan) on 2025-05-31
- Current as of `v0.4.11S`