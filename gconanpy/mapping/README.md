# Mapping

## Overview

Advanced dictionary utilities and custom dictionary classes for enhanced data manipulation in the gconanpy library. The `mapping` module provides a suite of dictionary utilities and custom dictionary classes that extend Python's built-in `dict` functionality. It includes specialized dictionary types for various use cases, from basic extensions to advanced features like lazy loading, encryption, dot notation access, and attribute-based mapping.

## Dependencies

- [cryptography](https://cryptography.io/en/latest/): Encryption capabilities

## Modules

### `__init__.py`

Standalone utility functions for the dictionary operations described in the classes below. Replicates functionality built into `mapping/dicts.py` classes without requiring the user to initialize the `dict` as a custom class.

- `chain_get`: Get the value of one of the provided keys, chained for fallback value retrieval.
- `fromConfigParser`: Create a dictionary from a `ConfigParser`.
- `from_strings`: Create a dictionary from delimiter-separated string pairs.
- `get_or_prompt_for`: Get a value or prompt the user for input.
- `get_subset_from_lookups`: Get a subset using lookup paths.
- `getdefault`: Safe dictionary access with defaults and optional exclusion filtering.
- `has`: Check if a key exists with exclusion filtering.
- `has_all`: Check if all keys exist in a `Mapping`.
- `invert`: Swap keys and values in a dictionary, with options to keep all keys or unpack iterables.
- `keys_mapped_to`: Find all keys mapped to a specific value.
- `lazyget`: Lazy dictionary access with a fallback function.
- `lazysetdefault`: Lazy dictionary setting with a fallback function.
- `lookup`: Nested dictionary lookup using dot notation paths.
- `many_from_1_mapper_dict`: Create a dict repeatedly mapping different keys to the same value.
- `missing_keys`: Find missing keys in a dictionary.
- `overlap_pct`: Calculate overlap percentage between `Collection`s.
- `pprint_val_lens`: Pretty print the length of each value in a `Mapping`.
- `rename_keys`: Rename dictionary keys.
- `setdefault_or_prompt_for`: Set a default or prompt the user.
- `setdefaults`: Set multiple defaults at once, preferring to keep old values.
- `sorted_by`: Sort a dictionary by keys or values.
- `update`: Update a dictionary with additional data from other `Mapping`s.

### `attrmap.py`

Dictionary-like `MutableMapping` classes that store items as attributes, accessible using dot notation.

- `AttrMap`: Simple `MutableMapping[str, T]` that can store, access, and modify items as attributes using dot notation, in a manner that is recognizable by type checkers.
- `DefaultAttrMap`: `AttrMap` equivalent of `defaultdict`: accessing a missing attribute creates it using a factory function.
- `ExcludAttrMap`: `AttrMap` with `exclude=` options on access methods, letting it ignore specified values as if they were blank.
- `MathAttrMap`: `AttrMap` that can perform math operations on its items.
- `SortAttrMap`: `AttrMap` that can yield its key-value pairs sorted by keys or values.
- `LazyAttrMap`: `AttrMap` with lazy get/set methods that delay evaluation of defaults until needed.
- `PromptAttrMap`: `AttrMap` able to interactively prompt the user to fill missing values.

### `bases.py`

Custom `Mapping` base classes inherited by classes in `dicts.py` and in `attrmap.py`.

- `InitMutableMap`: Base `MutableMapping` with a flexible `__init__` accepting `Mapping`s and keyword arguments.
- `ExcluderMap`: Custom `MutableMapping` that adds `exclude=` options to methods, letting it ignore specified values as if they were blank. Base class for `LazyMap` and others.
- `LazyMap`: `MutableMapping` that can get/set items and ignore the default parameter until/unless it is needed, ONLY evaluating it after failing to get/set an existing key.
- `MathMap`: `MutableMapping` that can perform math operations (arithmetic, comparison, bit shifting, etc.) on its items.
- `ComparableMathMap`: `MutableMapping` with comparison dunder methods (`>=`, `>`, `<=`, `<`) that compare element-wise.
- `PromptMap`: `LazyMap` able to interactively prompt the user to fill missing values.
- `SortMap`: Custom `MutableMapping` that can yield a generator of its key-value pairs sorted by keys or values.

### `dicts.py`

Custom dictionary classes with specialized functionality for various use cases. I suggest using `FancyDict`, which includes all of the others' functionality except encryption, unless your dict needs non-`str` keys.

- `Cryptionary`: Extended `Promptionary` that automatically encrypts values before storing them and automatically decrypts values before returning them.
- `CustomDict`: Base class for custom dictionary classes. Explicitly includes its class name in its string representation(s).
- `DotDict`: Custom dict with dot.notation item access. If `name` is not protected, then `self.name is self["name"]`.
- `DotPromptionary`: Combines dot notation with prompting.
- `ExcluDict`: Custom dict that adds `exclude=` options to `dict` methods, letting it ignore specified values as if they were blank.
- `FancyDict`: Combines most of the others' functionality: dot notation, interactive prompting, invert and sort methods, lazy loading, recursive walking, and subset operations.
- `Invertionary`: Custom dict that can swap its keys and values.
- `LazyDict`: Dict that can get/set items and ignore the default parameter until/unless it is needed, ONLY evaluating it after failing to get/set an existing key.
- `LazyDotDict`: Combines dot notation with lazy method calling.
- `MathDict`: Custom dict that can perform math operations on its items (addition, subtraction, multiplication, division, etc.).
- `OverlapPercents`: Custom dict calculating what percentage of the elements of each `Collection` are also in each other `Collection`.
- `Promptionary`: `LazyDict` able to interactively prompt the user to fill in missing values.
- `Sortionary`: Custom dict that can yield its key-value pairs sorted by keys or values.
- `SubCryptionary`: Combines subset operations with encryption.
- `Subsetionary`: Custom dict that can be created from, or create, a subset of another dict.
- `Updationary`: Custom dict with enhanced `update` that accepts `Mapping`s, iterables of pairs, and keyword arguments with an optional copy mode.
- `Walktionary`: Custom dict that can recursively traverse nested dictionaries via a `MapWalker`.

### `grids.py`

Multidimensional custom dictionary classes mapping combinations of an arbitrary number of keys (or "coordinates," or "dimensions") to specific values. Primarily different classes of `HashGrid`, a custom `dict` mapping `int` hashes (of key combinations) to values.

Initializing a `HashGrid` as `hg = HashGrid(([1,2,3], "foo"), ([3,2,1], "bar"))`, or equivalently as `hg = HashGrid(values=["foo", "bar"], a=[1, 3], b=[2, 2], c=[3, 1])`, lets you access items as `hg[1, 2, 3] == "foo"` and `hg[3, 2, 1] == "bar"`.

`HashGrid` does not know its own `keys`, so calling the `.keys()` method on a `HashGrid` will not return anything you can use to access the values. This may have cryptographic use.

For example, a `HashGrid` with two dimensions "username" and "password" can allow user-specific access to values using those credentials without actually storing any usernames or passwords. Make a `HashGrid` for that use case like this: `creds = HashGrid.for_creds()` After adding "myvalue" for the user "myuser" with password "mypass" (`creds["myuser", "mypass"] = "myvalue"`), `creds` will not store (or otherwise be able to produce) the values "myuser" or "mypass" even though a user could still get or alter "myvalue" by accessing `creds["myuser", "mypass"]`.

`HashGrid` exposes the values it stores. `Locktionary`, a combination of the `HashGrid` and the `Cryptionary`, encrypts its stored values. So, it directly exposes neither its key combinations nor its values. However, it is still possible for someone to use the `Cryptionary` to decrypt its values. Hopefully a later version can securely map a user's credentials to any value and store that mapping without exposing it, such that the credentials *and value* are only visible to someone who already has the credentials. 

- `BaseHashGrid`: Abstract base class defining functionality shared by all multi-key `HashGrid` classes.
- `UnorderedHashGrid`: A `HashGrid` that treats any combination of the same keys the same way regardless of order.
- `HashGrid`: Can map a combination of an arbitrary number of keys to each value, with strict validation of key counts.
- `Grid`: Simple 2D grid mapping (x, y) coordinate pairs to values with invertible axes.
- `Locktionary`: Combines multi-key one-way mapping with value encryption, exposing neither its keys nor its values.

## Usage Examples

### Custom Dictionaries

```python
from configparser import ConfigParser
from gconanpy.mapping.dicts import FancyDict, Cryptionary

# Load configuration
config_parser = ConfigParser()
config_parser.read("/home/project/config.ini")
config = FancyDict.fromConfigParser(config_parser)

# Access nested values with dot notation
config  # -> FancyDict({"db": {"host": "localhost"}, "api_key": None}})
config.db.host  # -> "localhost"

# Prompt user for missing API key after recognizing None as a missing value
config.setdefault_or_prompt_for("api_key", "Enter API key: ", exclude={None})

# Encrypted storage
crypto_dict = Cryptionary()
crypto_dict["secret"] = "sensitive_data"  # Automatically encrypted
print(crypto_dict)  # Shows encrypted string; doesn't show "sensitive_data"
decrypted = crypto_dict["secret"]  # Automatically decrypted
```

### Standalone Functions

```python
from gconanpy.mapping import chain_get, lookup, invert

# Chain multiple keys for fallback
value = chain_get(data, ["primary_key", "fallback_key"], default="default")

# Invert dictionary
inverted = invert({"a": 1, "b": 2})  # -> {1: "a", 2: "b"}

# Nested dictionary lookup
data = {
    "user": {
        "profile": {
            "name": "John",
            "email": "john@example.com"
        }
    }
}
name = lookup(data, "user.profile.name")  # -> "John"
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
