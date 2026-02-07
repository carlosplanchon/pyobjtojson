#!/usr/bin/env python3

import base64
import dataclasses
from collections.abc import Mapping, Sequence
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


def _serialize_for_json(
    obj: Any,
    visited: set[int],
    check_circular: bool = True,
    _skip_circular_check: bool = False,
    decimal_as_float: bool = True
) -> Any:
    """
    Internal recursion logic that can handle circular references
    using `visited`. This includes careful exception handling so
    partial failures don't break the entire serialization.

    :param obj: The object to serialize.
    :param visited: A set used to track visited objects (for cycle detection).
    :param check_circular: Whether to check for and mark circular references.
    :param _skip_circular_check: Internal flag to skip adding intermediate
                                   conversion results to visited set.
    :param decimal_as_float: If True, convert Decimal to float; otherwise to string.
    :return: A JSON-serializable structure, or a string if it cannot be
             converted more structurally.
    """

    # If it's None, bool, int, float, or str, it's already JSON-serializable.
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj

    # === Standard Python types support ===

    # datetime, date, time → ISO format
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()

    # UUID → string
    if isinstance(obj, UUID):
        return str(obj)

    # Decimal → float or string
    if isinstance(obj, Decimal):
        if decimal_as_float:
            return float(obj)
        return str(obj)

    # bytes, bytearray → base64
    if isinstance(obj, (bytes, bytearray)):
        return base64.b64encode(bytes(obj)).decode('utf-8')

    # Enum → underlying value
    if isinstance(obj, Enum):
        return obj.value

    # Path → string
    if isinstance(obj, Path):
        return str(obj)

    # set, frozenset → list
    if isinstance(obj, (set, frozenset)):
        try:
            # Try to sort if elements are comparable
            return sorted(list(obj))
        except TypeError:
            # If not sortable, convert to list without sorting
            return list(obj)

    obj_id = id(obj)

    # If circular checking is enabled, see if we've already
    # visited this object.
    if check_circular is True and not _skip_circular_check:
        if obj_id in visited:
            return "<circular reference>"
        visited.add(obj_id)

    # Handle Mapping (like dict). Build a new dict item by item,
    # catching errors.
    if isinstance(obj, Mapping):
        result_dict: dict[Any, Any] = {}
        for key, value in obj.items():
            try:
                result_dict[key] = _serialize_for_json(
                    value, visited, check_circular=check_circular,
                    decimal_as_float=decimal_as_float
                )
            except Exception as exc:
                result_dict[key] = f"<serialization error: {exc}>"
        return result_dict

    # Handle Sequence (like list/tuple), but not string.
    if isinstance(obj, Sequence) and not isinstance(obj, str):
        result_list: list[Any] = []
        for index, item in enumerate(obj):
            try:
                result_list.append(
                    _serialize_for_json(
                        obj=item,
                        visited=visited,
                        check_circular=check_circular,
                        decimal_as_float=decimal_as_float
                    )
                )
            except Exception as exc:
                result_list.append(f"<serialization error at index {index}: {exc}>")
        return result_list

    # Try Pydantic v2 model_dump(), but fall back if it fails
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            model_data = obj.model_dump()
            # Skip circular check for the intermediate dict to avoid false positives
            # when Python reuses memory addresses
            return _serialize_for_json(
                obj=model_data,
                visited=visited,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # Try Pydantic v1 .dict(), but fall back if it fails
    if hasattr(obj, "dict") and callable(obj.dict):
        try:
            dict_data = obj.dict()
            # Skip circular check for the intermediate dict
            return _serialize_for_json(
                obj=dict_data,
                visited=visited,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If it's a dataclass, convert it using asdict(), but handle exceptions
    if dataclasses.is_dataclass(obj):
        try:
            # is_dataclass can return True for both instances and types,
            # but we only process instances here
            dc_data = dataclasses.asdict(obj)  # type: ignore[arg-type]
            # Skip circular check for the intermediate dict
            return _serialize_for_json(
                obj=dc_data,
                visited=visited,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If there's a custom .to_dict() method, try that
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            custom_dict_data = obj.to_dict()
            # Skip circular check for the intermediate dict
            return _serialize_for_json(
                obj=custom_dict_data,
                visited=visited,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float
            )
        except Exception:
            # Fall through to next check if this fails
            ...

    # If the object has a __dict__, recurse into that
    if hasattr(obj, "__dict__"):
        try:
            # Skip circular check for the __dict__ to avoid false positives
            return _serialize_for_json(
                obj=obj.__dict__,
                visited=visited,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float
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


def obj_to_json(
    obj: Any,
    check_circular: bool = True,
    decimal_as_float: bool = True
) -> Any:
    """
    Public-facing function that starts with a fresh visited set
    to handle cycles (if `check_circular=True`). Calls the internal
    _serialize_for_json.

    Supports standard Python types including:
    - datetime, date, time (converted to ISO format)
    - UUID (converted to string)
    - Decimal (converted to float or string based on decimal_as_float)
    - bytes, bytearray (converted to base64)
    - Enum (converted to underlying value)
    - Path (converted to string)
    - set, frozenset (converted to sorted list)

    :param obj: The object to serialize to JSON-like structures.
    :param check_circular: If True, detect and mark circular references.
    :param decimal_as_float: If True, convert Decimal to float; otherwise to string.
                             Default is True.
    :return: A JSON-serializable structure (dict, list, str, int, float, bool, None).
    """
    visited: set[int] = set()
    return _serialize_for_json(
        obj=obj,
        visited=visited,
        check_circular=check_circular,
        decimal_as_float=decimal_as_float
    )
