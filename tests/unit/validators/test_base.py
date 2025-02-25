"""Tests for the base validator class."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.base import BaseValidator


# Test implementation of BaseValidator
class TestValidator(BaseValidator):
    """Test validator implementation."""

    def validate(self, data, strict=False):
        """Implement abstract validate method."""
        self._validate_required_fields(data, self.get_required_fields())

    def get_defaults(self):
        """Implement abstract get_defaults method."""
        return {"field1": "default1", "field2": "default2"}

    def get_required_fields(self):
        """Implement abstract get_required_fields method."""
        return ["required_field"]


def test_validator_initialization():
    """Test validator initialization."""
    schema = {"type": "object", "properties": {}}
    validator = TestValidator(schema)
    assert validator.schema == schema


def test_validate_required_fields():
    """Test validation of required fields."""
    validator = TestValidator({})
    data = {"required_field": "value"}
    validator.validate(data)  # Should not raise


def test_validate_missing_required_fields():
    """Test validation with missing required fields."""
    validator = TestValidator({})
    data = {"optional_field": "value"}
    with pytest.raises(ValidationError, match="Missing required fields"):
        validator.validate(data)


def test_validate_field_type():
    """Test field type validation."""
    validator = TestValidator({})
    with pytest.raises(ValidationError, match="Invalid type for field"):
        validator._validate_field_type(123, str, "string_field")


def test_validate_enum():
    """Test enum validation."""
    validator = TestValidator({})
    valid_values = ["a", "b", "c"]
    with pytest.raises(ValidationError, match="Invalid value for field"):
        validator._validate_enum("d", valid_values, "enum_field")


def test_validate_range():
    """Test range validation."""
    validator = TestValidator({})
    with pytest.raises(ValidationError, match="must be >="):
        validator._validate_range(5, minimum=10, field="range_field")
    with pytest.raises(ValidationError, match="must be <="):
        validator._validate_range(15, maximum=10, field="range_field")


def test_validate_string_length():
    """Test string length validation."""
    validator = TestValidator({})
    with pytest.raises(ValidationError, match="Length of field"):
        validator._validate_string_length("short", min_length=10, field="string_field")
    with pytest.raises(ValidationError, match="Length of field"):
        validator._validate_string_length("too_long", max_length=5, field="string_field")


def test_validate_pattern():
    """Test pattern validation."""
    validator = TestValidator({})
    with pytest.raises(ValidationError, match="must match pattern"):
        validator._validate_pattern("123", r"^[a-z]+$", "pattern_field")


def test_get_defaults():
    """Test getting default values."""
    validator = TestValidator({})
    defaults = validator.get_defaults()
    assert "field1" in defaults
    assert "field2" in defaults


def test_get_required_fields():
    """Test getting required fields."""
    validator = TestValidator({})
    required = validator.get_required_fields()
    assert "required_field" in required


def test_validator_string_representation():
    """Test validator string representation."""
    validator = TestValidator({})
    assert str(validator) == "TestValidator()"


def test_validate_multiple_fields():
    """Test validation of multiple fields."""
    validator = TestValidator({})
    data = {
        "required_field": "value",
        "string_field": "test",
        "number_field": 42,
    }
    validator._validate_field_type(data["string_field"], str, "string_field")
    validator._validate_field_type(data["number_field"], int, "number_field")
    validator.validate(data)  # Should not raise


def test_validate_nested_fields():
    """Test validation of nested fields."""
    validator = TestValidator({})
    data = {
        "required_field": "value",
        "nested": {
            "field1": "value1",
            "field2": "value2",
        },
    }
    validator._validate_field_type(data["nested"], dict, "nested")
    validator._validate_field_type(data["nested"]["field1"], str, "nested.field1")
    validator.validate(data)  # Should not raise
