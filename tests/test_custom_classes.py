#!/usr/bin/env python3
"""Tests for custom class serialization."""

import pytest
from pyobjtojson import obj_to_json


class SimpleClass:
    """Simple class with __dict__."""
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


class ClassWithToDict:
    """Class with custom to_dict method."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def to_dict(self):
        return {"x": self.x, "y": self.y, "sum": self.x + self.y}


class ClassWithPrivateAttrs:
    """Class with private attributes."""
    def __init__(self, public: str, private: str):
        self.public = public
        self._private = private
        self.__very_private = "secret"


class NestedCustomClass:
    """Custom class with nested custom class."""
    def __init__(self, name: str, child: SimpleClass):
        self.name = name
        self.child = child


class ClassWithProperties:
    """Class with @property decorators."""
    def __init__(self, value: int):
        self._value = value

    @property
    def doubled(self):
        return self._value * 2


class ClassWithSlots:
    """Class using __slots__."""
    __slots__ = ['x', 'y']

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class TestCustomClasses:
    """Test serialization of custom classes."""

    def test_simple_class(self):
        """Test basic custom class with __dict__."""
        obj = SimpleClass(name="test", value=42)
        result = obj_to_json(obj)

        assert result == {"name": "test", "value": 42}

    def test_class_with_to_dict(self):
        """Test class with custom to_dict method."""
        obj = ClassWithToDict(x=3, y=4)
        result = obj_to_json(obj)

        assert result == {"x": 3, "y": 4, "sum": 7}

    def test_class_with_private_attrs(self):
        """Test class with private attributes (they should be included)."""
        obj = ClassWithPrivateAttrs(public="visible", private="hidden")
        result = obj_to_json(obj)

        # All attributes in __dict__ should be serialized
        assert result["public"] == "visible"
        assert "_private" in result
        assert result["_private"] == "hidden"

    def test_nested_custom_class(self):
        """Test nested custom classes."""
        child = SimpleClass(name="child", value=10)
        obj = NestedCustomClass(name="parent", child=child)
        result = obj_to_json(obj)

        assert result == {
            "name": "parent",
            "child": {"name": "child", "value": 10}
        }

    def test_class_with_properties(self):
        """Test class with @property (properties are not in __dict__)."""
        obj = ClassWithProperties(value=5)
        result = obj_to_json(obj)

        # Only _value should be in the result, not the property
        assert "_value" in result
        assert result["_value"] == 5
        assert "doubled" not in result  # Properties are not serialized

    def test_class_with_slots(self):
        """Test class using __slots__ (no __dict__)."""
        obj = ClassWithSlots(x=10, y=20)
        result = obj_to_json(obj)

        # Classes with __slots__ will fall back to str()
        assert isinstance(result, str)

    def test_list_of_custom_objects(self):
        """Test list containing custom objects."""
        obj = [
            SimpleClass(name="first", value=1),
            SimpleClass(name="second", value=2),
            SimpleClass(name="third", value=3)
        ]
        result = obj_to_json(obj)

        assert result == [
            {"name": "first", "value": 1},
            {"name": "second", "value": 2},
            {"name": "third", "value": 3}
        ]

    def test_dict_with_custom_objects(self):
        """Test dict with custom object values."""
        obj = {
            "obj1": SimpleClass(name="first", value=1),
            "obj2": SimpleClass(name="second", value=2)
        }
        result = obj_to_json(obj)

        assert result == {
            "obj1": {"name": "first", "value": 1},
            "obj2": {"name": "second", "value": 2}
        }

    def test_circular_custom_class(self):
        """Test circular reference in custom classes."""
        obj1 = SimpleClass(name="obj1", value=1)
        obj2 = SimpleClass(name="obj2", value=2)
        obj1.ref = obj2
        obj2.ref = obj1

        result = obj_to_json(obj1, check_circular=True)

        assert result["name"] == "obj1"
        assert result["ref"]["name"] == "obj2"
        assert result["ref"]["ref"] == "<circular reference>"
