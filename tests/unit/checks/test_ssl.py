"""Tests for the SSL check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.ssl import SSLCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_ssl_check_initialization(mock_config):
    """Test basic SSL check initialization."""
    config = {"name": "test-ssl", "type": "ssl", "hostname": "test.com", "port": 443}
    check = SSLCheck(config)
    assert check.name == "test-ssl"
    assert check.hostname == "test.com"
    assert check.port == 443


def test_ssl_check_missing_hostname():
    """Test SSL check initialization without hostname."""
    config = {"name": "test", "type": "ssl", "port": 443}
    with pytest.raises(DeployerError, match="Hostname is required"):
        SSLCheck(config)


def test_ssl_check_invalid_port():
    """Test SSL check with invalid port."""
    config = {"name": "test", "type": "ssl", "hostname": "test.com", "port": 70000}
    with pytest.raises(DeployerError, match="Invalid port"):
        SSLCheck(config)


def test_ssl_check_expiry_threshold():
    """Test SSL check with expiry threshold."""
    config = {
        "name": "test",
        "type": "ssl",
        "hostname": "test.com",
        "port": 443,
        "expiry_threshold": 30,
    }
    check = SSLCheck(config)
    payload = check._build_api_payload()

    assertions = payload["config"]["assertions"]
    expiry_assertion = next(a for a in assertions if a["type"] == "expirationDays")
    assert expiry_assertion["target"] == 30


def test_ssl_check_deploy(mock_datadog_api):
    """Test SSL check deployment."""
    config = {
        "name": "test-ssl",
        "type": "ssl",
        "hostname": "test.com",
        "port": 443,
        "locations": ["aws:us-east-1"],
    }
    check = SSLCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()
        args = mock_datadog_api.Synthetics.create_test.call_args[0][0]
        assert args["config"]["hostname"] == "test.com"
