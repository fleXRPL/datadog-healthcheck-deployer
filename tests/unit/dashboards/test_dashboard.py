"""Tests for dashboard implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.dashboards.dashboard import Dashboard
from datadog_healthcheck_deployer.utils.exceptions import DashboardError


@pytest.fixture
def valid_config():
    """Create a valid dashboard configuration."""
    return {
        "title": "Test Dashboard",
        "description": "Test description",
        "layout_type": "ordered",
        "widgets": [
            {
                "title": "Widget 1",
                "type": "timeseries",
                "query": "avg:system.cpu.user{*}",
            }
        ],
        "template_variables": [
            {
                "name": "env",
                "prefix": "environment",
                "default": "*",
            }
        ],
    }


@pytest.fixture
def dashboard(valid_config):
    """Create a dashboard instance."""
    return Dashboard(valid_config)


def test_dashboard_initialization(valid_config):
    """Test dashboard initialization."""
    dashboard = Dashboard(valid_config)
    assert dashboard.title == valid_config["title"]
    assert dashboard.description == valid_config["description"]
    assert dashboard.layout_type == valid_config["layout_type"]
    assert dashboard.widgets == valid_config["widgets"]
    assert dashboard.template_variables == valid_config["template_variables"]
    assert dashboard.id is None


def test_dashboard_validation(dashboard):
    """Test dashboard validation."""
    dashboard.validate()  # Should not raise

    # Test missing title
    config = dashboard.config.copy()
    config.pop("title")
    dashboard.config = config
    with pytest.raises(DashboardError, match="required"):
        dashboard.validate()


@patch("datadog.api.Dashboard")
def test_dashboard_create(mock_dashboard_api, dashboard):
    """Test dashboard creation."""
    mock_dashboard_api.create.return_value = {"id": "test-123"}
    dashboard.create()
    assert dashboard.id == "test-123"
    mock_dashboard_api.create.assert_called_once()


@patch("datadog.api.Dashboard")
def test_dashboard_update(mock_dashboard_api, dashboard):
    """Test dashboard update."""
    dashboard.id = "test-123"
    dashboard.update()
    mock_dashboard_api.update.assert_called_once_with("test-123", **dashboard._build_api_payload())


@patch("datadog.api.Dashboard")
def test_dashboard_delete(mock_dashboard_api, dashboard):
    """Test dashboard deletion."""
    dashboard.id = "test-123"
    dashboard.delete()
    mock_dashboard_api.delete.assert_called_once_with("test-123")
    assert dashboard.id is None


@patch("datadog.api.Dashboard")
def test_dashboard_get_all(mock_dashboard_api):
    """Test getting all dashboards."""
    mock_dashboard_api.get_all.return_value = {
        "dashboards": [
            {
                "title": "Test 1",
                "description": "Description 1",
                "id": "test-123",
                "widgets": [],
            },
            {
                "title": "Test 2",
                "description": "Description 2",
                "id": "test-456",
                "widgets": [],
            },
        ]
    }
    dashboards = Dashboard.get_all()
    assert len(dashboards) == 2
    assert all(isinstance(d, Dashboard) for d in dashboards)
    mock_dashboard_api.get_all.assert_called_once()


def test_dashboard_build_api_payload(dashboard):
    """Test building API payload."""
    payload = dashboard._build_api_payload()
    assert payload["title"] == dashboard.title
    assert payload["description"] == dashboard.description
    assert payload["layout_type"] == dashboard.layout_type
    assert payload["widgets"] == dashboard.widgets
    assert payload["template_variables"] == dashboard.template_variables


def test_dashboard_string_representation(dashboard):
    """Test string representation of dashboard."""
    dashboard.id = "test-123"
    expected = f"Dashboard(title={dashboard.title}, id={dashboard.id})"
    assert str(dashboard) == expected


@patch("datadog.api.Dashboard")
def test_dashboard_create_error(mock_dashboard_api, dashboard):
    """Test dashboard creation error handling."""
    mock_dashboard_api.create.side_effect = Exception("API Error")
    with pytest.raises(DashboardError, match="Failed to create dashboard"):
        dashboard.create()


@patch("datadog.api.Dashboard")
def test_dashboard_update_error(mock_dashboard_api, dashboard):
    """Test dashboard update error handling."""
    dashboard.id = "test-123"
    mock_dashboard_api.update.side_effect = Exception("API Error")
    with pytest.raises(DashboardError, match="Failed to update dashboard"):
        dashboard.update()


@patch("datadog.api.Dashboard")
def test_dashboard_delete_error(mock_dashboard_api, dashboard):
    """Test dashboard deletion error handling."""
    dashboard.id = "test-123"
    mock_dashboard_api.delete.side_effect = Exception("API Error")
    with pytest.raises(DashboardError, match="Failed to delete dashboard"):
        dashboard.delete()


@patch("datadog.api.Dashboard")
def test_dashboard_get_all_error(mock_dashboard_api):
    """Test error handling when getting all dashboards."""
    mock_dashboard_api.get_all.side_effect = Exception("API Error")
    with pytest.raises(DashboardError, match="Failed to get dashboards"):
        Dashboard.get_all()
