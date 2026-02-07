#!/bin/bash
# Script to check type hints with mypy

echo "Running mypy type checker..."

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

mypy pyobjtojson/__init__.py

if [ $? -eq 0 ]; then
    echo "✓ Type checking passed!"
    exit 0
else
    echo "✗ Type checking failed!"
    exit 1
fi
