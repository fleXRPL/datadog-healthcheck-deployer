"""Test fixtures for the DataDog HealthCheck Deployer."""

from unittest.mock import MagicMock

import pytest

# Basic mock data for tests
MOCK_DATA = {
    "http_check": {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "method": "GET",
        "locations": ["aws:us-east-1"],
    },
    "ssl_check": {
        "name": "test-ssl",
        "type": "ssl",
        "hostname": "test.com",
        "port": 443,
        "locations": ["aws:us-east-1"],
    },
    "dns_check": {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "locations": ["aws:us-east-1"],
    },
    "tcp_check": {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "locations": ["aws:us-east-1"],
    },
}


@pytest.fixture
def mock_datadog_api():
    """Mock DataDog API with minimal responses."""
    mock_api = MagicMock()

    # Basic success responses
    mock_api.Monitor.create.return_value = {"id": "test-123"}
    mock_api.Monitor.get.return_value = {"id": "test-123", "status": "OK"}
    mock_api.Monitor.update.return_value = {"id": "test-123"}
    mock_api.Monitor.delete.return_value = {"deleted": "test-123"}

    mock_api.Dashboard.create.return_value = {"id": "dash-123"}
    mock_api.Dashboard.get.return_value = {"id": "dash-123", "title": "Test Dashboard"}
    mock_api.Dashboard.update.return_value = {"id": "dash-123"}
    mock_api.Dashboard.delete.return_value = {"deleted": "dash-123"}

    mock_api.Synthetics.create_test.return_value = {"public_id": "abc-123"}
    mock_api.Synthetics.get_test.return_value = {
        "public_id": "abc-123",
        "status": "live",
        "locations": ["aws:us-east-1"],
    }
    mock_api.Synthetics.update_test.return_value = {"public_id": "abc-123"}
    mock_api.Synthetics.delete_test.return_value = {"deleted": "abc-123"}

    return mock_api


@pytest.fixture
def mock_config():
    """Basic configuration fixture."""
    return {
        "version": "1.0",
        "defaults": {"frequency": 60, "timeout": 10},
        "variables": {
            "domain": "example.com",
            "timeout": 30,
        },
        "templates": {
            "basic_check": {
                "type": "http",
                "timeout": 30,
            },
        },
        "healthchecks": [MOCK_DATA["http_check"]],
    }


@pytest.fixture
def mock_monitor_config():
    """Basic monitor configuration fixture."""
    return {
        "name": "test-monitor",
        "type": "metric alert",
        "query": "avg:system.cpu.user{*}",
        "message": "CPU usage high",
        "thresholds": {
            "critical": 90,
            "warning": 80,
        },
        "tags": ["env:prod", "service:api"],
    }


@pytest.fixture
def mock_dashboard_config():
    """Basic dashboard configuration fixture."""
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
            {"name": "env", "prefix": "environment", "default": "*"},
        ],
    }


@pytest.fixture
def mock_logger():
    """Mock logger fixture."""
    return MagicMock()


@pytest.fixture
def mock_check():
    """Mock health check fixture."""
    check = MagicMock()
    check.name = "test-check"
    check.type = "http"
    check.url = "https://test.com/health"
    check.locations = ["aws:us-east-1"]
    return check


@pytest.fixture
def mock_monitor():
    """Mock monitor fixture."""
    monitor = MagicMock()
    monitor.name = "test-monitor"
    monitor.type = "metric alert"
    monitor.query = "avg:system.cpu.user{*}"
    monitor.id = "test-123"
    return monitor


@pytest.fixture
def mock_dashboard():
    """Mock dashboard fixture."""
    dashboard = MagicMock()
    dashboard.title = "Test Dashboard"
    dashboard.description = "Test description"
    dashboard.widgets = []
    dashboard.id = "dash-123"
    return dashboard


@pytest.fixture
def mock_validator():
    """Mock validator fixture."""
    validator = MagicMock()
    validator.validate.return_value = None
    validator.get_defaults.return_value = {}
    validator.get_required_fields.return_value = []
    return validator
