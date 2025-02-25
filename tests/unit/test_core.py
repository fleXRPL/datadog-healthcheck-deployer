"""Tests for the core functionality of the DataDog HealthCheck Deployer."""

import os
from unittest.mock import MagicMock, patch

import pytest

from datadog_healthcheck_deployer.core import HealthCheckDeployer
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


@pytest.fixture
def mock_api():
    """Mock the DataDog API."""
    mock_api = MagicMock()
    mock_api.Synthetics.get_test.return_value = {"public_id": "test-123", "status": "live"}
    mock_api.Synthetics.get_all_tests.return_value = {
        "tests": [
            {"public_id": "test-1", "name": "Test 1", "status": "live"},
            {"public_id": "test-2", "name": "Test 2", "status": "paused"},
        ]
    }
    return mock_api


@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    with patch.dict(
        os.environ,
        {"DD_API_KEY": "test-api-key", "DD_APP_KEY": "test-app-key", "DD_SITE": "datadoghq.com"},
    ):
        yield


def test_healthcheck_deployer_initialization(mock_env_vars):
    """Test HealthCheckDeployer initialization."""
    deployer = HealthCheckDeployer()
    assert deployer.monitor_manager is not None
    assert deployer.dashboard_manager is not None


def test_healthcheck_deployer_missing_credentials():
    """Test HealthCheckDeployer initialization with missing credentials."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(DeployerError, match="DataDog API and application keys are required"):
            HealthCheckDeployer()


def test_healthcheck_deployer_create_http_check():
    """Test creating an HTTP check."""
    deployer = HealthCheckDeployer()
    check_config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
    }

    check = deployer._create_check(check_config)
    assert check.name == "test-http"
    assert check.type == "http"
    assert check.url == "https://test.com/health"


def test_healthcheck_deployer_create_ssl_check():
    """Test creating an SSL check."""
    deployer = HealthCheckDeployer()
    check_config = {
        "name": "test-ssl",
        "type": "ssl",
        "hostname": "test.com",
        "port": 443,
    }

    check = deployer._create_check(check_config)
    assert check.name == "test-ssl"
    assert check.type == "ssl"
    assert check.hostname == "test.com"
    assert check.port == 443


def test_healthcheck_deployer_create_dns_check():
    """Test creating a DNS check."""
    deployer = HealthCheckDeployer()
    check_config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }

    check = deployer._create_check(check_config)
    assert check.name == "test-dns"
    assert check.type == "dns"
    assert check.hostname == "test.com"
    assert check.record_type == "A"


def test_healthcheck_deployer_create_tcp_check():
    """Test creating a TCP check."""
    deployer = HealthCheckDeployer()
    check_config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }

    check = deployer._create_check(check_config)
    assert check.name == "test-tcp"
    assert check.type == "tcp"
    assert check.hostname == "test.com"
    assert check.port == 80


def test_healthcheck_deployer_create_unsupported_check():
    """Test creating an unsupported check type."""
    deployer = HealthCheckDeployer()
    check_config = {
        "name": "test-unsupported",
        "type": "unsupported",
    }

    with pytest.raises(DeployerError, match="Unsupported check type"):
        deployer._create_check(check_config)


def test_healthcheck_deployer_deploy(mock_env_vars, mock_api):
    """Test deploying health checks."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://test.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ), patch("datadog.api", mock_api), patch.object(HealthCheckDeployer, "_handle_integrations"):

        deployer = HealthCheckDeployer()
        deployer.deploy("config.yaml")

        # Check that the check was created
        mock_api.Synthetics.create_test.assert_called_once()


def test_healthcheck_deployer_deploy_specific_check(mock_env_vars, mock_api):
    """Test deploying a specific health check."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http-1",
                "type": "http",
                "url": "https://test1.com/health",
                "locations": ["aws:us-east-1"],
            },
            {
                "name": "test-http-2",
                "type": "http",
                "url": "https://test2.com/health",
                "locations": ["aws:us-east-1"],
            },
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ), patch("datadog.api", mock_api), patch.object(HealthCheckDeployer, "_handle_integrations"):

        deployer = HealthCheckDeployer()
        deployer.deploy("config.yaml", check_name="test-http-2")

        # Check that only one check was created
        assert mock_api.Synthetics.create_test.call_count == 1

        # Check the correct check was created
        args = mock_api.Synthetics.create_test.call_args[0][0]
        assert args["name"] == "test-http-2"


def test_healthcheck_deployer_deploy_dry_run(mock_env_vars, mock_api):
    """Test deploying health checks in dry run mode."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://test.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ), patch("datadog.api", mock_api), patch.object(HealthCheckDeployer, "_handle_integrations"):

        deployer = HealthCheckDeployer()
        deployer.deploy("config.yaml", dry_run=True)

        # Check that no check was created
        mock_api.Synthetics.create_test.assert_not_called()


def test_healthcheck_deployer_validate(mock_env_vars):
    """Test validating health checks configuration."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://test.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ):

        deployer = HealthCheckDeployer()
        # Should not raise exceptions
        deployer.validate("config.yaml")


def test_healthcheck_deployer_validate_schema_only(mock_env_vars):
    """Test validating health checks configuration with schema only."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://test.com/health",
            }
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ):

        deployer = HealthCheckDeployer()
        # Should not raise exceptions or try to validate individual checks
        deployer.validate("config.yaml", schema_only=True)


def test_healthcheck_deployer_validate_specific_check(mock_env_vars):
    """Test validating a specific health check."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http-1",
                "type": "http",
                "url": "https://test1.com/health",
                "locations": ["aws:us-east-1"],
            },
            {
                "name": "test-http-2",
                "type": "http",
                "url": "https://test2.com/health",
                "locations": ["aws:us-east-1"],
            },
        ],
    }

    with patch("datadog_healthcheck_deployer.core.load_config", return_value=config), patch(
        "datadog_healthcheck_deployer.core.validate_config"
    ):

        deployer = HealthCheckDeployer()
        mock_check_validation = MagicMock()

        # Patch the _create_check method to return a mock check
        with patch.object(deployer, "_create_check") as mock_create_check:
            mock_check = MagicMock()
            mock_check.validate = mock_check_validation
            mock_create_check.return_value = mock_check

            deployer.validate("config.yaml", check_name="test-http-2")

            # Should only validate the specified check
            assert mock_create_check.call_count == 1
            assert mock_check_validation.call_count == 1

            # Check that the right check was validated
            check_config = mock_create_check.call_args[0][0]
            assert check_config["name"] == "test-http-2"


def test_healthcheck_deployer_status_specific_check(mock_env_vars, mock_api):
    """Test checking status of a specific health check."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        # Patch the _check_status method to track if it was called
        with patch.object(deployer, "_check_status") as mock_check_status:
            deployer.status(check_name="test-check")
            mock_check_status.assert_called_once_with("test-check", False)


def test_healthcheck_deployer_status_all_checks(mock_env_vars, mock_api):
    """Test checking status of all health checks."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        # Patch the _check_all_status method to track if it was called
        with patch.object(deployer, "_check_all_status") as mock_check_all_status:
            deployer.status()
            mock_check_all_status.assert_called_once_with(False)


def test_healthcheck_deployer_check_status(mock_env_vars, mock_api):
    """Test checking status of a specific health check."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        deployer._check_status("test-check", False)
        mock_api.Synthetics.get_test.assert_called_once_with("test-check")


def test_healthcheck_deployer_check_all_status(mock_env_vars, mock_api):
    """Test checking status of all health checks."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        deployer._check_all_status(False)
        mock_api.Synthetics.get_all_tests.assert_called_once()


def test_healthcheck_deployer_list_checks(mock_env_vars, mock_api):
    """Test listing health checks."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        checks = deployer.list_checks()
        assert len(checks) == 2
        assert checks[0]["name"] == "Test 1"
        assert checks[1]["name"] == "Test 2"


def test_healthcheck_deployer_list_checks_with_tag(mock_env_vars):
    """Test listing health checks with tag filter."""
    mock_api = MagicMock()
    mock_api.Synthetics.get_all_tests.return_value = {
        "tests": [
            {"public_id": "test-1", "name": "Test 1", "tags": ["env:prod"]},
            {"public_id": "test-2", "name": "Test 2", "tags": ["env:dev"]},
        ]
    }

    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        checks = deployer.list_checks(tag="env:prod")
        assert len(checks) == 1
        assert checks[0]["name"] == "Test 1"


def test_healthcheck_deployer_list_checks_with_type(mock_env_vars):
    """Test listing health checks with type filter."""
    mock_api = MagicMock()
    mock_api.Synthetics.get_all_tests.return_value = {
        "tests": [
            {"public_id": "test-1", "name": "Test 1", "type": "http"},
            {"public_id": "test-2", "name": "Test 2", "type": "ssl"},
        ]
    }

    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        checks = deployer.list_checks(check_type="ssl")
        assert len(checks) == 1
        assert checks[0]["name"] == "Test 2"


def test_healthcheck_deployer_delete(mock_env_vars, mock_api):
    """Test deleting a health check."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        deployer.delete("test-check")
        mock_api.Synthetics.delete_test.assert_called_once_with("test-check")


def test_healthcheck_deployer_delete_with_monitors(mock_env_vars, mock_api):
    """Test deleting a health check with its monitors."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        # Patch the monitor_manager.delete_monitors method to track if it was called
        with patch.object(deployer.monitor_manager, "delete_monitors") as mock_delete_monitors:
            deployer.delete("test-check", keep_monitors=False)
            mock_api.Synthetics.delete_test.assert_called_once_with("test-check")
            mock_delete_monitors.assert_called_once_with("test-check")


def test_healthcheck_deployer_delete_keep_monitors(mock_env_vars, mock_api):
    """Test deleting a health check while keeping its monitors."""
    with patch("datadog.api", mock_api):
        deployer = HealthCheckDeployer()
        # Patch the monitor_manager.delete_monitors method to track if it was called
        with patch.object(deployer.monitor_manager, "delete_monitors") as mock_delete_monitors:
            deployer.delete("test-check", keep_monitors=True)
            mock_api.Synthetics.delete_test.assert_called_once_with("test-check")
            mock_delete_monitors.assert_not_called()


def test_healthcheck_deployer_handle_integrations(mock_env_vars):
    """Test handling integrations."""
    deployer = HealthCheckDeployer()
    check = MagicMock()
    config = {
        "monitors": {"enabled": True},
        "dashboards": {"enabled": True},
    }

    # Patch the monitor_manager.configure and dashboard_manager.configure methods
    with patch.object(
        deployer.monitor_manager, "configure"
    ) as mock_monitor_configure, patch.object(
        deployer.dashboard_manager, "configure"
    ) as mock_dashboard_configure:

        deployer._handle_integrations(config, check)

        mock_monitor_configure.assert_called_once_with(check, config["monitors"])
        mock_dashboard_configure.assert_called_once_with(check, config["dashboards"])


def test_healthcheck_deployer_handle_integrations_monitors_only(mock_env_vars):
    """Test handling integrations with monitors only."""
    deployer = HealthCheckDeployer()
    check = MagicMock()
    config = {
        "monitors": {"enabled": True},
    }

    # Patch the monitor_manager.configure and dashboard_manager.configure methods
    with patch.object(
        deployer.monitor_manager, "configure"
    ) as mock_monitor_configure, patch.object(
        deployer.dashboard_manager, "configure"
    ) as mock_dashboard_configure:

        deployer._handle_integrations(config, check)

        mock_monitor_configure.assert_called_once_with(check, config["monitors"])
        mock_dashboard_configure.assert_not_called()


def test_healthcheck_deployer_handle_integrations_dashboards_only(mock_env_vars):
    """Test handling integrations with dashboards only."""
    deployer = HealthCheckDeployer()
    check = MagicMock()
    config = {
        "dashboards": {"enabled": True},
    }

    # Patch the monitor_manager.configure and dashboard_manager.configure methods
    with patch.object(
        deployer.monitor_manager, "configure"
    ) as mock_monitor_configure, patch.object(
        deployer.dashboard_manager, "configure"
    ) as mock_dashboard_configure:

        deployer._handle_integrations(config, check)

        mock_monitor_configure.assert_not_called()
        mock_dashboard_configure.assert_called_once_with(check, config["dashboards"])
