#!/usr/bin/env python3
"""Tests for edge cases and error handling."""

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
        """Test dict with non-string keys (should work as-is)."""
        obj = {
            1: "one",
            2: "two",
            (3, 4): "tuple key"
        }
        result = obj_to_json(obj)
        assert result[1] == "one"
        assert result[2] == "two"
        assert result[(3, 4)] == "tuple key"

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
