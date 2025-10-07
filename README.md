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

# create a new INI config
config = IniConfig()

# add values to the default section
config.set("app_name", "My App")
config.set("version", "1.0.0")

# you can use section object to interact with section settings
db_section = config.ensure_section("database")
db_section.comment = ['Contains database settings']

db_provider_opt = db_section.set("provider", "mysql")
db_provider_opt.comment = [
    "Controls the DB provider to be used"
]

# ... or set values directly via root config object
config.set("version", "1.2.3", section_name="database")

# save to file
config.save("config.ini")

# load back from file
loaded_config = IniConfig.load("config.ini")

app_name = loaded_config.get("app_name")  # My App
version = loaded_config.get("version")  # 1.0.0

db_section = loaded_config.get_section("database")

db_provider = db_section.get("provider")  # mysql
db_version = db_section.get("version")  # 1.2.3
```

Example config file output:
```ini
app_name = "My App"

version = "1.0.0"

# Contains database settings
[database]

# Controls the DB provider to be used
provider = "mysql"

version = "1.2.3"

```

## License

MIT License