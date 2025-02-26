"""Tests for the base check implementation."""

from unittest.mock import MagicMock, patch

import pytest

from datadog_healthcheck_deployer.checks.base import BaseCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


class TestCheck(BaseCheck):
    """Simple test check class."""

    def __init__(self, config):
        """Initialize test check."""
        super().__init__(config)
        self.config = config

    def _build_api_payload(self):
        """Build API payload for test."""
        return {
            "name": self.name,
            "type": self.type,
            "locations": self.locations,
        }


@pytest.fixture
def basic_config():
    """Basic config fixture."""
    return {"name": "test-check", "type": "http", "locations": ["aws:us-east-1"]}


def test_basic_initialization(basic_config):
    """Test basic check initialization."""
    check = TestCheck(basic_config)
    assert check.name == basic_config["name"]
    assert check.type == basic_config["type"]
    assert check.locations == basic_config["locations"]


def test_missing_name(basic_config):
    """Test check initialization without name."""
    invalid_config = basic_config.copy()
    invalid_config["name"] = ""
    check = TestCheck(invalid_config)
    with pytest.raises(DeployerError, match="Check name is required"):
        check.validate()


def test_missing_type(basic_config):
    """Test check initialization without type."""
    invalid_config = basic_config.copy()
    invalid_config["type"] = ""
    check = TestCheck(invalid_config)
    with pytest.raises(DeployerError, match="Check type is required"):
        check.validate()


def test_missing_locations(basic_config):
    """Test check validation without locations."""
    invalid_config = basic_config.copy()
    invalid_config["locations"] = []
    check = TestCheck(invalid_config)
    with pytest.raises(DeployerError, match="At least one location is required"):
        check.validate()


def test_deploy_new_check(mock_datadog_api, basic_config):
    """Test deploying new check."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.get_test.return_value = None

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()


def test_str_representation(basic_config):
    """Test string representation of check."""
    check = TestCheck(basic_config)
    assert str(check) == f"TestCheck(name={basic_config['name']}, type={basic_config['type']})"


def test_base_check_deploy_existing(mock_datadog_api, basic_config):
    """Test deploying existing check."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.get_test.return_value = {"name": "test-check"}

    with patch("datadog.api", mock_datadog_api):
        check.deploy(force=True)
        mock_datadog_api.Synthetics.update_test.assert_called_once()


def test_base_check_deploy_error(mock_datadog_api, basic_config):
    """Test deployment error handling."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.create_test.side_effect = Exception("API Error")

    with patch("datadog.api", mock_datadog_api):
        with pytest.raises(DeployerError):
            check.deploy()


def test_base_check_get_existing(mock_datadog_api, basic_config):
    """Test getting existing check."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.get_test.return_value = {"name": "test-check"}

    with patch("datadog.api", mock_datadog_api):
        result = check._get_existing_check()
        assert result == {"name": "test-check"}


def test_base_check_get_existing_not_found(mock_datadog_api, basic_config):
    """Test getting non-existent check."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.get_test.return_value = None

    with patch("datadog.api", mock_datadog_api):
        result = check._get_existing_check()
        assert result is None


def test_base_check_deploy_api_error_get_tests(mock_datadog_api, basic_config):
    """Test handling of API error during get_tests."""
    check = TestCheck(basic_config)
    mock_datadog_api.Synthetics.get_test.side_effect = Exception("API Error")

    with patch("datadog.api", mock_datadog_api):
        with pytest.raises(DeployerError):
            check._get_existing_check()


def test_base_check_pause_resume(mock_datadog_api, basic_config):
    """Test check pause and resume."""
    check = TestCheck(basic_config)

    with patch("datadog.api", mock_datadog_api):
        check.pause()
        check.resume()
        assert mock_datadog_api.Synthetics.update_test.call_count == 2


@pytest.fixture
def mock_datadog_api() -> MagicMock:
    """Create mock Datadog API."""
    with patch("datadog_healthcheck_deployer.checks.base.api") as mock_api:
        mock_api.Synthetics = MagicMock()
        # Set up default behaviors
        mock_api.Synthetics.get_test.return_value = None
        mock_api.Synthetics.create_test.return_value = {"public_id": "test-id"}
        mock_api.Synthetics.update_test.return_value = {"public_id": "test-id"}
        yield mock_api
