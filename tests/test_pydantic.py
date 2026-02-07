#!/usr/bin/env python3
"""Tests for Pydantic model serialization."""

import pytest

# Try to import pydantic, skip tests if not available
pydantic = pytest.importorskip("pydantic", reason="Pydantic not installed")

from pydantic import BaseModel, Field
from pyobjtojson import obj_to_json


class SimpleModel(BaseModel):
    """Simple Pydantic model for testing."""
    name: str
    age: int


class NestedModel(BaseModel):
    """Pydantic model with nested model."""
    title: str
    person: SimpleModel


class ModelWithValidation(BaseModel):
    """Pydantic model with field validation."""
    email: str
    count: int = Field(ge=0, le=100)


class ModelWithDefaults(BaseModel):
    """Pydantic model with default values."""
    required: str
    optional: str = "default"
    number: int = 42


class TestPydantic:
    """Test serialization of Pydantic models."""

    def test_simple_model(self):
        """Test basic Pydantic model serialization."""
        obj = SimpleModel(name="Alice", age=30)
        result = obj_to_json(obj)

        assert result == {"name": "Alice", "age": 30}

    def test_nested_model(self):
        """Test nested Pydantic model serialization."""
        person = SimpleModel(name="Bob", age=25)
        obj = NestedModel(title="Manager", person=person)
        result = obj_to_json(obj)

        assert result == {
            "title": "Manager",
            "person": {"name": "Bob", "age": 25}
        }

    def test_model_with_validation(self):
        """Test Pydantic model with validation."""
        obj = ModelWithValidation(email="test@example.com", count=50)
        result = obj_to_json(obj)

        assert result == {"email": "test@example.com", "count": 50}

    def test_model_with_defaults(self):
        """Test Pydantic model with default values."""
        obj = ModelWithDefaults(required="test")
        result = obj_to_json(obj)

        assert result == {
            "required": "test",
            "optional": "default",
            "number": 42
        }

    def test_list_of_models(self):
        """Test list containing Pydantic models."""
        obj = [
            SimpleModel(name="Alice", age=30),
            SimpleModel(name="Bob", age=25),
            SimpleModel(name="Charlie", age=35)
        ]
        result = obj_to_json(obj)

        assert result == [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]

    def test_dict_with_model_values(self):
        """Test dict with Pydantic model values."""
        obj = {
            "person1": SimpleModel(name="Alice", age=30),
            "person2": SimpleModel(name="Bob", age=25)
        }
        result = obj_to_json(obj)

        assert result == {
            "person1": {"name": "Alice", "age": 30},
            "person2": {"name": "Bob", "age": 25}
        }

    def test_mixed_pydantic_and_dict(self):
        """Test mixed Pydantic models and regular dicts."""
        obj = {
            "model": SimpleModel(name="Alice", age=30),
            "dict": {"key": "value"},
            "list": [1, 2, SimpleModel(name="Bob", age=25)]
        }
        result = obj_to_json(obj)

        assert result == {
            "model": {"name": "Alice", "age": 30},
            "dict": {"key": "value"},
            "list": [1, 2, {"name": "Bob", "age": 25}]
        }
