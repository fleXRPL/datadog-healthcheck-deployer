"""Tests for the configuration validator class."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.config_validator import ConfigValidator


@pytest.fixture
def validator():
    """Create a ConfigValidator instance."""
    return ConfigValidator()


def test_validate_basic_config(validator):
    """Test validation of basic configuration."""
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
    validator.validate(config)  # Should not raise


def test_validate_missing_version(validator):
    """Test validation without version."""
    config = {
        "healthchecks": [
            {
                "name": "test-check",
                "type": "http",
                "url": "https://example.com",
            }
        ],
    }
    with pytest.raises(ValidationError, match="Version is required"):
        validator.validate(config)


def test_validate_invalid_version(validator):
    """Test validation with invalid version."""
    config = {
        "version": "invalid",
        "healthchecks": [],
    }
    with pytest.raises(ValidationError, match="Invalid version format"):
        validator.validate(config)


def test_validate_missing_healthchecks(validator):
    """Test validation without healthchecks."""
    config = {
        "version": "1.0",
    }
    with pytest.raises(ValidationError, match="Healthchecks are required"):
        validator.validate(config)


def test_validate_empty_healthchecks(validator):
    """Test validation with empty healthchecks."""
    config = {
        "version": "1.0",
        "healthchecks": [],
    }
    validator.validate(config)  # Should not raise


def test_validate_duplicate_check_names(validator):
    """Test validation with duplicate check names."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {"name": "test", "type": "http"},
            {"name": "test", "type": "http"},
        ],
    }
    with pytest.raises(ValidationError, match="Duplicate check name"):
        validator.validate(config)


def test_validate_variables(validator):
    """Test validation with variables."""
    config = {
        "version": "1.0",
        "variables": {
            "domain": "example.com",
            "timeout": 30,
        },
        "healthchecks": [],
    }
    validator.validate(config)  # Should not raise


def test_validate_invalid_variables(validator):
    """Test validation with invalid variables."""
    config = {
        "version": "1.0",
        "variables": "not_a_dict",
        "healthchecks": [],
    }
    with pytest.raises(ValidationError, match="Variables must be a dictionary"):
        validator.validate(config)


def test_validate_templates(validator):
    """Test validation with templates."""
    config = {
        "version": "1.0",
        "templates": {
            "basic_check": {
                "type": "http",
                "timeout": 30,
            },
        },
        "healthchecks": [],
    }
    validator.validate(config)  # Should not raise


def test_validate_invalid_templates(validator):
    """Test validation with invalid templates."""
    config = {
        "version": "1.0",
        "templates": "not_a_dict",
        "healthchecks": [],
    }
    with pytest.raises(ValidationError, match="Templates must be a dictionary"):
        validator.validate(config)


def test_validate_defaults(validator):
    """Test validation with defaults."""
    config = {
        "version": "1.0",
        "defaults": {
            "timeout": 30,
            "frequency": 60,
        },
        "healthchecks": [],
    }
    validator.validate(config)  # Should not raise


def test_validate_invalid_defaults(validator):
    """Test validation with invalid defaults."""
    config = {
        "version": "1.0",
        "defaults": "not_a_dict",
        "healthchecks": [],
    }
    with pytest.raises(ValidationError, match="Defaults must be a dictionary"):
        validator.validate(config)


def test_validate_check_references_template(validator):
    """Test validation of check referencing template."""
    config = {
        "version": "1.0",
        "templates": {
            "basic_check": {
                "type": "http",
                "timeout": 30,
            },
        },
        "healthchecks": [
            {
                "name": "test",
                "template": "basic_check",
                "url": "https://example.com",
            },
        ],
    }
    validator.validate(config)  # Should not raise


def test_validate_check_invalid_template_reference(validator):
    """Test validation of check referencing non-existent template."""
    config = {
        "version": "1.0",
        "templates": {},
        "healthchecks": [
            {
                "name": "test",
                "template": "nonexistent",
            },
        ],
    }
    with pytest.raises(ValidationError, match="Template .* not found"):
        validator.validate(config)


def test_validate_check_with_variables(validator):
    """Test validation of check using variables."""
    config = {
        "version": "1.0",
        "variables": {
            "domain": "example.com",
            "timeout": 30,
        },
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://{{domain}}",
                "timeout": "{{timeout}}",
            },
        ],
    }
    validator.validate(config)  # Should not raise


def test_validate_check_with_undefined_variables(validator):
    """Test validation of check using undefined variables."""
    config = {
        "version": "1.0",
        "variables": {},
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://{{undefined}}",
            },
        ],
    }
    with pytest.raises(ValidationError, match="Undefined variable"):
        validator.validate(config, strict=True)


def test_validate_strict_mode(validator):
    """Test strict validation mode."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://example.com",
                "unknown_field": "value",
            },
        ],
    }
    with pytest.raises(ValidationError, match="Unknown field"):
        validator.validate(config, strict=True)
