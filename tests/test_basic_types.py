#!/usr/bin/env python3
"""Tests for basic Python types serialization."""

import pytest
from pyobjtojson import obj_to_json


class TestBasicTypes:
    """Test serialization of basic Python types."""

    def test_none(self):
        """Test that None is serialized correctly."""
        assert obj_to_json(None) is None

    def test_bool(self):
        """Test boolean serialization."""
        assert obj_to_json(True) is True
        assert obj_to_json(False) is False

    def test_int(self):
        """Test integer serialization."""
        assert obj_to_json(42) == 42
        assert obj_to_json(0) == 0
        assert obj_to_json(-100) == -100

    def test_float(self):
        """Test float serialization."""
        assert obj_to_json(3.14) == 3.14
        assert obj_to_json(0.0) == 0.0
        assert obj_to_json(-2.5) == -2.5

    def test_string(self):
        """Test string serialization."""
        assert obj_to_json("hello") == "hello"
        assert obj_to_json("") == ""
        assert obj_to_json("with spaces") == "with spaces"

    def test_list(self):
        """Test list serialization."""
        assert obj_to_json([1, 2, 3]) == [1, 2, 3]
        assert obj_to_json([]) == []
        assert obj_to_json([1, "two", 3.0, True, None]) == [1, "two", 3.0, True, None]

    def test_tuple(self):
        """Test tuple serialization (should convert to list)."""
        result = obj_to_json((1, 2, 3))
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_dict(self):
        """Test dictionary serialization."""
        assert obj_to_json({"a": 1, "b": 2}) == {"a": 1, "b": 2}
        assert obj_to_json({}) == {}

    def test_nested_structures(self):
        """Test nested lists and dicts."""
        data = {
            "list": [1, 2, [3, 4]],
            "dict": {"nested": {"deep": "value"}},
            "mixed": [{"a": 1}, {"b": 2}]
        }
        result = obj_to_json(data)
        assert result == data
