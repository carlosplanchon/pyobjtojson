# Tests for pyobjtojson

This directory contains comprehensive test coverage for the `pyobjtojson` library.

## Test Structure

- **`test_basic_types.py`**: Tests for basic Python types (int, str, list, dict, etc.)
- **`test_circular_references.py`**: Tests for circular reference detection and handling
- **`test_dataclasses.py`**: Tests for dataclass serialization
- **`test_pydantic.py`**: Tests for Pydantic model serialization (v1 and v2)
- **`test_custom_classes.py`**: Tests for custom class serialization
- **`test_edge_cases.py`**: Tests for edge cases and error handling

## Running Tests

### Install development dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Using uv
uv pip install -e ".[dev]"
```

### Run all tests

```bash
pytest
```

### Run specific test file

```bash
pytest tests/test_circular_references.py
```

### Run specific test

```bash
pytest tests/test_circular_references.py::TestCircularReferences::test_simple_circular_dict
```

### Run with coverage report

```bash
pytest --cov=pyobjtojson --cov-report=html
```

This will generate an HTML coverage report in `htmlcov/index.html`.

### Run tests in verbose mode

```bash
pytest -v
```

### Run tests and show print statements

```bash
pytest -s
```

## Test Coverage

The test suite aims for comprehensive coverage including:

- ✅ All basic Python types
- ✅ Nested structures
- ✅ Circular reference detection
- ✅ Dataclasses (simple, nested, with defaults)
- ✅ Pydantic models (v1 and v2)
- ✅ Custom classes with `__dict__`
- ✅ Custom classes with `to_dict()` method
- ✅ Error handling and edge cases
- ✅ Large data structures
- ✅ Unicode and special characters
- ✅ Mixed type collections

## Adding New Tests

When adding new features to `pyobjtojson`, please add corresponding tests:

1. Choose the appropriate test file or create a new one
2. Follow the existing test naming conventions (`test_*`)
3. Use descriptive test names that explain what is being tested
4. Include docstrings for complex tests
5. Test both success and failure cases
