#!/usr/bin/env python3
"""
Example demonstrating the type hints support in pyobjtojson.

With type hints, IDEs can provide better autocomplete and catch errors early.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pyobjtojson import obj_to_json


def serialize_user_data(user_id: int, name: str, balance: Decimal) -> dict[str, Any]:
    """
    Example function with type hints that serializes user data.

    IDEs will now provide autocomplete for obj_to_json parameters
    and warn about type mismatches.
    """
    user_data = {
        "id": user_id,
        "name": name,
        "balance": balance,
        "created_at": datetime.now()
    }

    # Type hints tell your IDE that obj_to_json returns Any
    # and accepts specific parameters with defaults
    result = obj_to_json(
        user_data,
        check_circular=True,      # IDE knows this is bool
        decimal_as_float=False    # IDE knows this is bool
    )

    return result  # type: ignore[return-value]


def main() -> None:
    """Demonstrate type hints in action."""

    # Your IDE will catch type errors before running the code
    result = serialize_user_data(
        user_id=123,
        name="John Doe",
        balance=Decimal("1234.56")
    )

    print("Serialized user data:")
    print(result)

    # Type hints also help with documentation
    # Hover over obj_to_json in your IDE to see parameter types
    data: dict[str, Any] = {
        "timestamp": datetime.now(),
        "value": 42
    }

    serialized: Any = obj_to_json(data)
    print("\nSerialized data:")
    print(serialized)


if __name__ == "__main__":
    main()
