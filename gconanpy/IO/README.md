# IO

Input/Output utilities for handling web requests and local file operations.

## Overview

The `IO` module provides utilities for both web-based and local file system operations. It includes classes and functions for downloading web content, parsing URLs, and managing local files with validation and error handling.

## Modules

### `local.py`

Functions and classes for local file system operations including file reading, writing, and directory management.

#### Key Functions

- **`extract_from_json`**: Load JSON data from file
- **`save_to_json`**: Save data to JSON file
- **`glob_and_copy`**: Copy files matching glob patterns
- **`walk_dir`**: Walk directory with optional file extension filtering

#### Key Classes

- **`LoadedTemplate`**: Enhanced string template loaded from files with field detection

#### Key Features

- JSON file reading and writing
- Template loading from files with field detection
- File copying with glob pattern matching
- Directory traversal with optional file extension filtering

#### Usage Examples

```python
from gconanpy.IO.local import extract_from_json, save_to_json, LoadedTemplate

# Save data to JSON
save_to_json({"key": "value"}, "output.json")

# Load JSON data
data = extract_from_json("output.json")  # -> {"key": "value"}

# Load templates from text files
templates = list()
for file_path in walk_dir("/path/to/dir", ext=".txt"):
    templates.append(LoadedTemplate.from_file_at(file_path))
    
    # .fields contains all variable names in the template
    print(f"Fields from {file_path}: {templates[-1].fields}")
```

### `web.py`

Functions and classes for web-based I/O operations including HTTP requests, URL parsing, and web content handling.

#### Key Classes

- **`URL`** can parse URLs to extract parameters.
- **`Link`** can convert hyperlinks to and from Markdown text format.

#### Usage Examples

```python
from gconanpy.IO.web import download_GET, URL, Link

# Download content from URL
response = download_GET("https://api.example.com/data", {"Authorization": "BEARER_TOKEN"})

# Parse and manipulate URL
url = URL("https://example.com/path?param=value")
url.get_params()  # -> {"param": ["value"]}
url.without_params()  # -> "https://example.com/path"

# Create URL from parts
URL.from_parts("foo.com", "api", "v1", "users", user_id=123)  # -> "https://foo.com/api/v1/users?user_id=123

# Handle markdown links
link = Link.from_markdown("[Example](https://example.com)")
link.url  # -> "https://example.com"
link.text  # -> "Example"
```

## Common Use Cases

### Web Content Processing

```python
from gconanpy.IO.web import download_GET, URL

# Download API data
headers = {"Content-Type": "application/json"}
response = download_GET("https://api.example.com/data", headers)

# Parse and modify URL
url = URL("https://example.com/api/v1/users?page=1&limit=10")
url.get_params()  # -> {'page': ['1'], 'limit': ['10']}
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-10-11
- Current as of `v0.21.6`

### License

This free and open-source software is released into the public domain.