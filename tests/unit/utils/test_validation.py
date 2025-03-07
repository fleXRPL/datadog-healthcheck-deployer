"""Tests for validation utilities."""

import socket
import ssl
from unittest.mock import MagicMock, patch

import dns.resolver
import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.utils.validation import (
    validate_check_type,
    validate_content_match,
    validate_dns_record,
    validate_http_method,
    validate_interval,
    validate_location,
    validate_monitor_config,
    validate_monitor_state,
    validate_monitor_type,
    validate_notification_channel,
    validate_notify_type,
    validate_ssl_certificate,
    validate_tags,
    validate_tcp_connection,
    validate_template,
    validate_thresholds,
    validate_url,
    validate_variables,
)


def test_validate_check_type():
    """Test check type validation."""
    validate_check_type("http")  # Should not raise
    validate_check_type("ssl")  # Should not raise

    with pytest.raises(ValidationError):
        validate_check_type("invalid")


def test_validate_http_method():
    """Test HTTP method validation."""
    validate_http_method("GET")  # Should not raise
    validate_http_method("POST")  # Should not raise

    with pytest.raises(ValidationError):
        validate_http_method("INVALID")


def test_validate_monitor_type():
    """Test monitor type validation."""
    validate_monitor_type("metric alert")  # Should not raise
    validate_monitor_type("service check")  # Should not raise

    with pytest.raises(ValidationError):
        validate_monitor_type("invalid")


def test_validate_monitor_state():
    """Test monitor state validation."""
    validate_monitor_state("OK")  # Should not raise
    validate_monitor_state("ALERT")  # Should not raise

    with pytest.raises(ValidationError):
        validate_monitor_state("INVALID")


def test_validate_notify_type():
    """Test notification type validation."""
    validate_notify_type("email")  # Should not raise
    validate_notify_type("slack")  # Should not raise

    with pytest.raises(ValidationError):
        validate_notify_type("invalid")


def test_validate_location():
    """Test location validation."""
    validate_location("aws:us-east-1")  # Should not raise

    with pytest.raises(ValidationError):
        validate_location("invalid")

    with pytest.raises(ValidationError):
        validate_location("aws:invalid")


def test_validate_tags():
    """Test tags validation."""
    valid_tags = {"env": "production", "service": "api"}
    validate_tags(valid_tags)  # Should not raise

    invalid_tags = {"invalid@tag": "value"}
    with pytest.raises(ValidationError):
        validate_tags(invalid_tags)


def test_validate_interval():
    """Test interval validation."""
    validate_interval(60)  # Should not raise
    validate_interval(300)  # Should not raise

    with pytest.raises(ValidationError):
        validate_interval("invalid")

    with pytest.raises(ValidationError):
        validate_interval(0)


def test_validate_url():
    """Test URL validation."""
    validate_url("https://example.com")  # Should not raise

    with pytest.raises(ValidationError):
        validate_url("invalid")


@patch("socket.create_connection")
@patch("ssl.create_default_context")
def test_validate_ssl_certificate(mock_context, mock_connection):
    """Test SSL certificate validation."""
    # Test successful validation
    mock_sock = MagicMock()
    mock_ssock = MagicMock()
    mock_ssock.getpeercert.return_value = {"subject": [("CN", "example.com")]}
    mock_context.return_value.wrap_socket.return_value = mock_ssock
    mock_connection.return_value = mock_sock

    validate_ssl_certificate("example.com")  # Should not raise

    # Test validation failure
    mock_context.return_value.wrap_socket.side_effect = ssl.SSLError(
        "Certificate validation failed"
    )
    with pytest.raises(ValidationError):
        validate_ssl_certificate("example.com")


@patch("dns.resolver.Resolver")
def test_validate_dns_record(mock_resolver):
    """Test DNS record validation."""
    mock_resolver.return_value.query.return_value = []

    validate_dns_record("example.com")  # Should not raise

    mock_resolver.return_value.query.side_effect = dns.resolver.NXDOMAIN
    with pytest.raises(ValidationError):
        validate_dns_record("invalid.com")


@patch("socket.create_connection")
def test_validate_tcp_connection(mock_connection):
    """Test TCP connection validation."""
    validate_tcp_connection("example.com", 80)  # Should not raise

    mock_connection.side_effect = socket.error
    with pytest.raises(ValidationError):
        validate_tcp_connection("invalid", 80)


def test_validate_content_match():
    """Test content match validation."""
    validate_content_match(r"test.*")  # Should not raise

    with pytest.raises(ValidationError):
        validate_content_match("(invalid")


def test_validate_thresholds():
    """Test threshold validation."""
    validate_thresholds(warning=90, critical=80)  # Should not raise

    with pytest.raises(ValidationError):
        validate_thresholds(warning="invalid", critical=80)

    with pytest.raises(ValidationError):
        validate_thresholds(warning=70, critical=80)  # Warning should be > critical


def test_validate_variables():
    """Test variables validation."""
    valid_vars = {"valid_name": "value"}
    validate_variables(valid_vars)  # Should not raise

    invalid_vars = {"invalid@name": "value"}
    with pytest.raises(ValidationError):
        validate_variables(invalid_vars)


def test_validate_template():
    """Test template validation."""
    valid_template = {"name": "test", "type": "http"}
    validate_template(valid_template)  # Should not raise

    invalid_template = {
        "name": "test"
        # Missing type
    }
    with pytest.raises(ValidationError):
        validate_template(invalid_template)


def test_validate_notification_channel():
    """Test notification channel validation."""
    valid_channel = {"type": "email", "name": "test", "addresses": ["test@example.com"]}
    validate_notification_channel(valid_channel)  # Should not raise

    invalid_channel = {
        "type": "email",
        "name": "test",
        # Missing addresses
    }
    with pytest.raises(ValidationError):
        validate_notification_channel(invalid_channel)


def test_validate_monitor_config():
    """Test monitor configuration validation."""
    valid_config = {"name": "test", "type": "metric alert", "query": "avg:system.cpu.user{*}"}
    validate_monitor_config(valid_config)  # Should not raise

    invalid_config = {
        "name": "test"
        # Missing type and query
    }
    with pytest.raises(ValidationError):
        validate_monitor_config(invalid_config)
