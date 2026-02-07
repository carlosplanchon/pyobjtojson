#!/usr/bin/env python3
"""Tests for circular reference detection."""

import pytest
from pyobjtojson import obj_to_json


class TestCircularReferences:
    """Test detection and handling of circular references."""

    def test_simple_circular_dict(self):
        """Test simple circular reference in dict."""
        a = {"name": "A"}
        b = {"name": "B", "ref": a}
        a["ref"] = b

        result = obj_to_json(a, check_circular=True)

        assert result["name"] == "A"
        assert result["ref"]["name"] == "B"
        # The circular reference is detected when 'a' appears again
        assert result["ref"]["ref"] == "<circular reference>"

    def test_self_reference(self):
        """Test object that references itself."""
        obj = {"key": "value"}
        obj["self"] = obj

        result = obj_to_json(obj, check_circular=True)

        assert result["key"] == "value"
        assert result["self"] == "<circular reference>"

    def test_circular_in_list(self):
        """Test circular reference through a list."""
        a = {"name": "A"}
        b = {"name": "B"}
        a["list"] = [b]
        b["parent"] = a

        result = obj_to_json(a, check_circular=True)

        assert result["name"] == "A"
        assert result["list"][0]["name"] == "B"
        # The circular reference is detected when 'a' appears again
        assert result["list"][0]["parent"] == "<circular reference>"

    def test_circular_disabled(self):
        """Test that circular check can be disabled."""
        # When circular check is disabled, the function doesn't use the
        # "<circular reference>" marker. Instead, it creates deeply nested
        # structures until hitting recursion limits (handled as serialization error)
        a = {"name": "A"}
        b = {"name": "B"}
        a["ref"] = b
        b["ref"] = a

        result = obj_to_json(a, check_circular=False)

        # The result should be deeply nested without the circular marker
        # We can verify this by checking a few levels deep
        assert result["name"] == "A"
        assert result["ref"]["name"] == "B"
        assert result["ref"]["ref"]["name"] == "A"
        # Eventually it will either repeat or hit serialization error
        # The key is that it doesn't use "<circular reference>" marker
        assert "<circular reference>" not in str(result)[:1000]  # Check first part

    def test_complex_circular_chain(self):
        """Test circular reference through a longer chain."""
        a = {"name": "A"}
        b = {"name": "B"}
        c = {"name": "C"}
        d = {"name": "D"}

        a["next"] = b
        b["next"] = c
        c["next"] = d
        d["next"] = a  # Creates a cycle back to A

        result = obj_to_json(a, check_circular=True)

        assert result["name"] == "A"
        assert result["next"]["name"] == "B"
        assert result["next"]["next"]["name"] == "C"
        assert result["next"]["next"]["next"]["name"] == "D"
        assert result["next"]["next"]["next"]["next"] == "<circular reference>"

    def test_multiple_references_same_object(self):
        """Test that same object referenced multiple times (not circular)."""
        shared = {"shared": "data"}
        container = {
            "ref1": shared,
            "ref2": shared,
            "ref3": shared
        }

        result = obj_to_json(container, check_circular=True)

        # First reference should be serialized normally
        assert result["ref1"]["shared"] == "data"
        # Subsequent references to the same object are marked as circular
        assert result["ref2"] == "<circular reference>"
        assert result["ref3"] == "<circular reference>"
