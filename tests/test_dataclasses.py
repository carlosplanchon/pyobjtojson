#!/usr/bin/env python3
"""Tests for dataclass serialization."""

import pytest
from dataclasses import dataclass, field
from pyobjtojson import obj_to_json


@dataclass
class SimpleDataClass:
    """Simple dataclass for testing."""
    name: str
    age: int


@dataclass
class NestedDataClass:
    """Dataclass with nested dataclass."""
    title: str
    person: SimpleDataClass


@dataclass
class DataClassWithList:
    """Dataclass with list field."""
    name: str
    items: list[int]


@dataclass
class DataClassWithDefaults:
    """Dataclass with default values."""
    required: str
    optional: str = "default"
    number: int = 42


@dataclass
class CircularDataClass:
    """Dataclass that can have circular references."""
    name: str
    parent: "CircularDataClass | None" = None


class TestDataclasses:
    """Test serialization of dataclasses."""

    def test_simple_dataclass(self):
        """Test basic dataclass serialization."""
        obj = SimpleDataClass(name="Alice", age=30)
        result = obj_to_json(obj)

        assert result == {"name": "Alice", "age": 30}

    def test_nested_dataclass(self):
        """Test nested dataclass serialization."""
        person = SimpleDataClass(name="Bob", age=25)
        obj = NestedDataClass(title="Manager", person=person)
        result = obj_to_json(obj)

        assert result == {
            "title": "Manager",
            "person": {"name": "Bob", "age": 25}
        }

    def test_dataclass_with_list(self):
        """Test dataclass with list field."""
        obj = DataClassWithList(name="shopping", items=[1, 2, 3])
        result = obj_to_json(obj)

        assert result == {"name": "shopping", "items": [1, 2, 3]}

    def test_dataclass_with_defaults(self):
        """Test dataclass with default values."""
        obj = DataClassWithDefaults(required="test")
        result = obj_to_json(obj)

        assert result == {
            "required": "test",
            "optional": "default",
            "number": 42
        }

    def test_dataclass_circular_reference(self):
        """Test dataclass with circular reference."""
        parent = CircularDataClass(name="Parent")
        child = CircularDataClass(name="Child", parent=parent)
        parent.parent = child  # Create circular reference

        result = obj_to_json(parent, check_circular=True)

        assert result["name"] == "Parent"
        assert result["parent"]["name"] == "Child"
        # The circular reference is detected when 'parent' appears again
        assert result["parent"]["parent"] == "<circular reference>"

    def test_list_of_dataclasses(self):
        """Test list containing dataclasses."""
        obj = [
            SimpleDataClass(name="Alice", age=30),
            SimpleDataClass(name="Bob", age=25),
            SimpleDataClass(name="Charlie", age=35)
        ]
        result = obj_to_json(obj)

        assert result == [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]

    def test_dict_with_dataclass_values(self):
        """Test dict with dataclass values."""
        obj = {
            "person1": SimpleDataClass(name="Alice", age=30),
            "person2": SimpleDataClass(name="Bob", age=25)
        }
        result = obj_to_json(obj)

        assert result == {
            "person1": {"name": "Alice", "age": 30},
            "person2": {"name": "Bob", "age": 25}
        }
