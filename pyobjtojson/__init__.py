#!/usr/bin/env python3

import dataclasses
from collections.abc import Mapping, Sequence


def _serialize_for_json(obj, visited, check_circular=True):
    """
    Internal recursion logic that can handle circular references
    using `visited`. This includes careful exception handling so
    partial failures don't break the entire serialization.

    :param obj: The object to serialize.
    :param visited: A set used to track visited objects (for cycle detection).
    :param check_circular: Whether to check for and mark circular references.
    :return: A JSON-serializable structure, or a string if it cannot be
             converted more structurally.
    """

    # If it's None, bool, int, float, or str, it’s already JSON-serializable.
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    obj_id = id(obj)

    # If circular checking is enabled, see if we've already
    # visited this object.
    if check_circular is True:
        if obj_id in visited:
            return "<circular reference>"
        visited.add(obj_id)

    # Handle Mapping (like dict). Build a new dict item by item,
    # catching errors.
    if isinstance(obj, Mapping):
        result = {}
        for key, value in obj.items():
            try:
                result[key] = _serialize_for_json(
                    value, visited, check_circular=check_circular
                )
            except Exception as exc:
                result[key] = f"<serialization error: {exc}>"
        return result

    # Handle Sequence (like list/tuple), but not string.
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        result = []
        for index, item in enumerate(obj):
            try:
                result.append(
                    _serialize_for_json(
                        obj=item,
                        visited=visited,
                        check_circular=check_circular
                    )
                )
            except Exception as exc:
                result.append(f"<serialization error at index {index}: {exc}>")
        return result

    # Try Pydantic v2 model_dump(), but fall back if it fails
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            model_data = obj.model_dump()
            return _serialize_for_json(
                obj=model_data,
                visited=visited,
                check_circular=check_circular
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # Try Pydantic v1 .dict(), but fall back if it fails
    if hasattr(obj, "dict") and callable(obj.dict):
        try:
            dict_data = obj.dict()
            return _serialize_for_json(
                obj=dict_data,
                visited=visited,
                check_circular=check_circular
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If it's a dataclass, convert it using asdict(), but handle exceptions
    if dataclasses.is_dataclass(obj):
        try:
            dc_data = dataclasses.asdict(obj)
            return _serialize_for_json(
                obj=dc_data,
                visited=visited,
                check_circular=check_circular
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If there's a custom .to_dict() method, try that
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            custom_dict_data = obj.to_dict()
            return _serialize_for_json(
                obj=custom_dict_data,
                visited=visited,
                check_circular=check_circular
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If the object has a __dict__, recurse into that
    if hasattr(obj, "__dict__"):
        try:
            return _serialize_for_json(
                obj=obj.__dict__,
                visited=visited,
                check_circular=check_circular
            )
        except Exception:
            # Fall through to next check if this fails
            pass

    # Last resort: convert to string, but even this can fail
    # if __str__ is broken
    try:
        return str(obj)
    except Exception as exc:
        # If that fails, return a generic serialization error.
        return f"<serialization error: {exc}>"


def obj_to_json(obj, check_circular=True):
    """
    Public-facing function that starts with a fresh visited set
    to handle cycles (if `check_circular=True`). Calls the internal
    _serialize_for_json.

    :param obj: The object to serialize to JSON-like structures.
    :param check_circular: If True, detect and mark circular references.
    """
    visited = set()
    return _serialize_for_json(
        obj=obj,
        visited=visited,
        check_circular=check_circular
    )
