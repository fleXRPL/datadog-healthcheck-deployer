"""Tests for the TCP check implementation."""

from unittest.mock import patch

import pytest

from datadog_healthcheck_deployer.checks.tcp import TCPCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_tcp_check_initialization(mock_config):
    """Test basic TCP check initialization."""
    config = {"name": "test-tcp", "type": "tcp", "hostname": "test.com", "port": 80}
    check = TCPCheck(config)
    assert check.name == "test-tcp"
    assert check.hostname == "test.com"
    assert check.port == 80


def test_tcp_check_missing_hostname():
    """Test TCP check initialization without hostname."""
    config = {"name": "test", "type": "tcp", "port": 80}
    with pytest.raises(DeployerError, match="Hostname is required"):
        TCPCheck(config)


def test_tcp_check_missing_port():
    """Test TCP check initialization without port."""
    config = {"name": "test", "type": "tcp", "hostname": "test.com"}
    with pytest.raises(DeployerError, match="Port is required"):
        TCPCheck(config)


def test_tcp_check_invalid_port():
    """Test TCP check with invalid port."""
    config = {"name": "test", "type": "tcp", "hostname": "test.com", "port": -1}
    with pytest.raises(DeployerError, match="Invalid port"):
        TCPCheck(config)


def test_tcp_check_with_string_match():
    """Test TCP check with string matching."""
    config = {
        "name": "test",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "send_string": "PING",
        "expect_string": "PONG",
    }
    check = TCPCheck(config)
    payload = check._build_api_payload()

    assert payload["config"]["send_string"] == "PING"
    assert payload["config"]["expect_string"] == "PONG"


def test_tcp_check_deploy(mock_datadog_api):
    """Test TCP check deployment."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "locations": ["aws:us-east-1"],
    }
    check = TCPCheck(config)

    with patch("datadog.api", mock_datadog_api):
        check.deploy()
        mock_datadog_api.Synthetics.create_test.assert_called_once()
        args = mock_datadog_api.Synthetics.create_test.call_args[0][0]
        assert args["config"]["hostname"] == "test.com"
        assert args["config"]["port"] == 80
