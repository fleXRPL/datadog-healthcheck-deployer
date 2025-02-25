"""Tests for the dashboard manager class."""

from unittest.mock import MagicMock, patch

import pytest

from datadog_healthcheck_deployer.dashboards.manager import DashboardManager
from datadog_healthcheck_deployer.utils.exceptions import DashboardError


def test_dashboard_manager_initialization():
    """Test dashboard manager initialization."""
    manager = DashboardManager()
    assert len(manager.dashboards) == 0


def test_dashboard_manager_configure():
    """Test basic dashboard configuration."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    manager.configure(check, config)
    assert len(manager.dashboards) == 1
    assert "test-check" in manager.dashboards


def test_dashboard_manager_disabled():
    """Test dashboard manager with disabled configuration."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {"enabled": False}

    manager.configure(check, config)
    assert len(manager.dashboards) == 0


def test_dashboard_manager_custom_widgets():
    """Test dashboard manager with custom widgets."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "widgets": [
            {
                "title": "Custom Widget",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            }
        ],
    }

    manager.configure(check, config)
    assert len(manager.dashboards) == 1
    dashboard = manager.dashboards["test-check"]
    assert len(dashboard.widgets) == 1
    assert dashboard.widgets[0]["title"] == "Custom Widget"


def test_dashboard_manager_invalid_template():
    """Test dashboard manager with invalid template."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "invalid_template",
    }

    with pytest.raises(DashboardError, match="Unknown template"):
        manager.configure(check, config)


def test_dashboard_manager_basic_health_template():
    """Test dashboard manager with basic health template."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    manager.configure(check, config)
    dashboard = manager.dashboards["test-check"]
    assert "Health Overview" in dashboard.title
    assert len(dashboard.widgets) == 3  # Status, Response Time, Success Rate


def test_dashboard_manager_service_health_template():
    """Test dashboard manager with service health template."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "service_health",
    }

    manager.configure(check, config)
    dashboard = manager.dashboards["test-check"]
    assert "Service Health" in dashboard.title
    assert len(dashboard.widgets) == 2  # Status group and Performance group


def test_dashboard_manager_detailed_health_template():
    """Test dashboard manager with detailed health template."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "detailed_health",
    }

    manager.configure(check, config)
    dashboard = manager.dashboards["test-check"]
    assert "Detailed Health" in dashboard.title
    assert len(dashboard.widgets) == 3  # Overview, Performance, Errors groups


def test_dashboard_manager_deploy(mock_datadog_api):
    """Test dashboard deployment."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    with patch("datadog.api", mock_datadog_api):
        manager.configure(check, config)
        assert mock_datadog_api.Dashboard.create.called


def test_dashboard_manager_delete(mock_datadog_api):
    """Test dashboard deletion."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    with patch("datadog.api", mock_datadog_api):
        manager.configure(check, config)
        manager.delete_dashboards("test-check")
        assert mock_datadog_api.Dashboard.delete.called
        assert "test-check" not in manager.dashboards


def test_dashboard_manager_get_status():
    """Test getting dashboard status."""
    manager = DashboardManager()
    check = MagicMock(name="test-check")
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    manager.configure(check, config)
    status = manager.get_dashboard_status("test-check")
    assert status is not None
    assert "title" in status
    assert "widgets_count" in status


def test_dashboard_manager_get_status_nonexistent():
    """Test getting status for nonexistent dashboard."""
    manager = DashboardManager()
    status = manager.get_dashboard_status("nonexistent")
    assert status is None


def test_dashboard_manager_multiple_checks():
    """Test dashboard manager with multiple checks."""
    manager = DashboardManager()
    checks = [
        MagicMock(name="check1"),
        MagicMock(name="check2"),
        MagicMock(name="check3"),
    ]
    config = {
        "enabled": True,
        "template": "basic_health",
    }

    for check in checks:
        manager.configure(check, config)

    assert len(manager.dashboards) == 3
    assert all(check.name in manager.dashboards for check in checks)
