"""Tests for the monitor validator class."""

import pytest

from datadog_healthcheck_deployer.utils.exceptions import ValidationError
from datadog_healthcheck_deployer.validators.monitor_validator import MonitorValidator


@pytest.fixture
def validator():
    """Create a MonitorValidator instance."""
    return MonitorValidator()


def test_validate_basic_monitor(validator):
    """Test validation of basic monitor configuration."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "message": "CPU usage high",
    }
    validator.validate(monitor)  # Should not raise


def test_validate_missing_name(validator):
    """Test validation without name."""
    monitor = {
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
    }
    with pytest.raises(ValidationError, match="Name is required"):
        validator.validate(monitor)


def test_validate_missing_type(validator):
    """Test validation without type."""
    monitor = {
        "name": "test-monitor",
        "query": "avg:system.cpu.user{*}",
    }
    with pytest.raises(ValidationError, match="Type is required"):
        validator.validate(monitor)


def test_validate_invalid_type(validator):
    """Test validation with invalid type."""
    monitor = {
        "name": "test-monitor",
        "type": "invalid",
        "query": "avg:system.cpu.user{*}",
    }
    with pytest.raises(ValidationError, match="Invalid monitor type"):
        validator.validate(monitor)


def test_validate_missing_query(validator):
    """Test validation without query."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
    }
    with pytest.raises(ValidationError, match="Query is required"):
        validator.validate(monitor)


def test_validate_monitor_with_thresholds(validator):
    """Test validation of monitor with thresholds."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "thresholds": {
            "critical": 90,
            "warning": 80,
        },
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_thresholds(validator):
    """Test validation of monitor with invalid thresholds."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "thresholds": {
            "critical": "invalid",
        },
    }
    with pytest.raises(ValidationError, match="Invalid threshold value"):
        validator.validate(monitor)


def test_validate_monitor_with_notify_no_data(validator):
    """Test validation of monitor with notify_no_data option."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "notify_no_data": True,
        "no_data_timeframe": 10,
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_no_data_timeframe(validator):
    """Test validation of monitor with invalid no_data_timeframe."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "notify_no_data": True,
        "no_data_timeframe": -1,
    }
    with pytest.raises(ValidationError, match="Invalid no_data_timeframe"):
        validator.validate(monitor)


def test_validate_monitor_with_notification_channels(validator):
    """Test validation of monitor with notification channels."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "message": "@slack-alerts @email",
        "notification_channels": {
            "slack": ["#alerts"],
            "email": ["team@example.com"],
        },
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_notification_channels(validator):
    """Test validation of monitor with invalid notification channels."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "notification_channels": "invalid",
    }
    with pytest.raises(ValidationError, match="Invalid notification channels"):
        validator.validate(monitor)


def test_validate_monitor_with_tags(validator):
    """Test validation of monitor with tags."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "tags": ["env:prod", "service:api"],
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_tags(validator):
    """Test validation of monitor with invalid tags."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "tags": "not_a_list",
    }
    with pytest.raises(ValidationError, match="Tags must be a list"):
        validator.validate(monitor)


def test_validate_monitor_with_options(validator):
    """Test validation of monitor with options."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "options": {
            "timeout_h": 24,
            "renotify_interval": 60,
            "escalation_message": "Still critical!",
        },
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_options(validator):
    """Test validation of monitor with invalid options."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "options": {
            "timeout_h": "invalid",
        },
    }
    with pytest.raises(ValidationError, match="Invalid monitor options"):
        validator.validate(monitor)


def test_validate_monitor_with_evaluation_window(validator):
    """Test validation of monitor with evaluation window."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "evaluation_window": "last_5m",
    }
    validator.validate(monitor)  # Should not raise


def test_validate_monitor_invalid_evaluation_window(validator):
    """Test validation of monitor with invalid evaluation window."""
    monitor = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "evaluation_window": "invalid",
    }
    with pytest.raises(ValidationError, match="Invalid evaluation window"):
        validator.validate(monitor)
