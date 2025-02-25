"""Tests for the monitor manager class."""

from unittest.mock import MagicMock, patch

from datadog_healthcheck_deployer.monitors.manager import MonitorManager


def test_monitor_manager_initialization():
    """Test monitor manager initialization."""
    manager = MonitorManager()
    assert len(manager.monitors) == 0


def test_monitor_manager_configure():
    """Test basic monitor configuration."""
    manager = MonitorManager()
    check = MagicMock(name="test-check")
    config = {"enabled": True, "availability": {"enabled": True, "threshold": 99.9}}

    manager.configure(check, config)
    assert len(manager.monitors) == 1


def test_monitor_manager_disabled():
    """Test monitor manager with disabled configuration."""
    manager = MonitorManager()
    check = MagicMock(name="test-check")
    config = {"enabled": False}

    manager.configure(check, config)
    assert len(manager.monitors) == 0


def test_monitor_manager_deploy(mock_datadog_api):
    """Test monitor deployment."""
    manager = MonitorManager()
    check = MagicMock(name="test-check")
    config = {"enabled": True, "availability": {"enabled": True, "threshold": 99.9}}

    with patch("datadog.api", mock_datadog_api):
        manager.configure(check, config)
        assert mock_datadog_api.Monitor.create.called


def test_monitor_manager_delete(mock_datadog_api):
    """Test monitor deletion."""
    manager = MonitorManager()
    check = MagicMock(name="test-check")
    config = {"enabled": True, "availability": {"enabled": True, "threshold": 99.9}}

    with patch("datadog.api", mock_datadog_api):
        manager.configure(check, config)
        manager.delete_monitors("test-check")
        assert mock_datadog_api.Monitor.delete.called
