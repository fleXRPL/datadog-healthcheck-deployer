"""Tests for the HTTP check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.http import HTTPCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_http_check_initialization():
    """Test basic HTTP check initialization."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    assert check.name == "test-http"
    assert check.url == "https://test.com/health"
    assert check.locations == ["aws:us-east-1"]


def test_http_check_missing_url():
    """Test HTTP check initialization without URL."""
    config = {"name": "test", "type": "http", "locations": ["aws:us-east-1"]}
    check = HTTPCheck(config)
    with pytest.raises(DeployerError, match="URL is required"):
        check.validate()


def test_http_check_deploy(mock_datadog_api):
    """Test HTTP check deployment."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    check.deploy()
    mock_datadog_api.Synthetics.create_test.assert_called_once()


def test_http_check_invalid_method():
    """Test HTTP check with invalid method."""
    config = {
        "name": "test",
        "type": "http",
        "url": "https://test.com",
        "method": "INVALID",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    with pytest.raises(DeployerError, match="Invalid HTTP method"):
        check.validate()


def test_http_check_with_headers():
    """Test HTTP check with custom headers."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "headers": {"Authorization": "Bearer token", "Content-Type": "application/json"},
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    assert check.headers == {"Authorization": "Bearer token", "Content-Type": "application/json"}

    # Test that headers are properly included in the API payload
    payload = check._build_api_payload()
    assert payload["config"]["request"]["headers"] == check.headers


def test_http_check_with_body():
    """Test HTTP check with request body."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "method": "POST",
        "body": '{"status": "check"}',
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    assert check.body == '{"status": "check"}'

    # Test that body is properly included in the API payload
    payload = check._build_api_payload()
    assert payload["config"]["request"]["body"] == check.body


def test_http_check_validation():
    """Test HTTP check validation."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)

    # This shouldn't raise any exceptions
    check.validate()


def test_http_check_with_success_criteria():
    """Test HTTP check with success criteria."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "success_criteria": [{"content": {"type": "json", "target": "healthy"}}],
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)
    payload = check._build_api_payload()

    assert "assertions" in payload["config"]
    assertions = payload["config"]["assertions"]
    assert len(assertions) > 0
    assert assertions[0]["type"] == "body"
    assert assertions[0]["target"] == "healthy"


def test_http_check_update(mock_datadog_api):
    """Test HTTP check update functionality."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)

    # Mock existing check
    mock_datadog_api.Synthetics.get_test.return_value = {"name": "test-http"}

    with patch("datadog.api", mock_datadog_api):
        check.deploy(force=True)
        mock_datadog_api.Synthetics.update_test.assert_called_once()


def test_http_check_get_results(mock_datadog_api):
    """Test getting HTTP check results."""
    config = {
        "name": "test-http",
        "type": "http",
        "url": "https://test.com/health",
        "locations": ["aws:us-east-1"],
    }
    check = HTTPCheck(config)

    mock_results = {
        "results": [
            {
                "status": "passed",
                "timestamp": 1626900000,
                "response": {
                    "status_code": 200,
                    "body": '{"status":"healthy"}',
                    "headers": {"Content-Type": "application/json"},
                    "response_time": 150,
                },
            }
        ]
    }

    mock_datadog_api.Synthetics.get_test_results.return_value = mock_results
    results = check.get_results(include_response=False)

    assert "response" not in results["results"][0]
