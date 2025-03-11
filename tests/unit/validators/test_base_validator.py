"""Tests for base validator implementation."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.base import BaseValidator


class SimpleValidator(BaseValidator):
    """Simple validator implementation for testing."""

    def validate(self, data, strict=False):
        """Validate data."""
        super().validate(data, strict)
        if "test" not in data:
            raise ValidationError("Missing required field: test")

    def get_defaults(self):
        """Get default values."""
        return {"test": "default"}

    def get_required_fields(self):
        """Get required fields."""
        return ["test"]


@pytest.fixture
def validator():
    """Create a validator instance."""
    schema = {
        "type": "object",
        "required": ["test"],
        "properties": {
            "test": {"type": "string"},
            "number": {"type": "integer", "minimum": 0, "maximum": 100},
            "enum": {"type": "string", "enum": ["a", "b", "c"]},
            "pattern": {"type": "string", "pattern": "^test-[a-z]+$"},
        },
    }
    return SimpleValidator(schema)


def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator.schema is not None
    assert "type" in validator.schema
    assert validator.schema["type"] == "object"


def test_validate_required_fields(validator):
    """Test validation of required fields."""
    data = {"test": "value"}
    validator._validate_required_fields(data, ["test"])

    with pytest.raises(ValidationError, match="Missing required fields"):
        validator._validate_required_fields(data, ["missing"])


def test_validate_field_type(validator):
    """Test field type validation."""
    validator._validate_field_type("test", str, "string_field")
    validator._validate_field_type(123, int, "int_field")

    with pytest.raises(ValidationError, match="Invalid type for field"):
        validator._validate_field_type(123, str, "string_field")


def test_validate_enum(validator):
    """Test enum validation."""
    validator._validate_enum("a", ["a", "b", "c"], "enum_field")

    with pytest.raises(ValidationError, match="Invalid value for field"):
        validator._validate_enum("d", ["a", "b", "c"], "enum_field")


def test_validate_range(validator):
    """Test range validation."""
    validator._validate_range(50, 0, 100, "range_field")

    with pytest.raises(ValidationError, match="must be >="):
        validator._validate_range(-1, 0, 100, "range_field")

    with pytest.raises(ValidationError, match="must be <="):
        validator._validate_range(101, 0, 100, "range_field")


def test_validate_string_length(validator):
    """Test string length validation."""
    validator._validate_string_length("test", 1, 10, "string_field")

    with pytest.raises(ValidationError, match="must be >="):
        validator._validate_string_length("", 1, 10, "string_field")

    with pytest.raises(ValidationError, match="must be <="):
        validator._validate_string_length("too_long_string", 1, 10, "string_field")


def test_validate_pattern(validator):
    """Test pattern validation."""
    validator._validate_pattern("test-abc", "^test-[a-z]+$", "pattern_field")

    with pytest.raises(ValidationError, match="must match pattern"):
        validator._validate_pattern("invalid", "^test-[a-z]+$", "pattern_field")


def test_validator_string_representation(validator):
    """Test string representation of validator."""
    assert str(validator) == "SimpleValidator()"


def test_validate_with_strict_mode(validator):
    """Test validation in strict mode."""
    data = {"test": "value", "number": 50}
    validator.validate(data, strict=True)

    # For MVP, we allow additional fields even in strict mode
    data["extra"] = "value"
    validator.validate(data, strict=True)  # Should not raise an error for MVP


def test_get_defaults(validator):
    """Test getting default values."""
    defaults = validator.get_defaults()
    assert "test" in defaults
    assert defaults["test"] == "default"


def test_get_required_fields(validator):
    """Test getting required fields."""
    required = validator.get_required_fields()
    assert "test" in required
    assert len(required) == 1
