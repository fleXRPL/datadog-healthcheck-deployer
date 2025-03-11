"""Tests for base check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.base import BaseCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


class SimpleCheck(BaseCheck):
    """Simple check implementation for testing."""

    def _build_api_payload(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "locations": self.locations,
            "status": "live" if self.enabled else "paused",
        }


@pytest.fixture
def valid_config():
    """Fixture for valid check configuration."""
    return {
        "name": "test-check",
        "type": "http",
        "locations": ["aws:us-east-1"],
        "enabled": True,
        "frequency": 60,
        "timeout": 10,
    }


def test_base_check_initialization(valid_config):
    """Test basic check initialization."""
    check = SimpleCheck(valid_config)
    assert check.name == valid_config["name"]
    assert check.type == valid_config["type"]
    assert check.locations == valid_config["locations"]
    assert check.enabled == valid_config["enabled"]
    assert check.frequency == valid_config["frequency"]
    assert check.timeout == valid_config["timeout"]


def test_base_check_validation_missing_name():
    """Test validation with missing name."""
    config = {"type": "http", "locations": ["aws:us-east-1"]}
    check = SimpleCheck(config)
    with pytest.raises(DeployerError, match="Check name is required"):
        check.validate()


def test_base_check_validation_missing_type():
    """Test validation with missing type."""
    config = {"name": "test-check", "locations": ["aws:us-east-1"]}
    check = SimpleCheck(config)
    with pytest.raises(DeployerError, match="Check type is required"):
        check.validate()


def test_base_check_validation_missing_locations():
    """Test validation with missing locations."""
    config = {"name": "test-check", "type": "http", "locations": []}
    check = SimpleCheck(config)
    with pytest.raises(DeployerError, match="At least one location is required"):
        check.validate()


@patch("datadog.api.Synthetics")
def test_base_check_deploy_new(mock_synthetics, valid_config):
    """Test deploying a new check."""
    mock_synthetics.get_test.return_value = None
    check = SimpleCheck(valid_config)
    check.deploy()
    mock_synthetics.create_test.assert_called_once()


@patch("datadog.api.Synthetics")
def test_base_check_deploy_existing_no_force(mock_synthetics, valid_config):
    """Test deploying when check exists without force flag."""
    mock_synthetics.get_test.return_value = {"name": "test-check"}
    check = SimpleCheck(valid_config)
    check.deploy(force=False)
    mock_synthetics.create_test.assert_not_called()
    mock_synthetics.update_test.assert_not_called()


@patch("datadog.api.Synthetics")
def test_base_check_deploy_existing_with_force(mock_synthetics, valid_config):
    """Test deploying when check exists with force flag."""
    mock_synthetics.get_test.return_value = {"name": "test-check"}
    check = SimpleCheck(valid_config)
    check.deploy(force=True)
    mock_synthetics.update_test.assert_called_once()


@patch("datadog.api.Synthetics")
def test_base_check_deploy_api_error(mock_synthetics, valid_config):
    """Test handling API error during deployment."""
    mock_synthetics.get_test.return_value = None  # Check doesn't exist
    mock_synthetics.create_test.side_effect = Exception("API Error")
    check = SimpleCheck(valid_config)
    with pytest.raises(DeployerError, match="Failed to deploy check"):
        check.deploy()


@patch("datadog.api.Synthetics")
def test_base_check_get_status(mock_synthetics, valid_config):
    """Test getting check status."""
    mock_synthetics.get_test.return_value = {"name": "test-check", "status": "live"}
    check = SimpleCheck(valid_config)
    status = check.get_status()
    assert status["name"] == "test-check"
    assert status["status"] == "live"


@patch("datadog.api.Synthetics")
def test_base_check_get_status_not_found(mock_synthetics, valid_config):
    """Test getting status of non-existent check."""
    mock_synthetics.get_test.return_value = None
    check = SimpleCheck(valid_config)
    with pytest.raises(DeployerError, match="Check .* not found"):
        check.get_status()


@patch("datadog.api.Synthetics")
def test_base_check_get_results(mock_synthetics, valid_config):
    """Test getting check results."""
    mock_results = {"results": [{"timestamp": 1234567890, "status": "passed"}]}
    mock_synthetics.get_test_results.return_value = mock_results
    check = SimpleCheck(valid_config)
    results = check.get_results()
    assert results == mock_results


@patch("datadog.api.Synthetics")
def test_base_check_get_results_with_filters(mock_synthetics, valid_config):
    """Test getting check results with time filters."""
    mock_results = {"results": [{"timestamp": 1234567890, "status": "passed"}]}
    mock_synthetics.get_test_results.return_value = mock_results
    check = SimpleCheck(valid_config)
    results = check.get_results(from_ts=1234567800, to_ts=1234567900)
    mock_synthetics.get_test_results.assert_called_with(
        check.name, from_ts=1234567800, to_ts=1234567900
    )
    assert results == mock_results


@patch("datadog.api.Synthetics")
def test_base_check_pause_resume(mock_synthetics, valid_config):
    """Test pausing and resuming a check."""
    check = SimpleCheck(valid_config)

    # Test pause
    check.pause()
    mock_synthetics.update_test.assert_called_with(check.name, {"enabled": False})

    # Test resume
    check.resume()
    mock_synthetics.update_test.assert_called_with(check.name, {"enabled": True})


def test_base_check_string_representation(valid_config):
    """Test string representation of check."""
    check = SimpleCheck(valid_config)
    expected = f"SimpleCheck(name={valid_config['name']}, type={valid_config['type']})"
    assert str(check) == expected
