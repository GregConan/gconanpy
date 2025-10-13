# Access

Object attribute and item access utilities for enhanced data manipulation.

## Overview

The `access` module provides comprehensive utilities for accessing and manipulating object attributes and collection items. It includes specialized classes and functions for safe attribute access, item retrieval, and data structure navigation with error handling and filtering capabilities.

## Modules

### `__init__.py`

Core accessor functions and classes for item and attribute manipulation.  

#### Key Classes

- **`Accessor`**: Unified interface for accessing and manipulating object attributes OR items, with advanced access and manipulation methods as well as basic get/has/set/delete operations.

The **`Accessor`** class attempts to abstract out the basic functionality shared by access/modification methods for items and attributes, potentially allowing functionality that treats them interchangeably.

Consider wanting to perform the same operation on an `Iterable`'s elements/items as its attributes. Ideally, using the `Accessor` class, you could define that operation exactly once in one function with a boolean "attributes or elements?" parameter. However, I have not yet found a use case that makes the added complexity and performance overhead worth it.

#### Key Functions

- **`getdefault`**: Safe item/attribute retrieval with default values
- **`setdefault`**: Set default value for missing item/attribute
- **`fill_replace`**: Replace specific (especially empty/blank) values in `Collection`s

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

Advanced attribute manipulation and introspection utilities.

#### Key Classes

- **`AttrsOf`**: Comprehensive attribute access and manipulation class.

#### Key Functions

- **`add_to`**: Add multiple attributes to an object
- **`get_all_names`**: Get all attribute names from multiple objects
- **`get_names`**: Get all attribute names of an object
- **`getdefault`**: Safe attribute access with defaults
- **`has`**: Check whether an object has an attribute, not counting certain values
- **`is_private`**: Check if attribute name is private
- **`is_read_only`**: Check if attribute is read-only
- **`lazyget`**: Lazy attribute access with fallback functions
- **`lazysetdefault`**: Lazy attribute setting with defaults
- **`setdefault`**: Set default value for missing attribute
- **`slotsof`**: Get object's `__slots__` or `__dict__` keys
- **`varsof`**: Get object's variables as dictionary

#### Usage Examples

```python
from gconanpy.access.attributes import AttrsOf, add_to, get_names

# Add attributes to an object
class BareObject(): ...
obj = BareObject()
obj.new_attr  # -> AttributeError
obj = add_to(obj, new_attr="value", another_attr=123)
obj.new_attr  # -> "value"
obj.another_attr  # -> 123

# Get all attribute names
get_names(obj)  # -> {"new_attr", "another_attr", ...}

# Attribute selection
attrs = AttrsOf(obj)
public_attrs = list(attrs.public())  # -> ["new_attr", "another_attr"]
methods = list(attrs.methods())
private_attrs = list(attrs.private())
```

### `dissectors.py`

Data structure inspection and analysis utilities for debugging and exploration.

#### Key Classes

- **`DifferenceBetween`**: Compare objects and identify differences
- **`Peeler`**: Remove unnecessary nested container layers
- **`Shredder`**: Recursively extract all data from nested structures
- **`Corer`**: Find the largest/smallest items in nested data
- **`Xray`**: Inspect object contents, attributes, and outputs

#### Usage Examples

```python
from gconanpy.access.dissectors import DifferenceBetween, Shredder, Xray

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

### `find.py`

Search and finder utilities with early termination patterns.

#### Key Classes

- **`Spliterator`**: Split and recombine strings iteratively
- **`UntilFound`**: Call function on items until condition is met
- **`BasicRange`**: Custom range-like iterator base class
- **`ErrIterChecker`**: Iterator with exception handling
- **`ReadyChecker`**: Context manager for readiness checking

#### Usage Examples

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
- Updated by @[GregConan](https://github.com/GregConan) on 2025-10-12
- Current as of `v0.22.0`

### License

This free and open-source software is released into the public domain.
