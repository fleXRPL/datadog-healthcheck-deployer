"""Tests for the TCP check implementation."""

import socket
from unittest.mock import MagicMock, patch

import pytest

from datadog_healthcheck_deployer.checks.tcp import TCPCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_tcp_check_initialization():
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


def test_tcp_check_with_ssl_config():
    """Test TCP check with SSL configuration."""
    config = {
        "name": "test-ssl-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 443,
        "ssl": True,
        "ssl_config": {
            "verify_mode": "CERT_REQUIRED",
            "check_hostname": True,
        },
    }
    check = TCPCheck(config)
    assert check.ssl is True
    assert check.ssl_config["verify_mode"] == "CERT_REQUIRED"

    payload = check._build_api_payload()
    assert payload["config"]["ssl"] is True
    assert "ssl_config" in payload["config"]


def test_tcp_check_validate_with_invalid_ssl_config():
    """Test TCP check validation with invalid SSL configuration."""
    config = {
        "name": "test-ssl-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 443,
        "ssl": True,
        "ssl_config": "not_a_dict",
    }
    check = TCPCheck(config)
    with pytest.raises(DeployerError, match="Invalid SSL configuration"):
        check.validate()


def test_tcp_check_validate_with_invalid_retry_config():
    """Test TCP check validation with invalid retry configuration."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "retry": "not_a_dict",
    }
    check = TCPCheck(config)
    with pytest.raises(DeployerError, match="Invalid retry configuration"):
        check.validate()


def test_tcp_check_connection_success():
    """Test successful TCP connection check."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }
    check = TCPCheck(config)

    # Mock the socket operations
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"OK"

    with patch("socket.socket", return_value=mock_socket):
        result = check.check_connection()
        assert result["success"] is True
        mock_socket.connect.assert_called_with(("test.com", 80))
        mock_socket.close.assert_called_once()


def test_tcp_check_connection_failure():
    """Test TCP connection failure."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }
    check = TCPCheck(config)

    # Mock socket to raise an exception
    mock_socket = MagicMock()
    mock_socket.connect.side_effect = socket.error("Connection refused")

    with patch("socket.socket", return_value=mock_socket):
        result = check.check_connection(retry=False)
        assert result["success"] is False
        assert "Connection failed" in result["error"]
        mock_socket.close.assert_called_once()


def test_tcp_check_retry_mechanism():
    """Test TCP check retry mechanism."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "retry": {
            "count": 3,
            "interval": 1,
        },
    }
    check = TCPCheck(config)

    # Mock socket to fail twice then succeed
    mock_socket_fail1 = MagicMock()
    mock_socket_fail1.connect.side_effect = socket.error("Connection refused")

    mock_socket_fail2 = MagicMock()
    mock_socket_fail2.connect.side_effect = socket.error("Connection refused")

    mock_socket_success = MagicMock()

    with patch(
        "socket.socket", side_effect=[mock_socket_fail1, mock_socket_fail2, mock_socket_success]
    ), patch("time.sleep", return_value=None):
        result = check.check_connection()
        assert result["success"] is True
        assert mock_socket_fail1.close.called
        assert mock_socket_fail2.close.called
        assert mock_socket_success.close.called


def test_tcp_check_string_validation_success():
    """Test TCP check string validation success."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "send_string": "PING",
        "expect_string": "PONG",
    }
    check = TCPCheck(config)

    # Mock the socket operations
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"PONG"

    with patch("socket.socket", return_value=mock_socket):
        result = check.check_connection()
        assert result["success"] is True
        mock_socket.send.assert_called_with(b"PING")
        mock_socket.recv.assert_called_once()


def test_tcp_check_string_validation_failure():
    """Test TCP check string validation failure."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
        "send_string": "PING",
        "expect_string": "PONG",
    }
    check = TCPCheck(config)

    # Mock the socket operations
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"ERROR"

    with patch("socket.socket", return_value=mock_socket):
        result = check.check_connection()
        assert result["success"] is False
        assert "Response did not match expected string" in result["error"]
        mock_socket.send.assert_called_with(b"PING")
        mock_socket.recv.assert_called_once()


def test_tcp_check_validate_service():
    """Test TCP service validation."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }
    check = TCPCheck(config)

    # Mock the connection check
    with patch.object(check, "check_connection", return_value={"success": True, "response": "OK"}):
        result = check.validate_service()
        assert result["valid"] is True
        assert "details" in result
        check.check_connection.assert_called_with(retry=False)


def test_tcp_check_validate_service_failure():
    """Test TCP service validation failure."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }
    check = TCPCheck(config)

    # Mock the connection check
    with patch.object(
        check, "check_connection", return_value={"success": False, "error": "Connection refused"}
    ):
        result = check.validate_service()
        assert result["valid"] is False
        assert result["error"] == "Connection refused"
        check.check_connection.assert_called_with(retry=False)


def test_tcp_check_get_results():
    """Test getting TCP check results."""
    config = {
        "name": "test-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 80,
    }
    check = TCPCheck(config)

    # Mock the parent method and validation
    mock_results = {"results": [{"tcp": {"status": "OK"}}]}

    with patch.object(check, "get_results", return_value=mock_results), patch.object(
        check, "validate_service", return_value={"valid": True}
    ):
        results = check.get_results(include_validation=True)
        assert results == mock_results
        assert results["results"][0]["validation"]["valid"] is True
        check.validate_service.assert_called_once()


def test_tcp_check_ssl_socket_creation():
    """Test SSL socket creation in TCP check."""
    config = {
        "name": "test-ssl-tcp",
        "type": "tcp",
        "hostname": "test.com",
        "port": 443,
        "ssl": True,
    }
    check = TCPCheck(config)

    mock_socket = MagicMock()
    mock_ssl_context = MagicMock()
    mock_ssl_socket = MagicMock()

    mock_ssl_context.wrap_socket.return_value = mock_ssl_socket

    with patch("socket.socket", return_value=mock_socket), patch(
        "ssl.create_default_context", return_value=mock_ssl_context
    ):
        socket = check._create_socket()

        assert socket == mock_ssl_socket
        mock_ssl_context.wrap_socket.assert_called_with(mock_socket, server_hostname="test.com")
