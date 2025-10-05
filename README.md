![Simplini Logo](resources/logo.png)

[![CI](https://github.com/gubenkoved/simplini/actions/workflows/ci.yml/badge.svg)](https://github.com/gubenkoved/simplini/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **simple** INI file parser and writer for Python that works.

## Installation

```bash
pip install simplini
```

## Why?

The reasons this library was created:

* Standard library configparser does not support round trip editing (comments will not be written back), see https://docs.python.org/3/library/configparser.html
* Alternatives like https://github.com/DiffSK/configobj have a lot of bugs and are not actively maintained

## Comparison

| Library        | Round-trip editing | Maintenance  | Correctness | Configurability | Multi-line values | Error reporting  |
|----------------|--------------------|--------------|-------------|-----------------|-------------------|------------------|
| `configparser` | ❌                  | 🟢           | ✅       | ✅               | ✅                  | 🙂            |
| `ConfigObj`    | ✅                  | 🔴           | 🐛      | ❌               | ❌                  | 🤔                 |
| `python-ini`   | ❌                  | ❓           | ❓      | ✅               | ❓                | 🙁                 |
| `ini-parser`   |  ✅                 | ❓           | 🐛       | ❌                | ❌                 | 🙁               |
| `simplini`     | ✅                  | 🟢           | ✅        | ✅               | ✅                  | 🥰 |

## Features

* Simple API
* Round-trip editing preserving comments
* Non-ambiguous strings encoding
* Configurable parsing and rendering behavior
* No surprises like sudden interpolation or lower-casing option names

## Usage

Basic usage example:

```python
from simplini import IniConfig

# Create a new INI config
config = IniConfig()

# Add values to the default section
config.set("app_name", "My App")
config.set("version", "1.0.0")

# set values for some named section
config.set("db", "sql", section_name="core")

# Add a comment to the default section
config.unnamed_section.comment = [
    "Configuration for My App",
    "Created on 2025-09-28",
]

# Save to file
config.save("config.ini")

# Load from file
loaded_config = IniConfig.load("config.ini")
app_name = loaded_config.get("app_name")  # My App
core_db = loaded_config.get("db", section_name="core")  # sql
```

Example config file output:
```ini
# Configuration for My App
# Created on 2025-09-28

app_name = "My App"

version = "1.0.0"

[core]

db = "sql"

```

## License

MIT License