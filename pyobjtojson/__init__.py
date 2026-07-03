#!/usr/bin/env python3

import base64
import dataclasses
import math
from collections.abc import Mapping, Sequence
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID


# Allowed policies for representing non-finite floats (inf/-inf/nan).
_NON_FINITE_MODES = ("null", "string", "keep")


def _non_finite_repr(value: float, non_finite: str) -> Any:
    """
    Represent a non-finite float (``inf``, ``-inf`` or ``nan``) according to
    the chosen policy. JSON has no literal for these values, so leaving them
    as-is yields output that either breaks ``json.dumps(..., allow_nan=False)``
    or produces the non-standard ``Infinity``/``NaN`` tokens that strict
    parsers reject.

    - ``"null"``: return ``None`` (matches JavaScript's ``JSON.stringify``).
    - ``"string"``: return ``"Infinity"``, ``"-Infinity"`` or ``"NaN"``.
    - ``"keep"``: return the float unchanged (legacy behavior).

    :param value: A non-finite float.
    :param non_finite: One of the policies above.
    :return: The chosen JSON-compatible representation.
    """
    if non_finite == "null":
        return None
    if non_finite == "string":
        if value != value:  # NaN is the only value not equal to itself
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    return value  # "keep"


def _serialize_for_json(
    obj: Any,
    visited: set[int],
    check_circular: bool = True,
    _skip_circular_check: bool = False,
    decimal_as_float: bool = True,
    non_finite: str = "null"
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
    :param non_finite: How to represent non-finite floats (inf/-inf/nan):
                       "null", "string", or "keep".
    :return: A JSON-serializable structure, or a string if it cannot be
             converted more structurally.
    """

    # Enum → underlying value. This must run before the primitive fast-path
    # below: IntEnum/StrEnum members are also int/str instances, so the
    # fast-path would otherwise return the enum member itself instead of its
    # documented `.value`.
    if isinstance(obj, Enum):
        return obj.value

    # Non-finite floats (inf, -inf, nan) have no JSON representation. Route
    # them through the chosen policy before the primitive fast-path returns
    # them verbatim. bool/int are always finite, so only float needs this.
    if isinstance(obj, float) and not math.isfinite(obj):
        return _non_finite_repr(obj, non_finite)

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
            # A Decimal can also be non-finite (Decimal("inf")/Decimal("nan")),
            # so apply the same policy once converted to float.
            as_float = float(obj)
            if not math.isfinite(as_float):
                return _non_finite_repr(as_float, non_finite)
            return as_float
        return str(obj)

    # bytes, bytearray → base64
    if isinstance(obj, (bytes, bytearray)):
        return base64.b64encode(bytes(obj)).decode('utf-8')

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

    # If circular checking is enabled, see if this object is already on the
    # current traversal path. We track whether *this* frame added the id so we
    # can remove it again on the way out (see the `finally` below). Keeping
    # `visited` as the active path (not every object ever seen) is what makes
    # this real cycle detection: a shared sub-object referenced from two
    # sibling branches (a DAG, not a cycle) must not be flagged circular.
    added_to_visited = False
    if check_circular is True and not _skip_circular_check:
        if obj_id in visited:
            return "<circular reference>"
        visited.add(obj_id)
        added_to_visited = True

    try:
        # Handle Mapping (like dict). Build a new dict item by item,
        # catching errors.
        if isinstance(obj, Mapping):
            result_dict: dict[Any, Any] = {}
            for key, value in obj.items():
                # Keys must also be JSON-compatible, otherwise json.dumps would
                # reject the returned structure even though the values are fine.
                json_key = _serialize_key(
                    key, visited, check_circular=check_circular,
                    decimal_as_float=decimal_as_float, non_finite=non_finite
                )
                try:
                    result_dict[json_key] = _serialize_for_json(
                        value, visited, check_circular=check_circular,
                        decimal_as_float=decimal_as_float, non_finite=non_finite
                    )
                except Exception as exc:
                    result_dict[json_key] = f"<serialization error: {exc}>"
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
                            decimal_as_float=decimal_as_float,
                            non_finite=non_finite
                        )
                    )
                except Exception as exc:
                    result_list.append(f"<serialization error at index {index}: {exc}>")
            return result_list

        # Try Pydantic v2 model_dump(), but fall back if it fails
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            try:
                model_data = obj.model_dump()
                # Skip re-adding the intermediate dict to `visited`; this object
                # is already on the path, so its converted form must not be
                # treated as a separate node.
                return _serialize_for_json(
                    obj=model_data,
                    visited=visited,
                    check_circular=check_circular,
                    _skip_circular_check=True,
                    decimal_as_float=decimal_as_float,
                    non_finite=non_finite
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
                    decimal_as_float=decimal_as_float,
                    non_finite=non_finite
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
                    decimal_as_float=decimal_as_float,
                    non_finite=non_finite
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
                    decimal_as_float=decimal_as_float,
                    non_finite=non_finite
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
                    decimal_as_float=decimal_as_float,
                    non_finite=non_finite
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
    finally:
        # Leave the traversal path: this object is no longer an ancestor of
        # whatever we serialize next, so remove it to allow legitimate reuse
        # of the same instance elsewhere in the tree.
        if added_to_visited:
            visited.discard(obj_id)


def _serialize_key(
    key: Any,
    visited: set[int],
    check_circular: bool = True,
    decimal_as_float: bool = True,
    non_finite: str = "null"
) -> Any:
    """
    Convert a mapping key into something ``json.dumps`` accepts as an object
    key: ``str``, ``int``, ``float``, ``bool`` or ``None``.

    ``json.dumps`` already coerces int/float/bool/None keys to strings itself,
    so those (and plain strings) pass through unchanged. Any other key is run
    through the normal value serializer so that common non-string keys become
    their natural scalar form (``UUID`` → str, ``datetime`` → ISO string,
    ``Enum`` → its value, ``Decimal`` → float/str). If the result is still a
    composite (e.g. a tuple serialized to a list), it is stringified as a last
    resort so the returned structure always survives ``json.dumps``.

    :param key: The mapping key to serialize.
    :param visited: The traversal-path set shared with the value serializer.
    :param check_circular: Whether cycle detection is enabled.
    :param decimal_as_float: If True, convert Decimal to float; otherwise string.
    :param non_finite: Policy for non-finite float keys (see _serialize_for_json).
    :return: A ``json.dumps``-compatible key.
    """
    # json.dumps natively accepts these as object keys, so leave them as-is to
    # preserve its default behavior (e.g. int key 1 -> "1"). A non-finite float
    # key is the one exception: it must follow the non_finite policy.
    if isinstance(key, float) and not math.isfinite(key):
        return _non_finite_repr(key, non_finite)
    if key is None or isinstance(key, (str, bool, int, float)):
        return key

    # Reuse the value machinery so typed keys become their natural scalar form.
    try:
        serialized = _serialize_for_json(
            obj=key,
            visited=visited,
            check_circular=check_circular,
            decimal_as_float=decimal_as_float,
            non_finite=non_finite
        )
    except Exception as exc:
        return f"<unserializable key: {exc}>"

    if serialized is None or isinstance(serialized, (str, bool, int, float)):
        return serialized

    # Composite results (lists/dicts from e.g. a tuple or a custom object)
    # can't be object keys; fall back to a string form.
    try:
        return str(serialized)
    except Exception as exc:
        return f"<unserializable key: {exc}>"


def obj_to_json(
    obj: Any,
    check_circular: bool = True,
    decimal_as_float: bool = True,
    non_finite: str = "null"
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
    :param non_finite: How to represent non-finite floats (inf/-inf/nan), which
                       have no JSON literal. One of:
                       - "null" (default): convert to None, matching JavaScript.
                       - "string": convert to "Infinity"/"-Infinity"/"NaN".
                       - "keep": leave the float as-is (not valid JSON).
    :return: A JSON-serializable structure (dict, list, str, int, float, bool, None).
    """
    if non_finite not in _NON_FINITE_MODES:
        raise ValueError(
            f"non_finite must be one of {_NON_FINITE_MODES}, got {non_finite!r}"
        )
    visited: set[int] = set()
    return _serialize_for_json(
        obj=obj,
        visited=visited,
        check_circular=check_circular,
        decimal_as_float=decimal_as_float,
        non_finite=non_finite
    )
