# Mapping

Advanced dictionary utilities and custom dictionary classes for enhanced data manipulation in the gconanpy library.

## Overview

The `mapping` module provides a suite of dictionary utilities and custom dictionary classes that extend Python's built-in `dict` functionality. It includes specialized dictionary types for various use cases, from basic extensions to advanced features like lazy loading, encryption, and dot notation access.

## Dependencies

- `cryptography`: For encryption capabilities
- `configparser`: For configuration file parsing
- `pprint`: For pretty printing functionality

## Modules

### `dicts.py`

Custom dictionary classes with specialized functionality for various use cases. I suggest using `FancyDict`, which includes all of the others' functionality except encryption, unless your dict needs non-`str` keys.

#### Basic Classes

- **`Cryptionary`** can automatically encrypt the values that it stores.
- **`Exclutionary`** can fill missing values or overwrite unwanted values.
- **`DotDict`** can access and modify items as attributes using dot notation.
- **`CustomDict`** is the base class for these custom dict classes.
- **`HashGrid`** can map a combination of an arbitrary number of keys to each value.
- **`Invertionary`** can swap its keys and values.
- **`LazyDict`** can delay execution of code to get/set default values.
- **`Promptionary`** can interactively prompt the user to fill missing values.
- **`Sortionary`** can sort its keys or its values *by* its keys or its values.
- **`Subsetionary`** can be created from, or create, a subset of another dict.
- **`Walktionary`** can recursively traverse nested dictionaries.

#### Combined Classes

- **`LazyDotDict`** combines dot notation with lazy method calling.
- **`Locktionary`** combines multi-key one-way mapping with value encryption.
- **`DotPromptionary`** combines dot notation with prompting.
- **`SubCryptionary`** combines subset operations with encryption.
- **`FancyDict`** combines most of the others' functionality: dot notation, interactive prompting, invert and sort methods, lazy loading, recursive walking, and subset operations.

#### Secure Multidimensional Dicts: `HashGrid` and `Locktionary`

The **`HashGrid`** and **`Locktionary`** classes map combinations of an arbitrary number of keys (or "coordinates," or "dimensions") to specific values.

Initializing a `HashGrid` as `hg = HashGrid(([1,2,3], "foo"), ([3,2,1], "bar"))`, or equivalently as `hg = HashGrid(values=["foo", "bar"], x=[1, 3], y=[2, 2], z=[3, 1])`, lets you access items as `hg[1, 2, 3] == "foo"` and `hg[3, 2, 1] == "bar"`.

`HashGrid` does not know its own `keys`, so calling the `.keys()` method on a `HashGrid` will not return anything you can use to access the values. This may have cryptographic use.

For example, a `HashGrid` with two dimensions "username" and "password" can allow user-specific access to values using those credentials without actually storing any usernames or passwords. Make a `HashGrid` for that use case like this: `creds = HashGrid.for_creds()` After adding "myvalue" for the user "myuser" with password "mypass" (`creds["myuser", "mypass"] = "myvalue"`), `creds` will not store (or otherwise be able to produce) the values "myuser" or "mypass" even though a user could still get or alter "myvalue" by accessing `creds["myuser", "mypass"]`.

`HashGrid` exposes the values it stores. `Locktionary`, a combination of the `HashGrid` and the `Cryptionary`, encrypts its stored values. So, it directly exposes neither its key combinations nor its values. However, it is still possible for someone to use the `Cryptionary` to decrypt its values. Hopefully a later version can securely map a user's credentials to any value and store that mapping without exposing it, such that the credentials *and value* are only visible to someone who already has the credentials. 

#### Usage Examples

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

### `__init__.py`

Standalone utility functions for the dictionary operations described above. Replicates functionality built into `mapping/dicts.py` classes without requiring the user to initialize the `dict` as anything else.

#### Usage Examples

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

## Error Handling

All dictionary operations include comprehensive error handling:

- Safe key access with defaults
- Exclusion-based filtering
- Lazy loading with fallback functions
- Encryption/decryption error handling
- Protected attribute access in dot notation

## Best Practices

- Use appropriate dictionary types for specific use cases
- Handle missing keys gracefully with defaults
- Use exclusion sets for filtering unwanted values
- Implement proper error handling for encryption operations
- Consider performance implications of lazy loading
- Use dot notation carefully to avoid conflicts with built-in attributes 

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-09-06
- Current as of `v0.13.2`

### License

This free and open-source software is released into the public domain.