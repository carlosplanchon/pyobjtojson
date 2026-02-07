# pyobjtojson

A lightweight Python library that simplifies the process of serializing **any** Python object into a JSON-friendly structure without getting tripped up by circular references. With built-in support for dataclasses, Pydantic (v1 & v2), and standard Python collections, **pyobjtojson** helps you convert your objects into a cycle-free, JSON-ready format for logging, storage, or data transfer.

## Features

- **Automatic Circular Reference Detection**
  Detects and replaces cyclical structures with `"<circular reference>"` to prevent infinite loops.
- **Broad Compatibility**
  Works seamlessly with dictionaries, lists, custom classes, dataclasses, and Pydantic models (including both `model_dump()` from v2 and `dict()` from v1).
- **Extended Standard Types Support**
  Native support for `datetime`, `date`, `time`, `UUID`, `Decimal`, `bytes`, `Enum`, `Path`, `set`, and `frozenset`.
- **Full Type Hints Support**
  Complete type annotations for better IDE autocomplete, type checking with mypy, and improved code documentation.
- **Non-Intrusive Serialization**
  No special inheritance or overrides needed. Uses reflection and standard Python methods (`__dict__`, `asdict()`, `to_dict()`, etc.) where available.
- **Easy to Integrate**
  Just call `obj_to_json()` on your data structure—no additional configuration required.

### DeepWiki Docs: [https://deepwiki.com/carlosplanchon/pyobjtojson](https://deepwiki.com/carlosplanchon/pyobjtojson)

## Installation with uv:

```bash
uv add pyobjtojson
```

## Quickstart

### 1. Basic Usage

```python
from pyobjtojson import obj_to_json

# A simple dictionary with lists
data = {
    "key1": "value1",
    "key2": [1, 2, 3],
    "nested": {"inner_key": "inner_value"}
}

json_obj = obj_to_json(data)  # Using json.dumps kwargs
```

**Output** (example):
```json
{
  "key1": "value1",
  "key2": [
    1,
    2,
    3
  ],
  "nested": {
    "inner_key": "inner_value"
  }
}
```

### 2. Handling Circular References
```python
from pyobjtojson import obj_to_json

a = {"name": "A"}
b = {"circular": a}
a["b"] = b  # Creates a circular reference

obj_to_json(a, check_circular=True)  # check_circular is True by default.
```

**Output**:
```json
{
  "name": "A",
  "b": {
    "circular": {
      "name": "A",
      "b": "<circular reference>"
    }
  }
}
```

### 3. Working with Dataclasses and Pydantic

```python
from dataclasses import dataclass
from pydantic import BaseModel
from pyobjtojson import obj_to_json

@dataclass
class MyDataClass:
    title: str
    value: int

class MyModel(BaseModel):
    name: str
    age: int

dataclass_instance = MyDataClass(title="Test", value=123)
pydantic_instance = MyModel(name="Alice", age=30)

obj = {
    "dataclass": dataclass_instance,
    "pydantic": pydantic_instance
}

obj_to_json(obj)
```

**Output**:
```json
{
  "dataclass": {
    "title": "Test",
    "value": 123
  },
  "pydantic": {
    "name": "Alice",
    "age": 30
  }
}
```

### 4. Standard Python Types

**pyobjtojson** now supports many standard Python types out of the box:

```python
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID
from pyobjtojson import obj_to_json

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

data = {
    "timestamp": datetime(2024, 1, 15, 10, 30, 45),
    "date": date(2024, 1, 15),
    "time": time(14, 30, 0),
    "id": UUID("12345678-1234-5678-1234-567812345678"),
    "price": Decimal("99.99"),
    "binary": b"Hello",
    "status": Status.ACTIVE,
    "path": Path("/home/user/file.txt"),
    "tags": {"python", "json", "api"}
}

obj_to_json(data)
```

**Output**:
```json
{
  "timestamp": "2024-01-15T10:30:45",
  "date": "2024-01-15",
  "time": "14:30:00",
  "id": "12345678-1234-5678-1234-567812345678",
  "price": 99.99,
  "binary": "SGVsbG8=",
  "status": "active",
  "path": "/home/user/file.txt",
  "tags": ["api", "json", "python"]
}
```

**Supported Standard Types:**
- **datetime, date, time** → ISO format strings
- **UUID** → string representation
- **Decimal** → float (default) or string (with `decimal_as_float=False`)
- **bytes, bytearray** → base64 encoded strings
- **Enum** → underlying value
- **Path** → string representation
- **set, frozenset** → sorted lists

## API Reference

### `obj_to_json(obj, check_circular=True, decimal_as_float=True)`

Returns a cycle-free structure (nested dictionaries/lists) that is JSON-serializable.

**Parameters:**
- `obj` (Any): The object to serialize to JSON-like structures.
- `check_circular` (bool, optional): If True (default), detect and mark circular references as `"<circular reference>"`.
- `decimal_as_float` (bool, optional): If True (default), convert `Decimal` to `float`. If False, convert to string for high precision.

**Returns:**
- `dict | list | Any`: A JSON-serializable structure.

## Type Hints

**pyobjtojson** is fully typed and passes strict mypy checking. This provides:

- **Better IDE Support**: Autocomplete and inline documentation
- **Type Safety**: Catch errors before runtime with mypy
- **Clear API**: Type annotations serve as documentation

```python
from typing import Any
from pyobjtojson import obj_to_json

# Your IDE will provide autocomplete and type checking
def serialize_data(data: dict[str, Any]) -> Any:
    return obj_to_json(
        data,
        check_circular=True,    # bool
        decimal_as_float=False  # bool
    )
```

To check types in your project:

```bash
mypy your_code.py
```

## Contributing
Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## License
[MIT License](LICENSE)
