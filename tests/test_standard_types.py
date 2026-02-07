#!/usr/bin/env python3
"""Tests for standard Python types support (datetime, UUID, Decimal, etc)."""

import base64
import pytest
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum, IntEnum
from pathlib import Path
from uuid import UUID

from pyobjtojson import obj_to_json


class Status(Enum):
    """Example Enum for testing."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class Priority(IntEnum):
    """Example IntEnum for testing."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TestDateTimeTypes:
    """Test datetime, date, and time serialization."""

    def test_datetime(self):
        """Test datetime serialization to ISO format."""
        dt = datetime(2024, 1, 15, 14, 30, 45, 123456)
        result = obj_to_json(dt)
        assert result == "2024-01-15T14:30:45.123456"
        assert isinstance(result, str)

    def test_date(self):
        """Test date serialization to ISO format."""
        d = date(2024, 1, 15)
        result = obj_to_json(d)
        assert result == "2024-01-15"
        assert isinstance(result, str)

    def test_time(self):
        """Test time serialization to ISO format."""
        t = time(14, 30, 45, 123456)
        result = obj_to_json(t)
        assert result == "14:30:45.123456"
        assert isinstance(result, str)

    def test_datetime_in_dict(self):
        """Test datetime in dictionary."""
        data = {
            "created_at": datetime(2024, 1, 15, 10, 0, 0),
            "date": date(2024, 1, 15),
            "time": time(10, 0, 0)
        }
        result = obj_to_json(data)
        assert result["created_at"] == "2024-01-15T10:00:00"
        assert result["date"] == "2024-01-15"
        assert result["time"] == "10:00:00"

    def test_datetime_in_list(self):
        """Test datetime in list."""
        data = [
            datetime(2024, 1, 1, 0, 0, 0),
            datetime(2024, 1, 2, 0, 0, 0),
            datetime(2024, 1, 3, 0, 0, 0)
        ]
        result = obj_to_json(data)
        assert result == [
            "2024-01-01T00:00:00",
            "2024-01-02T00:00:00",
            "2024-01-03T00:00:00"
        ]


class TestUUID:
    """Test UUID serialization."""

    def test_uuid(self):
        """Test UUID serialization to string."""
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        result = obj_to_json(uuid)
        assert result == "12345678-1234-5678-1234-567812345678"
        assert isinstance(result, str)

    def test_uuid_in_dict(self):
        """Test UUID in dictionary."""
        data = {
            "id": UUID("12345678-1234-5678-1234-567812345678"),
            "user_id": UUID("87654321-4321-8765-4321-876543218765")
        }
        result = obj_to_json(data)
        assert result["id"] == "12345678-1234-5678-1234-567812345678"
        assert result["user_id"] == "87654321-4321-8765-4321-876543218765"

    def test_uuid_in_list(self):
        """Test UUID in list."""
        data = [
            UUID("11111111-1111-1111-1111-111111111111"),
            UUID("22222222-2222-2222-2222-222222222222")
        ]
        result = obj_to_json(data)
        assert result == [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222"
        ]


class TestDecimal:
    """Test Decimal serialization."""

    def test_decimal_as_float(self):
        """Test Decimal converted to float (default)."""
        d = Decimal("19.99")
        result = obj_to_json(d)
        assert result == 19.99
        assert isinstance(result, float)

    def test_decimal_as_string(self):
        """Test Decimal converted to string."""
        d = Decimal("19.99")
        result = obj_to_json(d, decimal_as_float=False)
        assert result == "19.99"
        assert isinstance(result, str)

    def test_decimal_high_precision(self):
        """Test Decimal with high precision."""
        d = Decimal("123456789.123456789")
        result_float = obj_to_json(d, decimal_as_float=True)
        result_str = obj_to_json(d, decimal_as_float=False)

        assert isinstance(result_float, float)
        assert isinstance(result_str, str)
        assert result_str == "123456789.123456789"

    def test_decimal_in_dict(self):
        """Test Decimal in dictionary."""
        data = {
            "price": Decimal("99.99"),
            "tax": Decimal("8.25")
        }
        result = obj_to_json(data)
        assert result["price"] == 99.99
        assert result["tax"] == 8.25

    def test_decimal_in_list(self):
        """Test Decimal in list."""
        data = [Decimal("1.11"), Decimal("2.22"), Decimal("3.33")]
        result = obj_to_json(data)
        assert result == [1.11, 2.22, 3.33]


class TestBinaryData:
    """Test bytes and bytearray serialization."""

    def test_bytes(self):
        """Test bytes converted to base64."""
        data = b"Hello, World!"
        result = obj_to_json(data)
        expected = base64.b64encode(data).decode('utf-8')
        assert result == expected
        assert isinstance(result, str)

    def test_bytearray(self):
        """Test bytearray converted to base64."""
        data = bytearray(b"Binary data")
        result = obj_to_json(data)
        expected = base64.b64encode(bytes(data)).decode('utf-8')
        assert result == expected

    def test_bytes_in_dict(self):
        """Test bytes in dictionary."""
        data = {
            "file_content": b"File data",
            "signature": bytearray(b"Signature")
        }
        result = obj_to_json(data)
        assert result["file_content"] == base64.b64encode(b"File data").decode('utf-8')
        assert result["signature"] == base64.b64encode(b"Signature").decode('utf-8')

    def test_empty_bytes(self):
        """Test empty bytes."""
        data = b""
        result = obj_to_json(data)
        assert result == base64.b64encode(b"").decode('utf-8')


class TestEnum:
    """Test Enum serialization."""

    def test_string_enum(self):
        """Test string-based Enum."""
        result = obj_to_json(Status.ACTIVE)
        assert result == "active"

    def test_int_enum(self):
        """Test int-based Enum."""
        result = obj_to_json(Priority.HIGH)
        assert result == 3

    def test_enum_in_dict(self):
        """Test Enum in dictionary."""
        data = {
            "status": Status.PENDING,
            "priority": Priority.MEDIUM
        }
        result = obj_to_json(data)
        assert result["status"] == "pending"
        assert result["priority"] == 2

    def test_enum_in_list(self):
        """Test Enum in list."""
        data = [Status.ACTIVE, Status.INACTIVE, Status.PENDING]
        result = obj_to_json(data)
        assert result == ["active", "inactive", "pending"]


class TestPath:
    """Test Path serialization."""

    def test_path(self):
        """Test Path converted to string."""
        p = Path("/home/user/document.txt")
        result = obj_to_json(p)
        assert result == "/home/user/document.txt"
        assert isinstance(result, str)

    def test_path_relative(self):
        """Test relative Path."""
        p = Path("relative/path/file.py")
        result = obj_to_json(p)
        assert result == "relative/path/file.py"

    def test_path_in_dict(self):
        """Test Path in dictionary."""
        data = {
            "config_file": Path("/etc/config.yaml"),
            "log_file": Path("/var/log/app.log")
        }
        result = obj_to_json(data)
        assert result["config_file"] == "/etc/config.yaml"
        assert result["log_file"] == "/var/log/app.log"


class TestSetTypes:
    """Test set and frozenset serialization."""

    def test_set(self):
        """Test set converted to sorted list."""
        data = {1, 3, 2, 5, 4}
        result = obj_to_json(data)
        assert result == [1, 2, 3, 4, 5]
        assert isinstance(result, list)

    def test_frozenset(self):
        """Test frozenset converted to sorted list."""
        data = frozenset([3, 1, 2])
        result = obj_to_json(data)
        assert result == [1, 2, 3]

    def test_set_strings(self):
        """Test set with strings."""
        data = {"python", "json", "api"}
        result = obj_to_json(data)
        assert result == ["api", "json", "python"]

    def test_set_unsortable(self):
        """Test set with unsortable mixed types."""
        # Mixed types that can't be sorted
        data = {1, "string", 2.5}
        result = obj_to_json(data)
        # Should be a list but order undefined
        assert isinstance(result, list)
        assert len(result) == 3
        assert 1 in result
        assert "string" in result
        assert 2.5 in result

    def test_set_in_dict(self):
        """Test set in dictionary."""
        data = {
            "tags": {"important", "urgent", "review"},
            "numbers": {1, 2, 3}
        }
        result = obj_to_json(data)
        assert result["tags"] == ["important", "review", "urgent"]
        assert result["numbers"] == [1, 2, 3]

    def test_empty_set(self):
        """Test empty set."""
        data = set()
        result = obj_to_json(data)
        assert result == []


class TestMixedStandardTypes:
    """Test combinations of standard types."""

    def test_all_types_together(self):
        """Test dict with all new standard types."""
        data = {
            "timestamp": datetime(2024, 1, 15, 10, 0, 0),
            "date": date(2024, 1, 15),
            "uuid": UUID("12345678-1234-5678-1234-567812345678"),
            "price": Decimal("99.99"),
            "binary": b"data",
            "status": Status.ACTIVE,
            "path": Path("/home/user/file.txt"),
            "tags": {"python", "json"}
        }
        result = obj_to_json(data)

        assert result["timestamp"] == "2024-01-15T10:00:00"
        assert result["date"] == "2024-01-15"
        assert result["uuid"] == "12345678-1234-5678-1234-567812345678"
        assert result["price"] == 99.99
        assert result["binary"] == base64.b64encode(b"data").decode('utf-8')
        assert result["status"] == "active"
        assert result["path"] == "/home/user/file.txt"
        assert result["tags"] == ["json", "python"]

    def test_nested_standard_types(self):
        """Test nested structures with standard types."""
        data = {
            "events": [
                {
                    "id": UUID("11111111-1111-1111-1111-111111111111"),
                    "timestamp": datetime(2024, 1, 1, 12, 0, 0),
                    "status": Status.ACTIVE
                },
                {
                    "id": UUID("22222222-2222-2222-2222-222222222222"),
                    "timestamp": datetime(2024, 1, 2, 12, 0, 0),
                    "status": Status.INACTIVE
                }
            ]
        }
        result = obj_to_json(data)

        assert len(result["events"]) == 2
        assert result["events"][0]["id"] == "11111111-1111-1111-1111-111111111111"
        assert result["events"][0]["timestamp"] == "2024-01-01T12:00:00"
        assert result["events"][0]["status"] == "active"
