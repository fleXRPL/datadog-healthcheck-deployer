"""Tests for the check validator class."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.check_validator import CheckValidator


@pytest.fixture
def validator():
    """Create a CheckValidator instance."""
    return CheckValidator()


def test_validate_basic_check(validator):
    """Test validation of basic check configuration."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "locations": ["aws:us-east-1"],
    }
    validator.validate(check)  # Should not raise


def test_validate_missing_name(validator):
    """Test validation without name."""
    check = {
        "type": "http",
        "url": "https://example.com",
    }
    with pytest.raises(ValidationError, match="Name is required"):
        validator.validate(check)


def test_validate_missing_type(validator):
    """Test validation without type."""
    check = {
        "name": "test-check",
        "url": "https://example.com",
    }
    with pytest.raises(ValidationError, match="Type is required"):
        validator.validate(check)


def test_validate_invalid_type(validator):
    """Test validation with invalid type."""
    check = {
        "name": "test-check",
        "type": "invalid",
    }
    with pytest.raises(ValidationError, match="Invalid check type"):
        validator.validate(check)


def test_validate_http_check(validator):
    """Test validation of HTTP check."""
    check = {
        "name": "test-http",
        "type": "http",
        "url": "https://example.com",
        "method": "GET",
        "headers": {"Content-Type": "application/json"},
        "timeout": 30,
    }
    validator.validate(check)  # Should not raise


def test_validate_http_check_missing_url(validator):
    """Test validation of HTTP check without URL."""
    check = {
        "name": "test-http",
        "type": "http",
    }
    with pytest.raises(ValidationError, match="URL is required"):
        validator.validate(check)


def test_validate_http_check_invalid_method(validator):
    """Test validation of HTTP check with invalid method."""
    check = {
        "name": "test-http",
        "type": "http",
        "url": "https://example.com",
        "method": "INVALID",
    }
    with pytest.raises(ValidationError, match="Invalid HTTP method"):
        validator.validate(check)


def test_validate_ssl_check(validator):
    """Test validation of SSL check."""
    check = {
        "name": "test-ssl",
        "type": "ssl",
        "hostname": "example.com",
        "port": 443,
    }
    validator.validate(check)  # Should not raise


def test_validate_ssl_check_missing_hostname(validator):
    """Test validation of SSL check without hostname."""
    check = {
        "name": "test-ssl",
        "type": "ssl",
    }
    with pytest.raises(ValidationError, match="Hostname is required"):
        validator.validate(check)


def test_validate_dns_check(validator):
    """Test validation of DNS check."""
    check = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "example.com",
        "record_type": "A",
    }
    validator.validate(check)  # Should not raise


def test_validate_dns_check_invalid_record_type(validator):
    """Test validation of DNS check with invalid record type."""
    check = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "example.com",
        "record_type": "INVALID",
    }
    with pytest.raises(ValidationError, match="Invalid DNS record type"):
        validator.validate(check)


def test_validate_tcp_check(validator):
    """Test validation of TCP check."""
    check = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "example.com",
        "port": 80,
    }
    validator.validate(check)  # Should not raise


def test_validate_tcp_check_invalid_port(validator):
    """Test validation of TCP check with invalid port."""
    check = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "example.com",
        "port": -1,
    }
    with pytest.raises(ValidationError, match="Invalid port"):
        validator.validate(check)


def test_validate_check_with_monitors(validator):
    """Test validation of check with monitors."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "monitors": {
            "availability": {
                "enabled": True,
                "threshold": 99.9,
            },
            "latency": {
                "enabled": True,
                "threshold": 500,
            },
        },
    }
    validator.validate(check)  # Should not raise


def test_validate_check_invalid_monitor_config(validator):
    """Test validation of check with invalid monitor configuration."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "monitors": {
            "availability": {
                "enabled": True,
                "threshold": "invalid",
            },
        },
    }
    with pytest.raises(ValidationError, match="Invalid monitor configuration"):
        validator.validate(check)


def test_validate_check_with_tags(validator):
    """Test validation of check with tags."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "tags": ["env:prod", "service:api"],
    }
    validator.validate(check)  # Should not raise


def test_validate_check_invalid_tags(validator):
    """Test validation of check with invalid tags."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "tags": "not_a_list",
    }
    with pytest.raises(ValidationError, match="Tags must be a list"):
        validator.validate(check)


def test_validate_check_with_locations(validator):
    """Test validation of check with locations."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "locations": ["aws:us-east-1", "aws:eu-west-1"],
    }
    validator.validate(check)  # Should not raise


def test_validate_check_invalid_location(validator):
    """Test validation of check with invalid location."""
    check = {
        "name": "test-check",
        "type": "http",
        "url": "https://example.com",
        "locations": ["invalid:location"],
    }
    with pytest.raises(ValidationError, match="Invalid location"):
        validator.validate(check)
