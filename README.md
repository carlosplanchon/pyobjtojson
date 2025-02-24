# pyobjtojson

A lightweight Python library that simplifies the process of serializing **any** Python object into a JSON-friendly structure without getting tripped up by circular references. With built-in support for dataclasses, Pydantic (v1 & v2), and standard Python collections, **pyobjtojson** helps you convert your objects into a cycle-free, JSON-ready format for logging, storage, or data transfer.

## Features

- **Automatic Circular Reference Detection**  
  Detects and replaces cyclical structures with `"<circular reference>"` to prevent infinite loops.
- **Broad Compatibility**  
  Works seamlessly with dictionaries, lists, custom classes, dataclasses, and Pydantic models (including both `model_dump()` from v2 and `dict()` from v1).
- **Non-Intrusive Serialization**  
  No special inheritance or overrides needed. Uses reflection and standard Python methods (`__dict__`, `asdict()`, `to_dict()`, etc.) where available.
- **Easy to Integrate**  
  Just call `obj_to_json()` on your data structure—no additional configuration required.
  
## Installation

```bash
pip install pyobjtojson
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

obj_to_json(a)
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

## API Reference

- **`obj_to_json(obj) -> dict | list | Any`**  
  Returns a cycle-free structure (nested dictionaries/lists) that is JSON-serializable.

## Contributing
Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## License
[MIT License](LICENSE)
