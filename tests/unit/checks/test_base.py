"""Tests for the base check class."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.base import BaseCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


# Minimal concrete implementation for testing
class TestCheck(BaseCheck):
    """Test implementation of BaseCheck."""

    def _build_api_payload(self):
        return {"name": self.name, "type": self.type}

    def validate(self):
        super().validate()


def test_base_check_initialization():
    """Test basic check initialization."""
    config = {"name": "test", "type": "test-type"}
    check = TestCheck(config)
    assert check.name == "test"
    assert check.type == "test-type"
    assert check.enabled is True


def test_base_check_missing_name():
    """Test check initialization without name."""
    config = {"type": "test-type"}
    with pytest.raises(DeployerError, match="Check name is required"):
        TestCheck(config)


def test_base_check_missing_type():
    """Test check initialization without type."""
    config = {"name": "test"}
    with pytest.raises(DeployerError, match="Check type is required"):
        TestCheck(config)


def test_base_check_validation():
    """Test basic check validation."""
    config = {"name": "test", "type": "test-type", "locations": ["aws:us-east-1"]}
    check = TestCheck(config)
    check.validate()  # Should not raise


def test_base_check_validation_no_locations():
    """Test check validation without locations."""
    config = {"name": "test", "type": "test-type"}
    check = TestCheck(config)
    with pytest.raises(DeployerError, match="No locations specified"):
        check.validate()


def test_base_check_deploy(mock_datadog_api):
    """Test basic check deployment."""
    config = {"name": "test", "type": "test-type", "locations": ["aws:us-east-1"]}
    check = TestCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()
