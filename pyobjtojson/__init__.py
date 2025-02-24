#!/usr/bin/env python3

import dataclasses
from collections.abc import Mapping, Sequence


def _serialize_for_json(obj, visited):
    """
    Internal recursion logic that can
    handle circular references using `visited`.
    """
    # If it's None, bool, int, float, or str, it’s already serializable
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # If we've seen this object already, it's a circular reference
    obj_id = id(obj)
    if obj_id in visited:
        return "<circular reference>"
    visited.add(obj_id)

    # If it's a Mapping (like dict), recursively process
    if isinstance(obj, Mapping):
        return {
            key: _serialize_for_json(value, visited)
            for key, value in obj.items()
        }

    # If it's a Sequence (like list or tuple) but not a string
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        return [_serialize_for_json(item, visited) for item in obj]

    # Check for Pydantic v2's model_dump()
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return _serialize_for_json(obj.model_dump(), visited)

    # Check for Pydantic v1's dict()
    if hasattr(obj, "dict") and callable(obj.dict):
        return _serialize_for_json(obj.dict(), visited)

    # If it's a dataclass, convert it using dataclasses.asdict()
    if dataclasses.is_dataclass(obj):
        return _serialize_for_json(dataclasses.asdict(obj), visited)

    # If there's a custom .to_dict() method
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return _serialize_for_json(obj.to_dict(), visited)

    # If the object has a __dict__, serialize that
    if hasattr(obj, "__dict__"):
        return _serialize_for_json(obj.__dict__, visited)

    # If we get here, just convert to string (as a last resort)
    return str(obj)


def obj_to_json(obj):
    """
    Public-facing function that starts with a fresh visited set
    to handle cycles. This calls the internal _serialize_for_json.
    """
    return _serialize_for_json(obj, visited=set())
