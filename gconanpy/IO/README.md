# IO

Input/Output utilities for handling web requests and local file operations.

## Overview

The `IO` module provides utilities for both web-based and local file system operations. It includes classes and functions for downloading web content, parsing URLs, and managing local files with validation and error handling.

## Dependencies

- `glob` for file pattern matching
- `json` for JSON file operations
- `requests` for HTTP operations
- `shutil` for file copying operations
- `urllib` for basic web content reading

## Modules

### `web.py`

Functions and classes for web-based I/O operations including HTTP requests, URL parsing, and web content handling.

#### Key Classes

- **`URL`**: Enhanced URL parser with additional utility methods
- **`Link`**: Markdown link representation and manipulation

#### Key Features

- HTTP request handling with error checking
- URL parsing and manipulation
- Markdown link parsing and generation
- URL parameter extraction and modification

#### Usage Examples

```python
from gconanpy.IO.web import download_GET, URL, Link

# Download content from URL
response = download_GET("https://api.example.com/data", {"Authorization": "BEARER_TOKEN"})

# Parse and manipulate URL
url = URL("https://example.com/path?param=value")
params = url.get_params()
clean_url = url.without_params()

# Create URL from parts
url = URL.from_parts("api", "v1", "users", user_id=123)

# Handle markdown links
link = Link.from_markdown("[Example](https://example.com)")
markdown = link.to_markdown("Custom Text")
```

### `local.py`

Functions and classes for local file system operations including file reading, writing, and directory management.

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

# Load JSON data
data = extract_from_json("config.json")

# Save data to JSON
save_to_json({"key": "value"}, "output.json")

# Load template from file
template = LoadedTemplate.from_file_at("template.txt")
fields = template.fields  # Get template variables

# Walk directory for specific files
for file_path in walk_dir("/path/to/dir", ext=".txt"):
    print(f"Found: {file_path}")
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
params = url.get_params()  # -> {'page': ['1'], 'limit': ['10']}
```

### File Operations

```python
from gconanpy.IO.local import extract_from_json, LoadedTemplate

# Load configuration
config = extract_from_json("config.json")

# Process template
template = LoadedTemplate.from_file_at("email_template.txt")
# template.fields contains all variable names in the template
```

## Error Handling

Both modules include error handling:

- Network request failures are caught and reported
- File operations include proper exception handling
- URL parsing includes validation
- Template loading includes field detection

## Best Practices

- Always use appropriate headers for web requests
- Validate URLs before processing
- Handle file paths carefully across different operating systems
- Use context managers for file operations when possible
- Include error handling for network and file operations 

## Meta

### About This Document

- Created by @[GregConan](https://github.com/GregConan) on 2025-08-05
- Updated by @[GregConan](https://github.com/GregConan) on 2025-08-09
- Current as of `v0.13.2`

### License

This free and open-source software is released into the public domain.