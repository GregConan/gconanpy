# IO

## Overview

Input/Output utilities for handling web requests and local file system operations.

The `IO` module provides utilities for both web-based and local file system operations. It includes classes and functions for downloading web content, parsing URLs, and managing local files with validation and error handling.

## Dependencies

- [requests](https://requests.readthedocs.io/en/latest/): HTTP operations

## Modules

### `local.py`

Functions and classes for local file system operations including file reading, writing, and directory management.

- `extract_from_json`: Load JSON data from a file.
- `glob_and_copy`: Copy files matching glob patterns to a destination directory.
- `LoadedTemplate`: Enhanced `string.Template` loaded from files with automatic field/variable name detection.
- `save_to_json`: Save data to a JSON file.
- `walk_dir`: Walk a directory tree, optionally filtering by file extension.

### `web.py`

Functions and classes for web-based I/O operations including HTTP requests, URL parsing, and web content handling.

- `download_GET`: Download content from a URL using an HTTP GET request with headers.
- `read_webpage_at`: Read the contents of a webpage at a given URL.
- `URL`: `gconanpy.strings.FancyString` subclass that can parse URLs to extract parameters, remove parameters, and build URLs from parts.
- `Link`: Convert hyperlinks to and from Markdown text format.

## Usage Examples

### Local File Operations

```python
from gconanpy.IO.local import extract_from_json, save_to_json, LoadedTemplate

# Save data to JSON
save_to_json({"key": "value"}, "output.json")

# Load JSON data
extract_from_json("output.json")  # -> {"key": "value"}

# Load templates from text files
templates = []
for file_path in walk_dir("/path/to/dir", ext=".txt"):
    templates.append(LoadedTemplate.from_file_at(file_path))
    
    # .fields contains all variable names in the template
    print(f"Fields from {file_path}: {templates[-1].fields}")
```

### Web Operations

```python
from gconanpy.IO.web import download_GET, URL, Link

# Download content from URL
response = download_GET("https://api.example.com/data", {"Authorization": "BEARER_TOKEN"})

# Parse and manipulate URL
url = URL("https://example.com/path?param=value")
url.params  # -> {"param": ["value"]}
url.without_params  # -> "https://example.com/path"

# Create URL from parts
URL.from_parts("foo.com", "api", "v1", "users", user_id=123)  # -> "https://foo.com/api/v1/users?user_id=123"

# Handle markdown links
link = Link.from_markdown("[Example](https://example.com)")
link.url  # -> "https://example.com"
link.text  # -> "Example"
```

### Web Content Processing

```python
from gconanpy.IO.web import download_GET, URL

# Download API data
headers = {"Content-Type": "application/json"}
response = download_GET("https://api.example.com/data", headers)

# Parse URL
url = URL("https://example.com/api/v1/users?page=1&limit=10")
url.params  # -> {'page': ['1'], 'limit': ['10']}
```

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2026-04-23
- Current as of `v0.32.1`

### License

This free and open-source software is released into the public domain.
