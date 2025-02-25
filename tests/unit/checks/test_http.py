"""Tests for the HTTP check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.http import HTTPCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_http_check_initialization(mock_config):
    """Test basic HTTP check initialization."""
    check = HTTPCheck(mock_config["healthchecks"][0])
    assert check.name == "test-http"
    assert check.url == "https://test.com/health"
    assert check.method == "GET"


def test_http_check_missing_url():
    """Test HTTP check initialization without URL."""
    config = {"name": "test", "type": "http"}
    with pytest.raises(DeployerError, match="URL is required"):
        HTTPCheck(config)


def test_http_check_invalid_method():
    """Test HTTP check with invalid method."""
    config = {"name": "test", "type": "http", "url": "https://test.com", "method": "INVALID"}
    with pytest.raises(DeployerError, match="Invalid HTTP method"):
        HTTPCheck(config)


def test_http_check_success_criteria():
    """Test HTTP check with success criteria."""
    config = {
        "name": "test",
        "type": "http",
        "url": "https://test.com",
        "success_criteria": [{"status_code": 200}, {"response_time": 1000}],
    }
    check = HTTPCheck(config)
    payload = check._build_api_payload()

    assert len(payload["config"]["assertions"]) == 2
    assert payload["config"]["assertions"][0]["type"] == "statusCode"
    assert payload["config"]["assertions"][1]["type"] == "responseTime"


def test_http_check_deploy(mock_datadog_api):
    """Test HTTP check deployment."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()
        args = mock_datadog_api.Synthetics.create_test.call_args[0][0]
        assert args["config"]["request"]["url"] == "https://test.com/health"
