"""Tests for the DNS check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.dns import DNSCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_dns_check_initialization(mock_config):
    """Test basic DNS check initialization."""
    config = {"name": "test-dns", "type": "dns", "hostname": "test.com", "record_type": "A"}
    check = DNSCheck(config)
    assert check.name == "test-dns"
    assert check.hostname == "test.com"
    assert check.record_type == "A"


def test_dns_check_missing_hostname():
    """Test DNS check initialization without hostname."""
    config = {"name": "test", "type": "dns", "record_type": "A"}
    with pytest.raises(DeployerError, match="Hostname is required"):
        DNSCheck(config)


def test_dns_check_invalid_record_type():
    """Test DNS check with invalid record type."""
    config = {"name": "test", "type": "dns", "hostname": "test.com", "record_type": "INVALID"}
    with pytest.raises(DeployerError, match="Invalid DNS record type"):
        DNSCheck(config)


def test_dns_check_expected_values():
    """Test DNS check with expected values."""
    config = {
        "name": "test",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "expected_values": ["192.0.2.1"],
    }
    check = DNSCheck(config)
    payload = check._build_api_payload()

    assertions = payload["config"]["assertions"]
    value_assertion = next(a for a in assertions if a["type"] == "recordValue")
    assert value_assertion["target"] == ["192.0.2.1"]


def test_dns_check_deploy(mock_datadog_api):
    """Test DNS check deployment."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "locations": ["aws:us-east-1"],
    }
    check = DNSCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()
        args = mock_datadog_api.Synthetics.create_test.call_args[0][0]
        assert args["config"]["hostname"] == "test.com"
