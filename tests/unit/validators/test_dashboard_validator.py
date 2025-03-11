"""Tests for dashboard validator implementation."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.dashboard_validator import DashboardValidator


@pytest.fixture
def validator():
    """Create a dashboard validator instance."""
    return DashboardValidator()


@pytest.fixture
def valid_config():
    """Create a valid dashboard configuration."""
    return {
        "title": "Test Dashboard",
        "description": "Test description",
        "layout_type": "ordered",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            },
            {
                "title": "Widget 2",
                "type": "query_value",
                "query": "avg:system.memory.used{*}",
            },
        ],
        "template_variables": [
            {
                "name": "env",
                "prefix": "environment",
                "default": "*",
            },
        ],
    }


def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator.schema is not None
    assert "type" in validator.schema
    assert validator.schema["type"] == "object"
    assert "required" in validator.schema
    assert "title" in validator.schema["required"]


def test_validate_valid_config(validator, valid_config):
    """Test validation of valid configuration."""
    validator.validate(valid_config)  # Should not raise


def test_validate_missing_title(validator, valid_config):
    """Test validation with missing title."""
    config = valid_config.copy()
    del config["title"]  # Remove title field
    with pytest.raises(ValidationError, match="'title' is a required property"):
        validator.validate(config)


def test_validate_invalid_layout_type(validator, valid_config):
    """Test validation with invalid layout type."""
    config = valid_config.copy()
    config["layout_type"] = "invalid"
    with pytest.raises(ValidationError, match="'invalid' is not one of"):
        validator.validate(config)


def test_validate_widgets(validator, valid_config):
    """Test widget validation."""
    # Test invalid widget type
    valid_config["widgets"][0]["type"] = "invalid_type"
    with pytest.raises(ValidationError, match="Invalid widget type"):
        validator.validate(valid_config)

    # Test missing widget title
    valid_config["widgets"][0]["type"] = "timeseries"
    del valid_config["widgets"][0]["title"]
    with pytest.raises(ValidationError, match="Title is required"):
        validator.validate(valid_config)

    # Test group widget with nested widgets
    valid_config["widgets"] = [
        {
            "title": "Group Widget",
            "type": "group",
            "widgets": [
                {
                    "title": "Nested Widget",
                    "type": "timeseries",
                    "query": "avg:system.cpu.user{*}",
                }
            ],
        }
    ]
    validator.validate(valid_config)  # Should not raise


def test_validate_template_variables(validator, valid_config):
    """Test template variable validation."""
    # Test missing variable name
    valid_config["template_variables"][0].pop("name")
    with pytest.raises(ValidationError, match="Template variable name is required"):
        validator.validate(valid_config)

    # Test duplicate variable names
    valid_config["template_variables"] = [
        {"name": "env", "prefix": "environment"},
        {"name": "env", "prefix": "environment"},  # Duplicate name
    ]
    with pytest.raises(ValidationError, match="Duplicate template variable name"):
        validator.validate(valid_config)


def test_get_defaults(validator):
    """Test getting default values."""
    defaults = validator.get_defaults()
    assert isinstance(defaults, dict)
    assert "layout_type" in defaults
    assert defaults["layout_type"] == "ordered"
    assert "widgets" in defaults
    assert isinstance(defaults["widgets"], list)
    assert "template_variables" in defaults
    assert isinstance(defaults["template_variables"], list)


def test_get_required_fields(validator):
    """Test getting required fields."""
    required = validator.get_required_fields()
    assert "title" in required


def test_validate_with_strict_mode(validator, valid_config):
    """Test validation in strict mode."""
    # Basic validation should pass
    validator.validate(valid_config, strict=True)

    # Even in strict mode, we allow additional fields for MVP
    valid_config["extra"] = "value"
    validator.validate(valid_config, strict=True)  # Should not raise an error
