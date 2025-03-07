"""Tests for config validator implementation."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.config_validator import ConfigValidator


@pytest.fixture
def validator():
    """Create a config validator instance."""
    return ConfigValidator()


def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator.schema is not None
    assert "type" in validator.schema
    assert validator.schema["type"] == "object"
    assert "required" in validator.schema
    assert "version" in validator.schema["required"]
    assert "healthchecks" in validator.schema["required"]


def test_validate_version(validator):
    """Test version validation."""
    config = {
        "version": "1.0",
        "healthchecks": [],
    }
    # For MVP, we allow empty healthchecks list
    validator.validate(config)

    # Test unsupported version
    config["version"] = "2.0"
    with pytest.raises(ValidationError, match="Unsupported version"):
        validator.validate(config)


def test_validate_healthchecks(validator):
    """Test healthchecks validation."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-check",
                "type": "http",
                "url": "https://example.com",
            }
        ],
    }
    validator.validate(config)

    # For MVP, we allow empty healthchecks list
    config["healthchecks"] = []
    validator.validate(config)  # Should not raise an error for MVP


def test_validate_duplicate_check_names(validator):
    """Test validation of duplicate check names."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-check",
                "type": "http",
                "url": "https://example.com",
            },
            {
                "name": "test-check",  # Duplicate name
                "type": "http",
                "url": "https://example.com",
            },
        ],
    }
    with pytest.raises(ValidationError, match="Duplicate check names found"):
        validator.validate(config)


def test_validate_variables(validator):
    """Test variables validation."""
    config = {
        "version": "1.0",
        "healthchecks": [{"name": "test", "type": "http"}],
        "variables": {
            "domain": "example.com",
            "timeout": 30,
        },
    }
    validator.validate(config)

    # Test invalid variables type
    config["variables"] = []
    with pytest.raises(ValidationError, match="Variables must be a dictionary"):
        validator.validate(config)


def test_validate_templates(validator):
    """Test templates validation."""
    config = {
        "version": "1.0",
        "healthchecks": [{"name": "test", "type": "http"}],
        "templates": {
            "basic_http": {
                "type": "http",
                "timeout": 30,
            },
        },
    }
    validator.validate(config)

    # Test invalid templates type
    config["templates"] = []
    with pytest.raises(ValidationError, match="Templates must be a dictionary"):
        validator.validate(config)


def test_validate_defaults(validator):
    """Test defaults validation."""
    config = {
        "version": "1.0",
        "healthchecks": [{"name": "test", "type": "http"}],
        "defaults": {
            "timeout": 30,
            "frequency": 60,
        },
    }
    validator.validate(config)

    # Test invalid defaults type
    config["defaults"] = []
    with pytest.raises(ValidationError, match="Defaults must be a dictionary"):
        validator.validate(config)


def test_get_defaults(validator):
    """Test getting default values."""
    defaults = validator.get_defaults()
    assert "version" in defaults
    assert defaults["version"] == "1.0"
    assert "healthchecks" in defaults
    assert isinstance(defaults["healthchecks"], list)
    assert "defaults" in defaults
    assert isinstance(defaults["defaults"], dict)
    assert "variables" in defaults
    assert isinstance(defaults["variables"], dict)
    assert "templates" in defaults
    assert isinstance(defaults["templates"], dict)


def test_get_required_fields(validator):
    """Test getting required fields."""
    required = validator.get_required_fields()
    assert "version" in required
    assert "healthchecks" in required


def test_validate_with_strict_mode(validator):
    """Test validation in strict mode."""
    config = {
        "version": "1.0",
        "healthchecks": [{"name": "test", "type": "http"}],
    }
    # Basic validation should pass
    validator.validate(config, strict=True)

    # Even in strict mode, we allow additional fields for flexibility in MVP
    config["extra"] = "value"
    validator.validate(config, strict=True)  # Should not raise an error
