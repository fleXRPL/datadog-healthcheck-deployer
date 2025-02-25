"""Tests for the monitor class."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.monitors.monitor import Monitor
from datadog_healthcheck_deployer.utils.exceptions import MonitorError


def test_monitor_initialization():
    """Test basic monitor initialization."""
    config = {"name": "test-monitor", "type": "metric alert", "query": "avg:system.cpu.user{*}"}
    monitor = Monitor(config)
    assert monitor.name == "test-monitor"
    assert monitor.type == "metric alert"
    assert monitor.query == "avg:system.cpu.user{*}"


def test_monitor_validation():
    """Test monitor validation."""
    config = {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "message": "CPU usage high",
    }
    monitor = Monitor(config)
    monitor.validate()  # Should not raise


def test_monitor_invalid_type():
    """Test monitor with invalid type."""
    config = {"name": "test-monitor", "type": "invalid", "query": "avg:system.cpu.user{*}"}
    with pytest.raises(MonitorError, match="Invalid monitor type"):
        Monitor(config)


def test_monitor_create(mock_datadog_api):
    """Test monitor creation."""
    config = {"name": "test-monitor", "type": "metric alert", "query": "avg:system.cpu.user{*}"}
    monitor = Monitor(config)

    with patch("datadog.api", mock_datadog_api):
        monitor.create()
        mock_datadog_api.Monitor.create.assert_called_once()
        assert monitor.id == "test-123"


def test_monitor_update(mock_datadog_api):
    """Test monitor update."""
    config = {"name": "test-monitor", "type": "metric alert", "query": "avg:system.cpu.user{*}"}
    monitor = Monitor(config)
    monitor.id = "test-123"

    with patch("datadog.api", mock_datadog_api):
        monitor.update()
        mock_datadog_api.Monitor.update.assert_called_once_with("test-123", name="test-monitor")
