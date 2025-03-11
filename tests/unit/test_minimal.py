"""Minimal test suite for core functionality."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.http import HTTPCheck
from datadog_healthcheck_deployer.core import HealthCheckDeployer
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_http_check_deploy(mock_datadog_api):
    """Test basic HTTP check deployment."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://example.com",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()


def test_core_initialization():
    """Test core deployer initialization."""
    with patch.dict("os.environ", {"DD_API_KEY": "test-key", "DD_APP_KEY": "test-key"}):
        with patch("datadog_healthcheck_deployer.core.initialize") as mock_init:
            HealthCheckDeployer()
            mock_init.assert_called_once()


def test_missing_credentials():
    """Test initialization without credentials."""
    with patch.dict("os.environ", clear=True):
        with pytest.raises(DeployerError, match="DataDog API and application keys are required"):
            HealthCheckDeployer()
