"""Tests for monitor implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.monitors.monitor import Monitor
from datadog_healthcheck_deployer.utils.exceptions import MonitorError


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
            "thresholds": {
                "critical": 90,
                "warning": 80,
            },
        },
    }


@pytest.fixture
def monitor(valid_config):
    """Create a monitor instance."""
    return Monitor(valid_config)


def test_monitor_initialization(valid_config):
    """Test monitor initialization."""
    monitor = Monitor(valid_config)
    assert monitor.name == valid_config["name"]
    assert monitor.type == valid_config["type"]
    assert monitor.query == valid_config["query"]
    assert monitor.message == valid_config["message"]
    assert monitor.tags == valid_config["tags"]
    assert monitor.options == valid_config["options"]
    assert monitor.id is None


def test_monitor_validation(monitor):
    """Test monitor validation."""
    monitor.validate()  # Should not raise

    # Test missing required field
    del monitor.config["query"]
    with pytest.raises(MonitorError, match="required"):
        monitor.validate()


@patch("datadog.api.Monitor")
def test_monitor_create(mock_monitor_api, monitor):
    """Test monitor creation."""
    mock_monitor_api.create.return_value = {"id": "test-123"}
    monitor.create()
    assert monitor.id == "test-123"
    mock_monitor_api.create.assert_called_once()


@patch("datadog.api.Monitor")
def test_monitor_update(mock_monitor_api, monitor):
    """Test monitor update."""
    monitor.id = "test-123"
    monitor.update()
    mock_monitor_api.update.assert_called_once_with("test-123", **monitor._build_api_payload())


@patch("datadog.api.Monitor")
def test_monitor_delete(mock_monitor_api, monitor):
    """Test monitor deletion."""
    monitor.id = "test-123"
    monitor.delete()
    mock_monitor_api.delete.assert_called_once_with("test-123")
    assert monitor.id is None


@patch("datadog.api.Monitor")
def test_monitor_get_status(mock_monitor_api, monitor):
    """Test getting monitor status."""
    monitor.id = "test-123"
    mock_monitor_api.get.return_value = {
        "overall_state": "OK",
        "type": "metric alert",
        "created": "2024-01-01",
        "modified": "2024-01-02",
    }
    status = monitor.get_status()
    assert status["id"] == "test-123"
    assert status["overall_state"] == "OK"
    mock_monitor_api.get.assert_called_once_with("test-123")


@patch("datadog.api.Monitor")
def test_monitor_mute(mock_monitor_api, monitor):
    """Test monitor muting."""
    monitor.id = "test-123"
    monitor.mute(scope="host:test", end=1234567890)
    mock_monitor_api.mute.assert_called_once_with("test-123", scope="host:test", end=1234567890)


@patch("datadog.api.Monitor")
def test_monitor_unmute(mock_monitor_api, monitor):
    """Test monitor unmuting."""
    monitor.id = "test-123"
    monitor.unmute(scope="host:test", all_scopes=True)
    mock_monitor_api.unmute.assert_called_once_with("test-123", scope="host:test", all_scopes=True)


@patch("datadog.api.Monitor")
def test_monitor_get_all(mock_monitor_api):
    """Test getting all monitors."""
    mock_monitor_api.get_all.return_value = [
        {
            "name": "test-1",
            "type": "metric alert",
            "query": "avg:system.cpu.user{*}",
            "id": "test-123",
        },
        {
            "name": "test-2",
            "type": "service check",
            "query": "avg:system.memory.used{*}",
            "id": "test-456",
        },
    ]
    monitors = Monitor.get_all(tag="env:prod")
    assert len(monitors) == 2
    assert all(isinstance(m, Monitor) for m in monitors)
    mock_monitor_api.get_all.assert_called_once_with(tag="env:prod", with_downtimes=True)


@patch("datadog.api.Monitor")
def test_monitor_search(mock_monitor_api):
    """Test monitor search."""
    mock_monitor_api.search.return_value = {
        "monitors": [
            {
                "name": "test-1",
                "type": "metric alert",
                "query": "avg:system.cpu.user{*}",
                "id": "test-123",
            }
        ]
    }
    monitors = Monitor.search("cpu")
    assert len(monitors) == 1
    assert isinstance(monitors[0], Monitor)
    mock_monitor_api.search.assert_called_once_with(query="cpu")


def test_monitor_string_representation(monitor):
    """Test string representation of monitor."""
    monitor.id = "test-123"
    expected = f"Monitor(name={monitor.name}, type={monitor.type}, id={monitor.id})"
    assert str(monitor) == expected


def test_monitor_build_options(valid_config):
    """Test building monitor options."""
    monitor = Monitor(valid_config)
    options = monitor._build_options()

    # Check default values are set
    assert "thresholds" in options
    assert "notify_no_data" in options
    assert "no_data_timeframe" in options
    assert "renotify_interval" in options
    assert "timeout_h" in options

    # Check custom values are preserved
    assert options["thresholds"]["critical"] == 90
    assert options["thresholds"]["warning"] == 80
