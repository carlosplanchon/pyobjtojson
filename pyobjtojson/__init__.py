#!/usr/bin/env python3

import base64
import dataclasses
import math
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Literal, get_args
from uuid import UUID


# Policy names for representing non-finite floats (inf/-inf/nan). Exposed as a
# Literal so callers get IDE completion and static checking while still passing
# plain strings. `_NON_FINITE_MODES` is derived from it for the runtime guard,
# keeping a single source of truth.
NonFinite = Literal["null", "string", "keep"]
_NON_FINITE_MODES = get_args(NonFinite)


def _non_finite_repr(value: float, non_finite: NonFinite) -> Any:
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


class _TraversalState:
    """
    Mutable bookkeeping for a single obj_to_json() call.

    - ``path``: ids of the objects on the current traversal path. An id seen
      again while it is still on the path is a genuine cycle.
    - ``memo``: id -> (obj, result) for objects whose serialization already
      completed without emitting any circular-reference marker. A shared
      sub-object (a DAG, not a cycle) is serialized once and the cached result
      is reused for every other reference, keeping the traversal linear.
      Re-walking shared subtrees per reference is exponential in the nesting
      depth of the sharing. The object itself is stored next to its result to
      keep it alive: ids of dead objects can be recycled by the interpreter
      and would otherwise let an unrelated new object wrongly hit the cache.
    - ``markers``: count of "<circular reference>" markers emitted so far.
      A result containing a marker depends on where the object sits relative
      to the marked ancestor, so only marker-free subtrees are memoized.
    """

    __slots__ = ("path", "memo", "markers")

    def __init__(self) -> None:
        self.path: set[int] = set()
        self.memo: dict[int, tuple[Any, Any]] = {}
        self.markers: int = 0


def _serialize_for_json(
    obj: Any,
    state: _TraversalState,
    check_circular: bool = True,
    _skip_circular_check: bool = False,
    decimal_as_float: bool = True,
    non_finite: NonFinite = "null"
) -> Any:
    """
    Internal recursion logic that can handle circular references using the
    traversal `state`. This includes careful exception handling so partial
    failures don't break the entire serialization.

    :param obj: The object to serialize.
    :param state: Per-call traversal state: the active path (for cycle
                  detection), the memo of completed subtrees (for shared
                  references) and the circular-marker count.
    :param check_circular: Whether to check for and mark circular references.
    :param _skip_circular_check: Internal flag to skip adding intermediate
                                   conversion results to the traversal path.
    :param decimal_as_float: If True, convert Decimal to float; otherwise to string.
    :param non_finite: How to represent non-finite floats (inf/-inf/nan):
                       "null", "string", or "keep".
    :return: A JSON-serializable structure, or a string if it cannot be
             converted more structurally.
    """

    # Enum → underlying value. This must run before the primitive fast-path
    # below: IntEnum/StrEnum members are also int/str instances, so the
    # fast-path would otherwise return the enum member itself instead of its
    # documented `.value`. The value is re-serialized rather than returned
    # verbatim: enum values are not always JSON primitives (datetime, Decimal,
    # tuples, non-finite floats, ...) and must get the same conversions and
    # policies as the same value anywhere else in the structure.
    if isinstance(obj, Enum):
        return _serialize_for_json(
            obj=obj.value,
            state=state,
            check_circular=check_circular,
            decimal_as_float=decimal_as_float,
            non_finite=non_finite
        )

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
            # A Decimal can be non-finite. NaN must be detected on the Decimal
            # itself: float(Decimal("sNaN")) raises ValueError (a signaling
            # NaN has no float conversion), so converting first would crash
            # before the policy could run. is_nan() covers both NaN and sNaN.
            if obj.is_nan():
                return _non_finite_repr(float("nan"), non_finite)
            if obj.is_infinite():
                return _non_finite_repr(
                    -math.inf if obj.is_signed() else math.inf, non_finite
                )
            as_float = float(obj)
            if not math.isfinite(as_float):
                # The Decimal itself is finite but too large for a float
                # (e.g. Decimal("1e500") overflows to inf). Applying the
                # non_finite policy would silently destroy a real value, so
                # degrade to the exact string form instead, as
                # decimal_as_float=False would.
                return str(obj)
            return as_float
        return str(obj)

    # bytes, bytearray → base64
    if isinstance(obj, (bytes, bytearray)):
        return base64.b64encode(bytes(obj)).decode('utf-8')

    # Path → string
    if isinstance(obj, Path):
        return str(obj)

    obj_id = id(obj)

    # If circular checking is enabled, see if this object is already on the
    # current traversal path. The membership check runs even for intermediate
    # conversion results (_skip_circular_check=True): a conversion method such
    # as to_dict() or model_dump() can return an object that is itself on the
    # path (`return self`, or two objects whose to_dict() return each other),
    # and without the check those cycles would recurse until the interpreter
    # stack is exhausted. The flag only skips *adding* the intermediate to the
    # path, so the converted form of an object is not treated as a separate
    # node. We track whether *this* frame added the id so we can remove it
    # again on the way out (see the `finally` below). Keeping `state.path` as
    # the active path (not every object ever seen) is what makes this real
    # cycle detection: a shared sub-object referenced from two sibling
    # branches (a DAG, not a cycle) must not be flagged circular.
    added_to_path = False
    if check_circular is True:
        if obj_id in state.path:
            state.markers += 1
            return "<circular reference>"
        # Already serialized somewhere outside the current path: reuse that
        # result instead of walking the subtree again. Without this, every
        # reference to a shared subtree re-walks it and nested sharing
        # (a diamond DAG) blows up exponentially.
        cached = state.memo.get(obj_id)
        if cached is not None:
            return cached[1]
        if not _skip_circular_check:
            state.path.add(obj_id)
            added_to_path = True

    markers_before = state.markers
    try:
        result = _serialize_container(
            obj=obj,
            state=state,
            check_circular=check_circular,
            decimal_as_float=decimal_as_float,
            non_finite=non_finite
        )
        if added_to_path and state.markers == markers_before:
            # No circular marker was emitted below this object, so its result
            # is position-independent and can be reused for every other
            # reference to the same object.
            state.memo[obj_id] = (obj, result)
        return result
    finally:
        # Leave the traversal path: this object is no longer an ancestor of
        # whatever we serialize next, so remove it to allow legitimate reuse
        # of the same instance elsewhere in the tree.
        if added_to_path:
            state.path.discard(obj_id)


def _serialize_container(
    obj: Any,
    state: _TraversalState,
    check_circular: bool = True,
    decimal_as_float: bool = True,
    non_finite: NonFinite = "null"
) -> Any:
    """
    Dispatch for container-like and structured objects: mappings, sequences,
    sets, Pydantic models, dataclasses, objects with to_dict() and plain
    __dict__ objects, with a str() fallback. Called by _serialize_for_json
    once the scalar fast paths did not match and the object was registered on
    the traversal path.
    """
    # Handle Mapping (like dict). Build a new dict item by item,
    # catching errors.
    if isinstance(obj, Mapping):
        result_dict: dict[Any, Any] = {}
        for key, value in obj.items():
            # Keys must also be JSON-compatible, otherwise json.dumps would
            # reject the returned structure even though the values are fine.
            json_key = _serialize_key(
                key, state, check_circular=check_circular,
                decimal_as_float=decimal_as_float, non_finite=non_finite
            )
            try:
                result_dict[json_key] = _serialize_for_json(
                    value, state, check_circular=check_circular,
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
                        state=state,
                        check_circular=check_circular,
                        decimal_as_float=decimal_as_float,
                        non_finite=non_finite
                    )
                )
            except Exception as exc:
                result_list.append(f"<serialization error at index {index}: {exc}>")
        return result_list

    # set, frozenset → list. Sort first, while the raw elements are still
    # comparable, so the output stays deterministic; then serialize each
    # element like any other value so sets get the same conversions and
    # policies (datetime, Decimal, Enum, non_finite, ...) as lists do.
    if isinstance(obj, (set, frozenset)):
        try:
            # Try to sort if elements are comparable
            elements = sorted(obj)
        except TypeError:
            # If not sortable, convert to list without sorting
            elements = list(obj)
        set_items: list[Any] = []
        for index, item in enumerate(elements):
            try:
                set_items.append(
                    _serialize_for_json(
                        obj=item,
                        state=state,
                        check_circular=check_circular,
                        decimal_as_float=decimal_as_float,
                        non_finite=non_finite
                    )
                )
            except Exception as exc:
                set_items.append(f"<serialization error at index {index}: {exc}>")
        return set_items

    # Structured objects: try each conversion strategy in order and recurse
    # into the first one that succeeds. Every strategy yields an intermediate
    # stand-in for `obj` itself, so the recursion skips re-adding it to the
    # path (_skip_circular_check=True): the converted form must not be
    # treated as a separate node. `applies` is a thunk so a strategy's
    # attributes are only probed once every earlier strategy has been ruled
    # out, exactly like the if-chain this replaces.
    converters: tuple[tuple[Callable[[], bool], Callable[[], Any]], ...] = (
        # Pydantic v2
        (
            lambda: callable(getattr(obj, "model_dump", None)),
            lambda: obj.model_dump(),
        ),
        # Pydantic v1
        (
            lambda: callable(getattr(obj, "dict", None)),
            lambda: obj.dict(),
        ),
        # Dataclass instances (is_dataclass is also True for the class
        # itself; asdict then raises and falls through to the next strategy)
        (
            lambda: dataclasses.is_dataclass(obj),
            lambda: dataclasses.asdict(obj),
        ),
        # Custom to_dict()
        (
            lambda: callable(getattr(obj, "to_dict", None)),
            lambda: obj.to_dict(),
        ),
        # Plain object namespace
        (
            lambda: hasattr(obj, "__dict__"),
            lambda: obj.__dict__,
        ),
    )
    for applies, convert in converters:
        if not applies():
            continue
        try:
            return _serialize_for_json(
                obj=convert(),
                state=state,
                check_circular=check_circular,
                _skip_circular_check=True,
                decimal_as_float=decimal_as_float,
                non_finite=non_finite
            )
        except Exception:
            # Converting or serializing this form failed: fall through to
            # the next strategy
            continue

    # Last resort: convert to string, but even this can fail
    # if __str__ is broken
    try:
        return str(obj)
    except Exception as exc:
        # If that fails, return a generic serialization error.
        return f"<serialization error: {exc}>"


def _serialize_key(
    key: Any,
    state: _TraversalState,
    check_circular: bool = True,
    decimal_as_float: bool = True,
    non_finite: NonFinite = "null"
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
    :param state: The traversal state shared with the value serializer.
    :param check_circular: Whether cycle detection is enabled.
    :param decimal_as_float: If True, convert Decimal to float; otherwise string.
    :param non_finite: Policy for non-finite float keys (see _serialize_for_json).
    :return: A ``json.dumps``-compatible key.
    """
    # json.dumps natively accepts these as object keys, so leave them as-is to
    # preserve its default behavior (e.g. int key 1 -> "1"). Two exceptions:
    # a non-finite float key must follow the non_finite policy, and Enum keys
    # must skip the fast-path entirely. IntEnum/StrEnum (and other int/str/
    # float mixin) members are also instances of their mixin primitive, so
    # without the Enum check they would pass through as the enum member
    # itself instead of its documented `.value`, the same subclass-shadowing
    # issue _serialize_for_json guards against for values.
    if not isinstance(key, Enum):
        if isinstance(key, float) and not math.isfinite(key):
            return _non_finite_repr(key, non_finite)
        if key is None or isinstance(key, (str, bool, int, float)):
            return key

    # Reuse the value machinery so typed keys become their natural scalar form.
    try:
        serialized = _serialize_for_json(
            obj=key,
            state=state,
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
    non_finite: NonFinite = "null"
) -> Any:
    """
    Public-facing function that starts with fresh traversal state
    to handle cycles (if `check_circular=True`). Calls the internal
    _serialize_for_json.

    A sub-object referenced from several places (a DAG) is serialized once
    and the converted result is reused for every occurrence, so shared
    structures stay linear to serialize.

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
    state = _TraversalState()
    return _serialize_for_json(
        obj=obj,
        state=state,
        check_circular=check_circular,
        decimal_as_float=decimal_as_float,
        non_finite=non_finite
    )
