![Simplini Logo](resources/logo.png)

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
config.unnamed_section.set("app_name", "My App")
config.unnamed_section.set("version", "1.0.0")

# Add a comment to the default section
config.unnamed_section.comment = ["Configuration for My App", "Created on 2025-09-28"]

# Save to file
config.save("config.ini")

# Load from file
loaded_config = IniConfig.load("config.ini")
app_name = loaded_config.unnamed_section["app_name"].value  # "My App"
```

Example config file output:
```ini
# Configuration for My App
# Created on 2025-09-28
app_name = "My App"
version = "1.0.0"
```

## License

MIT License