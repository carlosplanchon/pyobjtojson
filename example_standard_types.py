#!/usr/bin/env python3
"""
Example demonstrating the new standard types support in pyobjtojson.
"""

import json
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID

from pyobjtojson import obj_to_json


class OrderStatus(Enum):
    """Example Enum for order statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


def main():
    print("="*60)
    print("pyobjtojson - Standard Types Support Demo")
    print("="*60)

    # Create a complex object with various standard types
    order = {
        "order_id": UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890"),
        "created_at": datetime(2024, 1, 15, 10, 30, 45),
        "ship_date": date(2024, 1, 20),
        "ship_time": time(14, 0, 0),
        "status": OrderStatus.SHIPPED,

        "customer": {
            "id": UUID("12345678-1234-5678-1234-567812345678"),
            "name": "John Doe",
            "joined": date(2023, 6, 15)
        },

        "items": [
            {
                "product": "Laptop",
                "price": Decimal("1299.99"),
                "quantity": 1
            },
            {
                "product": "Mouse",
                "price": Decimal("29.99"),
                "quantity": 2
            }
        ],

        "total": Decimal("1359.97"),
        "tax": Decimal("108.80"),
        "grand_total": Decimal("1468.77"),

        "attachments": {
            "receipt": b"PDF binary data here...",
            "signature": bytearray(b"Digital signature")
        },

        "tags": {"electronics", "express-shipping", "gift"},

        "file_paths": [
            Path("/var/orders/2024/01/order_12345.json"),
            Path("/var/invoices/2024/01/invoice_12345.pdf")
        ]
    }

    print("\n1. Serializing with Decimal as float (default):")
    print("-" * 60)
    result = obj_to_json(order)
    print(json.dumps(result, indent=2))

    print("\n\n2. Serializing with Decimal as string (high precision):")
    print("-" * 60)
    result_precise = obj_to_json(order, decimal_as_float=False)
    print(json.dumps(result_precise, indent=2))

    print("\n\n3. Demonstrating individual types:")
    print("-" * 60)

    examples = {
        "datetime": datetime(2024, 1, 15, 14, 30, 45, 123456),
        "date": date(2024, 1, 15),
        "time": time(14, 30, 45),
        "uuid": UUID("00000000-0000-0000-0000-000000000000"),
        "decimal_float": Decimal("99.99"),
        "decimal_string": Decimal("123456789.123456789"),
        "bytes": b"Hello",
        "enum": OrderStatus.DELIVERED,
        "path": Path("/home/user/file.txt"),
        "set": {3, 1, 2},
    }

    print("\nDecimal as float:")
    for key, value in examples.items():
        if key.startswith("decimal"):
            result = obj_to_json(value, decimal_as_float=True)
            print(f"  {key}: {value} → {result} (type: {type(result).__name__})")

    print("\nDecimal as string:")
    for key, value in examples.items():
        if key.startswith("decimal"):
            result = obj_to_json(value, decimal_as_float=False)
            print(f"  {key}: {value} → {result} (type: {type(result).__name__})")

    print("\nOther types:")
    for key, value in examples.items():
        if not key.startswith("decimal"):
            result = obj_to_json(value)
            display_value = str(value)[:50]
            display_result = str(result)[:50]
            print(f"  {key}: {display_value} → {display_result}")

    print("\n" + "="*60)
    print("All types are JSON-serializable!")
    print("="*60)


if __name__ == "__main__":
    main()
