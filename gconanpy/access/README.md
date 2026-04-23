# Access

## Overview

Object attribute and item access utilities for enhanced data manipulation. 

The `access` module provides comprehensive utilities for accessing and manipulating object attributes and collection items. It includes specialized classes and functions for safe attribute access, item retrieval, and data structure navigation with error handling and filtering capabilities.

Several `access/` and `mapping/` files share some identically named access and manipulation functions/methods to provide the same functionality for different use cases:

- `access/attributes.py` for object attributes,
- `mapping/__init__.py` for any `Mapping`s, 
- `mapping/dicts.py` for custom `dict`s (object-oriented), and
- `access/__init__.py` for object attributes *or* `Collection` items.

## Dependencies

- [more-itertools](https://more-itertools.readthedocs.io/en/stable/): Advanced iteration utilities

## Modules

### `__init__.py`

Core accessor functions and classes for item and attribute manipulation.  

- `getdefault`: Return the value for a key if it is in the object, else a default. Same as `dict.get`, but also works on `Sequence`s.
- `fill_replace`: Replace specific (especially empty/blank) values in `Collection`s.
- `setdefault`: Return the value for a key if it is in the object; else add that key with a default value and return the default. Same as `dict.setdefault`, but also works on `MutableSequence`s.

#### Key Class: `Accessor`

- `Accessor`: Unified interface for accessing and manipulating object attributes OR items, with advanced access and manipulation methods as well as basic get/has/set/delete operations.

The `Accessor` class attempts to abstract out the basic functionality shared by access/modification methods for items and attributes, potentially allowing functionality that treats them interchangeably.

Consider wanting to perform the same operation on an `Iterable`'s elements/items as its attributes. Ideally, using the `Accessor` class, you could define that operation exactly once in one function with a boolean "attributes or elements?" parameter. However, I have not yet found a use case that makes the added complexity and performance overhead worth it.

#### Usage Examples

```python
from gconanpy.access import getdefault, setdefault, Access

# Safe item access with defaults
value = getdefault(my_dict, "key", "default_value")

# Set default if missing
setdefault(my_list, 0, "first_item")

# Use pre-configured accessors
Access.item.get(my_dict, "key")
Access.attribute.has(my_obj, "attr_name")
```

### `attributes.py`

Dynamic attribute manipulation and introspection utilities including filtering, lazy access, and comprehensive object analysis.

- `add_to`: Add multiple attributes to an object.
- `get_names`: Get all attribute names from one or more objects, including inherited attributes.
- `getdefault`: Safe attribute access with a default value and optional exclusion filtering.
- `has`: Check whether an object has an attribute, not counting certain values.
- `is_private`: Check if an attribute name is private (starts with an underscore).
- `is_read_only`: Check if an attribute is read-only by trying to set it to its current value.
- `lazyget`: Lazy attribute access returning a fallback function's result if absent.
- `lazysetdefault`: Lazy attribute setting with a fallback function if absent.
- `setdefault`: Set a default value for a missing attribute.
- `slotsof`: Get an object's mutable attribute names (namely its `__slots__` or its `__dict__` keys).
- `varsof`: Get an object's mutable attributes (namely its `__slots__` and their values or its `__dict__`).

#### Key Class: `AttrsOf`

- `AttrsOf`: Comprehensive attribute access and manipulation class to select, iterate, copy, or filter the attributes of any object.

### `find.py`

Classes and functions for finding items in iterables with early termination. Includes integrated string manipulation. 

- `BasicRange`: Custom range-like iterator base class with configurable start, end, and step.
- `ErrIterChecker`: Iterator combining `BasicRange` with exception handling for iterating while catching errors.
- `iterfind`: Find the first item in an iterable matching a condition.
- `modifind`: Find an item after modification, returning the first modified result satisfying a condition.
- `ReadyChecker`: Context manager to check once per iteration whether an item being modified is ready to return.
- `Spliterator`: Split and recombine strings iteratively until satisfaction of a condition.
- `UntilFound`: Call a function on each item in an iterable until one of them returns a result satisfying a specified condition.

### `nested.py`

Classes to inspect, traverse, examine, and compare complex/nested data structures without already knowing their internal structure. Very useful for interactive debugging.

- `Corer`: Find the largest or smallest items in nested data structures using configurable comparison functions.
- `DifferenceBetween`: Compare objects and identify differences in type, length, keys, elements, or attributes.
- `Peeler`: Remove unnecessary nested container layers from data structures.
- `Shredder`: Recursively extract all data from nested structures, with optional filtering and a maximum traversal depth.
- `Xray`: Inspect object contents, attributes, and outputs. Extremely convenient for interactive debugging.

## Usage Examples

### Safe Item/Attribute Access

```python
from gconanpy.access import getdefault, setdefault, ACCESS

# Safe dict item access with defaults
my_dict = {}
getdefault(my_dict, "key", "default_value")  # -> "default_value"
my_dict  # -> {}
setdefault(my_dict, "key", "default_value")  # -> "default_value"
my_dict  # -> {"key": "default_value"}

# Safe list item access with defaults
my_list = []
getdefault(my_list, 0, "first_item")  # -> "first_item"
my_list  # -> []
setdefault(my_list, 0, "first_item")  # -> "first_item"
my_list  # -> ["first_item"]

# Use pre-configured accessors
ACCESS.item.get(my_dict, "key")  # -> "default_value"
ACCESS.item.has(my_dict, "key")  # -> True
ACCESS.item.has(my_dict, "key", exclude="default_value")  # -> False
```

### Attribute Manipulation

```python
from gconanpy.access import attributes

# Add attributes to an object
class BareObject():
    ...
obj = BareObject()
obj.new_attr  # -> AttributeError
obj = attributes.add_to(obj, new_attr="value", another_attr=123)
obj.new_attr  # -> "value"
obj.another_attr  # -> 123

# Get all attribute names
attributes.get_names(obj)  # -> {"new_attr", "another_attr", ...}

# Attribute selection
attrs = attributes.AttrsOf(obj)
list(attrs.public_names())  # -> ["new_attr", "another_attr"]
private_attrs = list(attrs.private_names())
```

### Data Structure Inspection

```python
from gconanpy.access.nested import DifferenceBetween, Shredder, Xray

# Compare objects and find differences
DifferenceBetween([1,2,3], [1,2,3])  # -> list1 == list2
DifferenceBetween([1,2,3], [1,2,4])  # -> Element 2 differs between list1 and list2: Element 2 of list1 is 3 and element 2 of list2 is 4
DifferenceBetween([1,2,3], [1,2,3,4])  # -> Length differs between list1 and list2: Length of list1 is 3 and length of list2 is 4
DifferenceBetween([1,2,3], [1,2,3], (1,2,3))  # -> Type differs between list1, list2, and tuple1: Type of list1 is <class 'list'>, type of list2 is <class 'list'>, and type of tuple1 is <class 'tuple'>

# Extract all data from nested structure
shredder.shred({"foo": [1, {"bar": ["baz"]}]})  # -> {1, "baz"}

# Inspect object structure with Xray
class BareObject():
    foo = "bar"
my_object = BareObject()
Xray(my_object)  # -> BareObject attributes: ['foo']
Xray(dict(a=1, b=2, c=[1, 2, 3, 4, 5]))  # -> dict contents: ['a', 'b', and 'c']
```

### Finding Items

```python
from gconanpy.access.find import iterfind, modifind, UntilFound

# Find first item matching condition
numbers = [1, 2, 3, 4, 5]
first_even = iterfind(numbers, lambda x: x % 2 == 0)

# Find item after modification
def double(x): return x * 2
first_large = modifind(numbers, modify=double, found_if=lambda x: x > 6)

# Use UntilFound for complex searches
finder = UntilFound(lambda x: x > 10)
result = finder.check_each(numbers, default=None)
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-10-10
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
