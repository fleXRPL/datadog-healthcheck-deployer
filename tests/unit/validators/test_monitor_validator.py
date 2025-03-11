"""Tests for monitor validator implementation."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.monitor_validator import MonitorValidator


@pytest.fixture
def validator():
    """Create a monitor validator instance."""
    return MonitorValidator()


@pytest.fixture
def valid_config():
    """Create a valid monitor configuration."""
    return {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "message": "CPU usage is high",
        "tags": {"env": "prod", "service": "api"},
        "options": {
            "timeout_h": 24,
            "renotify_interval": 60,
            "thresholds": {
                "critical": 90,
                "warning": 80,
            },
        },
    }


def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator.schema is not None
    assert "type" in validator.schema
    assert validator.schema["type"] == "object"
    assert "required" in validator.schema
    assert "name" in validator.schema["required"]
    assert "type" in validator.schema["required"]
    assert "query" in validator.schema["required"]


def test_validate_valid_config(validator, valid_config):
    """Test validation of valid configuration."""
    validator.validate(valid_config)  # Should not raise


def test_validate_missing_required_fields(validator, valid_config):
    """Test validation with missing required fields."""
    invalid_config = {
        "name": "test-monitor",
        # Missing type and query
    }
    with pytest.raises(ValidationError, match="'type' is a required property"):
        validator.validate(invalid_config)


def test_validate_invalid_monitor_type(validator, valid_config):
    """Test validation with invalid monitor type."""
    config = valid_config.copy()
    config["type"] = "invalid_type"
    with pytest.raises(ValidationError, match="'invalid_type' is not one of"):
        validator.validate(config)


def test_validate_thresholds(validator, valid_config):
    """Test threshold validation."""
    config = valid_config.copy()
    config["options"] = {"thresholds": {"critical": "invalid"}}
    with pytest.raises(ValidationError, match="Invalid threshold value"):
        validator.validate(config)


def test_validate_options(validator, valid_config):
    """Test options validation."""
    # Test invalid timeout value
    valid_config["options"]["timeout_h"] = -1
    with pytest.raises(ValidationError, match="Invalid timeout value"):
        validator.validate(valid_config)

    # Test invalid renotify interval
    valid_config["options"]["timeout_h"] = 24
    valid_config["options"]["renotify_interval"] = -1
    with pytest.raises(ValidationError, match="Invalid renotify interval"):
        validator.validate(valid_config)


def test_get_defaults(validator):
    """Test getting default values."""
    defaults = validator.get_defaults()
    assert isinstance(defaults, dict)
    assert "tags" in defaults
    assert isinstance(defaults["tags"], list)  # Tags should be a list, not a dict
    assert "notify_no_data" in defaults
    assert defaults["notify_no_data"] is True
    assert "no_data_timeframe" in defaults
    assert defaults["no_data_timeframe"] == 10
    assert "include_tags" in defaults
    assert defaults["include_tags"] is True
    assert "require_full_window" in defaults
    assert defaults["require_full_window"] is True


def test_get_required_fields(validator):
    """Test getting required fields."""
    required = validator.get_required_fields()
    assert "name" in required
    assert "type" in required
    assert "query" in required


def test_validate_with_strict_mode(validator, valid_config):
    """Test validation in strict mode."""
    # Basic validation should pass
    validator.validate(valid_config, strict=True)

    # Even in strict mode, we allow additional fields for MVP
    valid_config["extra"] = "value"
    validator.validate(valid_config, strict=True)  # Should not raise an error
