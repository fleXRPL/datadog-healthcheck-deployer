"""Test fixtures for the DataDog HealthCheck Deployer."""

from unittest.mock import MagicMock, patch

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
    """Create mock Datadog API."""
    with patch("datadog_healthcheck_deployer.checks.base.api") as mock_api:
        mock_api.Synthetics = MagicMock()
        mock_api.Synthetics.get_test.return_value = None
        mock_api.Synthetics.create_test.return_value = {"public_id": "test-id"}
        yield mock_api


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict("os.environ", {"DD_API_KEY": "test-key", "DD_APP_KEY": "test-key"}):
        yield


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
    """Create a mock check."""
    check = MagicMock()
    check.name = "test-check"
    check.type = "http"
    check.enabled = True
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


@pytest.fixture
def sample_config():
    """Sample configuration for tests."""
    return {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://example.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }
