"""Tests for monitor manager implementation."""

from unittest.mock import MagicMock, patch

import pytest
from datadog import initialize

from datadog_healthcheck_deployer.monitors.manager import MonitorManager
from datadog_healthcheck_deployer.utils.exceptions import MonitorError


@pytest.fixture(autouse=True)
def mock_datadog():
    """Mock DataDog API initialization."""
    with patch("datadog.api.Monitor.search") as mock_search, patch(
        "datadog_healthcheck_deployer.utils.validation.validate_tags"
    ):
        mock_search.return_value = {"monitors": []}
        initialize(api_key="test-key", app_key="test-key")
        yield mock_search


@pytest.fixture
def manager():
    """Create a monitor manager instance."""
    return MonitorManager()


@pytest.fixture
def mock_check():
    """Create a mock check."""
    check = MagicMock()
    check.name = "test-check"
    check.type = "http"
    check.tags = ["env:test", "service:test"]
    return check


@pytest.fixture
def valid_config():
    """Create a valid monitor configuration."""
    return {
        "availability": {"enabled": True, "threshold": 99.9},
        "latency": {"enabled": True, "threshold": 500},
        "ssl": {"enabled": False},
    }


def test_manager_initialization(manager):
    """Test monitor manager initialization."""
    assert isinstance(manager.monitors, dict)
    assert len(manager.monitors) == 0


def test_configure_monitor_error(manager, mock_check, valid_config):
    """Test monitor configuration error handling."""
    with patch("datadog_healthcheck_deployer.monitors.monitor.Monitor") as mock_monitor_cls, patch(
        "datadog.api.Monitor.create"
    ) as mock_create:
        mock_monitor = MagicMock()
        mock_monitor_cls.return_value = mock_monitor
        mock_create.side_effect = Exception("API Error")

        with pytest.raises(MonitorError, match="Failed to configure monitors"):
            manager.configure(mock_check, valid_config)


def test_build_tags(manager, mock_check):
    """Test building tags."""
    tags = manager._build_tags(mock_check, "test")
    expected_tags = [
        "env:test",
        "service:test",
        "check_type:http",
        "monitor_type:test",
        "managed-by:dd-healthcheck",
    ]
    assert tags == expected_tags
