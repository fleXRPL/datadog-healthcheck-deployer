"""Tests for the dashboard class."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.dashboards.dashboard import Dashboard
from datadog_healthcheck_deployer.utils.exceptions import DashboardError


def test_dashboard_initialization():
    """Test basic dashboard initialization."""
    config = {
        "title": "Test Dashboard",
        "description": "Test description",
        "widgets": [{"title": "Widget 1", "type": "timeseries"}],
    }
    dashboard = Dashboard(config)
    assert dashboard.title == "Test Dashboard"
    assert dashboard.description == "Test description"
    assert len(dashboard.widgets) == 1


def test_dashboard_validation():
    """Test dashboard validation."""
    config = {
        "title": "Test Dashboard",
        "description": "Test description",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            }
        ],
    }
    dashboard = Dashboard(config)
    dashboard.validate()  # Should not raise


def test_dashboard_missing_title():
    """Test dashboard initialization without title."""
    config = {"description": "Test description", "widgets": []}
    with pytest.raises(DashboardError, match="Dashboard title is required"):
        Dashboard(config)


def test_dashboard_invalid_widget():
    """Test dashboard with invalid widget configuration."""
    config = {
        "title": "Test Dashboard",
        "widgets": [{"title": "Invalid Widget"}],  # Missing required type
    }
    dashboard = Dashboard(config)
    with pytest.raises(DashboardError, match="Invalid widget configuration"):
        dashboard.validate()


def test_dashboard_create(mock_datadog_api):
    """Test dashboard creation."""
    config = {
        "title": "Test Dashboard",
        "description": "Test description",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            }
        ],
    }
    dashboard = Dashboard(config)

    with patch("datadog.api", mock_datadog_api):
        dashboard.create()
        mock_datadog_api.Dashboard.create.assert_called_once()
        assert dashboard.id == "dash-123"


def test_dashboard_update(mock_datadog_api):
    """Test dashboard update."""
    config = {
        "title": "Test Dashboard",
        "description": "Test description",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            }
        ],
    }
    dashboard = Dashboard(config)
    dashboard.id = "dash-123"

    with patch("datadog.api", mock_datadog_api):
        dashboard.update()
        mock_datadog_api.Dashboard.update.assert_called_once_with(
            "dash-123",
            title="Test Dashboard",
            description="Test description",
            widgets=config["widgets"],
            layout_type="ordered",
            template_variables=[],
        )


def test_dashboard_delete(mock_datadog_api):
    """Test dashboard deletion."""
    config = {"title": "Test Dashboard", "widgets": []}
    dashboard = Dashboard(config)
    dashboard.id = "dash-123"

    with patch("datadog.api", mock_datadog_api):
        dashboard.delete()
        mock_datadog_api.Dashboard.delete.assert_called_once_with("dash-123")
        assert dashboard.id is None


def test_dashboard_get_all(mock_datadog_api):
    """Test getting all dashboards."""
    mock_datadog_api.Dashboard.get_all.return_value = {
        "dashboards": [
            {
                "id": "dash-1",
                "title": "Dashboard 1",
                "widgets": [],
            },
            {
                "id": "dash-2",
                "title": "Dashboard 2",
                "widgets": [],
            },
        ]
    }

    with patch("datadog.api", mock_datadog_api):
        dashboards = Dashboard.get_all()
        assert len(dashboards) == 2
        assert all(isinstance(d, Dashboard) for d in dashboards)
        assert dashboards[0].id == "dash-1"
        assert dashboards[1].id == "dash-2"


def test_dashboard_template_variables():
    """Test dashboard with template variables."""
    config = {
        "title": "Test Dashboard",
        "template_variables": [
            {"name": "env", "prefix": "environment", "default": "*"},
            {"name": "service", "prefix": "service", "default": "all"},
        ],
        "widgets": [],
    }
    dashboard = Dashboard(config)
    assert len(dashboard.template_variables) == 2
    assert dashboard.template_variables[0]["name"] == "env"
    assert dashboard.template_variables[1]["default"] == "all"


def test_dashboard_complex_layout():
    """Test dashboard with complex layout configuration."""
    config = {
        "title": "Test Dashboard",
        "layout_type": "grid",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "layout": {"x": 0, "y": 0, "width": 6, "height": 4},
            },
            {
                "title": "Widget 2",
                "type": "toplist",
                "layout": {"x": 6, "y": 0, "width": 6, "height": 4},
            },
        ],
    }
    dashboard = Dashboard(config)
    assert dashboard.layout_type == "grid"
    assert len(dashboard.widgets) == 2
    assert all("layout" in w for w in dashboard.widgets)
