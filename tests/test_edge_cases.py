#!/usr/bin/env python3
"""Tests for edge cases and error handling."""

import json
import pytest
from pyobjtojson import obj_to_json


class BrokenClass:
    """Class that raises exceptions."""
    def __init__(self):
        self.value = "ok"

    def __str__(self):
        raise RuntimeError("__str__ is broken")


class BrokenToDict:
    """Class with broken to_dict method."""
    def __init__(self):
        self.value = "ok"

    def to_dict(self):
        raise ValueError("to_dict is broken")


class BrokenDict:
    """Class with broken __dict__ access."""
    def __init__(self):
        pass

    @property
    def __dict__(self):
        raise AttributeError("__dict__ access is broken")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dict(self):
        """Test empty dictionary."""
        assert obj_to_json({}) == {}

    def test_empty_list(self):
        """Test empty list."""
        assert obj_to_json([]) == []

    def test_very_nested_structure(self):
        """Test deeply nested structure."""
        data = {"level": 1}
        current = data
        for i in range(2, 20):
            current["nested"] = {"level": i}
            current = current["nested"]

        result = obj_to_json(data)
        assert result["level"] == 1
        assert result["nested"]["level"] == 2

    def test_large_list(self):
        """Test large list serialization."""
        obj = list(range(10000))
        result = obj_to_json(obj)
        assert len(result) == 10000
        assert result[0] == 0
        assert result[-1] == 9999

    def test_large_dict(self):
        """Test large dictionary serialization."""
        obj = {f"key_{i}": i for i in range(1000)}
        result = obj_to_json(obj)
        assert len(result) == 1000
        assert result["key_0"] == 0
        assert result["key_999"] == 999

    def test_mixed_types_in_list(self):
        """Test list with mixed types including complex objects."""
        class Simple:
            def __init__(self, x):
                self.x = x

        obj = [
            1,
            "string",
            3.14,
            True,
            None,
            [1, 2, 3],
            {"key": "value"},
            Simple(42)
        ]
        result = obj_to_json(obj)

        assert result[0] == 1
        assert result[1] == "string"
        assert result[2] == 3.14
        assert result[3] is True
        assert result[4] is None
        assert result[5] == [1, 2, 3]
        assert result[6] == {"key": "value"}
        assert result[7] == {"x": 42}

    def test_unicode_strings(self):
        """Test unicode strings."""
        obj = {
            "emoji": "🎉🚀✨",
            "chinese": "你好世界",
            "arabic": "مرحبا",
            "mixed": "Hello 世界 🌍"
        }
        result = obj_to_json(obj)
        assert result == obj

    def test_special_string_characters(self):
        """Test strings with special characters."""
        obj = {
            "newline": "line1\nline2",
            "tab": "col1\tcol2",
            "quote": 'He said "hello"',
            "backslash": "path\\to\\file"
        }
        result = obj_to_json(obj)
        assert result == obj

    def test_dict_with_non_string_keys(self):
        """Non-string keys must yield a json.dumps-compatible structure.

        int/float/bool/None keys are kept as-is (json.dumps coerces them to
        strings itself); other keys are stringified so the result never breaks
        json.dumps.
        """
        obj = {
            1: "one",
            2: "two",
            (3, 4): "tuple key"
        }
        result = obj_to_json(obj)

        # Primitive keys pass through unchanged.
        assert result[1] == "one"
        assert result[2] == "two"
        # The tuple key is no longer a valid JSON key, so it is stringified.
        assert (3, 4) not in result
        assert result["[3, 4]"] == "tuple key"

    def test_output_with_non_string_keys_is_json_dumpable(self):
        """The whole point of the fix: json.dumps must not raise."""
        import json

        obj = {(1, 2): "x", frozenset({9}): "y", 5: "z"}
        result = obj_to_json(obj)

        # Must not raise TypeError: keys must be str, int, float, bool or None.
        json.dumps(result)

    def test_typed_keys_are_serialized(self):
        """Common typed keys become their natural scalar string form."""
        from uuid import UUID
        from datetime import datetime, date
        from enum import Enum
        from pathlib import Path

        class Color(Enum):
            RED = "red"

        obj = {
            UUID(int=0): "uuid",
            datetime(2024, 1, 15, 10, 30): "dt",
            date(2024, 1, 15): "date",
            Color.RED: "enum",
            Path("/tmp/x"): "path",
        }
        result = obj_to_json(obj)

        assert result["00000000-0000-0000-0000-000000000000"] == "uuid"
        assert result["2024-01-15T10:30:00"] == "dt"
        assert result["2024-01-15"] == "date"
        assert result["red"] == "enum"
        assert result["/tmp/x"] == "path"

    def test_decimal_key_respects_decimal_as_float(self):
        """Decimal keys follow the same decimal_as_float option as values."""
        from decimal import Decimal

        as_float = obj_to_json({Decimal("9.99"): "v"})
        assert as_float[9.99] == "v"

        as_str = obj_to_json({Decimal("9.99"): "v"}, decimal_as_float=False)
        assert as_str["9.99"] == "v"

    def test_broken_str_method(self):
        """Test object with broken __str__ method."""
        obj = {"broken": BrokenClass()}
        result = obj_to_json(obj)

        # The library uses __dict__ before trying __str__, so it succeeds
        # The broken __str__ is never called
        assert result["broken"]["value"] == "ok"

    def test_broken_to_dict_method(self):
        """Test object with broken to_dict method."""
        obj = {"broken": BrokenToDict()}
        result = obj_to_json(obj)

        # Should fall back to __dict__
        assert result["broken"]["value"] == "ok"

    def test_none_in_collections(self):
        """Test None values in various collections."""
        obj = {
            "list_with_none": [1, None, 3],
            "dict_with_none": {"a": None, "b": 2},
            "nested_none": {"inner": [None, {"key": None}]}
        }
        result = obj_to_json(obj)
        assert result == obj

    def test_boolean_edge_cases(self):
        """Test boolean values (which are also ints in Python)."""
        obj = {
            "true": True,
            "false": False,
            "list": [True, False, True]
        }
        result = obj_to_json(obj)
        assert result["true"] is True
        assert result["false"] is False
        assert result["list"] == [True, False, True]

    def test_number_edge_cases(self):
        """Test edge cases for numbers."""
        obj = {
            "zero": 0,
            "negative": -123,
            "large": 999999999999999999,
            "float_zero": 0.0,
            "negative_float": -3.14,
            "scientific": 1.23e10
        }
        result = obj_to_json(obj)
        assert result == obj


class TestNonFiniteFloats:
    """Test the `non_finite` policy for inf/-inf/nan floats."""

    def test_default_is_null(self):
        """By default non-finite floats become None, producing valid JSON."""
        result = obj_to_json(
            {"a": float("inf"), "b": float("-inf"), "c": float("nan")}
        )
        assert result == {"a": None, "b": None, "c": None}
        # The whole point: strict json.dumps must not raise.
        json.dumps(result, allow_nan=False)

    def test_finite_floats_untouched(self):
        """Finite floats are never altered by the policy."""
        obj = {"x": 1.5, "y": -3.0, "z": 0.0}
        assert obj_to_json(obj) == obj

    def test_string_mode(self):
        """String mode yields the standard-looking token strings."""
        result = obj_to_json(
            {"pos": float("inf"), "neg": float("-inf"), "nan": float("nan")},
            non_finite="string",
        )
        assert result == {"pos": "Infinity", "neg": "-Infinity", "nan": "NaN"}
        json.dumps(result, allow_nan=False)

    def test_keep_mode_preserves_legacy_behavior(self):
        """Keep mode returns the floats unchanged (not strict-JSON valid)."""
        result = obj_to_json({"a": float("inf")}, non_finite="keep")
        assert result["a"] == float("inf")
        assert isinstance(result["a"], float)

    def test_non_finite_decimal(self):
        """Non-finite Decimal values follow the same policy once floated."""
        from decimal import Decimal

        assert obj_to_json(Decimal("Infinity")) is None
        assert obj_to_json(Decimal("NaN"), non_finite="string") == "NaN"
        # With decimal_as_float=False the Decimal is stringified anyway.
        assert obj_to_json(Decimal("Infinity"), decimal_as_float=False) == "Infinity"

    def test_non_finite_dict_key(self):
        """A non-finite float used as a dict key follows the policy too."""
        assert obj_to_json(
            {float("inf"): "v"}, non_finite="string"
        ) == {"Infinity": "v"}
        result = obj_to_json({float("nan"): "v"})  # default null
        assert result == {None: "v"}
        json.dumps(result)  # None key becomes "null", still valid JSON

    def test_non_finite_in_list(self):
        """Non-finite values inside sequences are handled."""
        assert obj_to_json([1.0, float("nan"), float("inf")]) == [1.0, None, None]

    def test_non_finite_in_set(self):
        """Non-finite floats inside sets follow the policy too."""
        assert obj_to_json({float("nan")}) == [None]
        assert obj_to_json({float("inf")}, non_finite="string") == ["Infinity"]

        result = obj_to_json({"s": {float("inf"), 1.0}})
        assert result["s"] == [1.0, None]  # inf sorts after 1.0, then follows policy
        json.dumps(result, allow_nan=False)

    def test_invalid_mode_raises(self):
        """An unknown policy is a programming error and raises ValueError."""
        with pytest.raises(ValueError, match="non_finite must be one of"):
            obj_to_json({"a": 1}, non_finite="bogus")
