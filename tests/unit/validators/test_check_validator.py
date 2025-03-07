"""Tests for check validator implementation."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.check_validator import CheckValidator


@pytest.fixture
def validator():
    """Create a check validator instance."""
    return CheckValidator()


def test_validator_initialization(validator):
    """Test validator initialization."""
    assert validator.schema is not None
    assert "type" in validator.schema
    assert validator.schema["type"] == "object"
    assert "required" in validator.schema
    assert "name" in validator.schema["required"]
    assert "type" in validator.schema["required"]


def test_validate_http_check(validator):
    """Test validation of HTTP check configuration."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://example.com",
        "method": "GET",
        "locations": ["aws:us-east-1"],
    }
    validator.validate(config)

    # Test invalid method
    config["method"] = "INVALID"
    with pytest.raises(ValidationError, match="Invalid HTTP method"):
        validator.validate(config)

    # Test missing URL
    del config["url"]
    with pytest.raises(ValidationError, match="URL is required"):
        validator.validate(config)


def test_validate_ssl_check(validator):
    """Test validation of SSL check configuration."""
    config = {
        "name": "test-ssl",
        "type": "ssl",
        "hostname": "example.com",
        "port": 443,
        "locations": ["aws:us-east-1"],
    }
    validator.validate(config)

    # Test missing hostname
    del config["hostname"]
    with pytest.raises(ValidationError, match="Hostname is required"):
        validator.validate(config)

    # Test invalid port
    config["hostname"] = "example.com"
    config["port"] = 70000
    with pytest.raises(ValidationError, match="Invalid port"):
        validator.validate(config)


def test_validate_dns_check(validator):
    """Test validation of DNS check configuration."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "example.com",
        "record_type": "A",
        "locations": ["aws:us-east-1"],
    }
    validator.validate(config)

    # Test missing hostname
    del config["hostname"]
    with pytest.raises(ValidationError, match="Hostname is required"):
        validator.validate(config)

    # Test invalid record type
    config["hostname"] = "example.com"
    config["record_type"] = "INVALID"
    with pytest.raises(ValidationError, match="Invalid DNS record type"):
        validator.validate(config)


def test_validate_tcp_check(validator):
    """Test validation of TCP check configuration."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "example.com",
        "port": 80,
        "locations": ["aws:us-east-1"],
    }
    validator.validate(config)

    # Test missing hostname
    del config["hostname"]
    with pytest.raises(ValidationError, match="Hostname is required"):
        validator.validate(config)

    # Test missing port
    config["hostname"] = "example.com"
    del config["port"]
    with pytest.raises(ValidationError, match="Port is required"):
        validator.validate(config)

    # Test invalid port
    config["port"] = -1
    with pytest.raises(ValidationError, match="Invalid port"):
        validator.validate(config)


def test_get_defaults(validator):
    """Test getting default values."""
    defaults = validator.get_defaults()
    assert "enabled" in defaults
    assert defaults["enabled"] is True
    assert "tags" in defaults
    assert isinstance(defaults["tags"], list)
    assert "locations" in defaults
    assert "aws:us-east-1" in defaults["locations"]
    assert "frequency" in defaults
    assert defaults["frequency"] == 60
    assert "timeout" in defaults
    assert defaults["timeout"] == 10


def test_get_required_fields(validator):
    """Test getting required fields."""
    required = validator.get_required_fields()
    assert "name" in required
    assert "type" in required


def test_validate_with_strict_mode(validator):
    """Test validation in strict mode."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://example.com",
        "locations": ["aws:us-east-1"],
    }
    # Basic validation should pass
    validator.validate(config, strict=True)

    # Even in strict mode, we allow additional fields for flexibility in MVP
    config["extra"] = "value"
    validator.validate(config, strict=True)  # Should not raise an error
