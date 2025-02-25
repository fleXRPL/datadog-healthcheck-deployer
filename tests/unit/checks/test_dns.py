"""Tests for the DNS check implementation."""

from unittest.mock import MagicMock, patch

import dns.resolver
import pytest

from datadog_healthcheck_deployer.checks.dns import DNSCheck
from datadog_healthcheck_deployer.utils.exceptions import DeployerError


def test_dns_check_initialization():
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


def test_dns_check_with_nameservers():
    """Test DNS check with custom nameservers."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "nameservers": ["8.8.8.8", "1.1.1.1"],
    }
    check = DNSCheck(config)
    assert check.nameservers == ["8.8.8.8", "1.1.1.1"]

    payload = check._build_api_payload()
    assert payload["config"]["nameservers"] == ["8.8.8.8", "1.1.1.1"]


def test_dns_check_with_timeout():
    """Test DNS check with custom timeout."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "timeout": 5,
    }
    check = DNSCheck(config)
    assert check.timeout == 5

    payload = check._build_api_payload()
    assert payload["config"]["timeout"] == 5


def test_dns_check_resolve_record_success():
    """Test successful DNS record resolution."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    # Create mock Answer object
    mock_answer = MagicMock()
    mock_answer.rrset = [MagicMock()]
    mock_answer.rrset[0].to_text.return_value = "192.0.2.1"
    mock_answer.rrset[0].rdtype = dns.rdatatype.A

    # Mock the resolver
    with patch("dns.resolver.Resolver", return_value=MagicMock()) as mock_resolver:
        mock_resolver.return_value.resolve.return_value = mock_answer

        result = check.resolve_record()

        assert result["success"] is True
        assert len(result["answers"]) == 1
        assert result["answers"][0]["value"] == "192.0.2.1"
        assert result["answers"][0]["type"] == "A"


def test_dns_check_resolve_record_with_nameserver():
    """Test DNS record resolution with specific nameserver."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    # Create mock Answer object
    mock_answer = MagicMock()
    mock_answer.rrset = [MagicMock()]
    mock_answer.rrset[0].to_text.return_value = "192.0.2.1"
    mock_answer.rrset[0].rdtype = dns.rdatatype.A

    # Mock the resolver
    with patch("dns.resolver.Resolver", return_value=MagicMock()) as mock_resolver:
        mock_resolver.return_value.resolve.return_value = mock_answer

        result = check.resolve_record(nameserver="8.8.8.8")

        assert result["success"] is True
        assert result["nameserver"] == "8.8.8.8"
        mock_resolver.return_value.nameservers = ["8.8.8.8"]


def test_dns_check_resolve_record_failure():
    """Test DNS record resolution failure."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    # Mock the resolver to raise an exception
    with patch("dns.resolver.Resolver", return_value=MagicMock()) as mock_resolver:
        mock_resolver.return_value.resolve.side_effect = dns.resolver.NXDOMAIN("Domain not found")

        result = check.resolve_record()

        assert result["success"] is False
        assert "error" in result
        assert "Domain not found" in result["error"]


def test_dns_check_validate_records_success():
    """Test successful DNS record validation."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "expected_values": ["192.0.2.1"],
    }
    check = DNSCheck(config)

    # Mock the resolve_record method
    mock_result = {"success": True, "answers": [{"type": "A", "value": "192.0.2.1"}]}

    with patch.object(check, "resolve_record", return_value=mock_result):
        result = check.validate_records()

        assert result["valid"] is True
        assert "expected_values" in result
        assert "actual_values" in result
        assert result["expected_values"] == ["192.0.2.1"]
        assert result["actual_values"] == ["192.0.2.1"]


def test_dns_check_validate_records_mismatch():
    """Test DNS record validation with mismatched values."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "expected_values": ["192.0.2.1"],
    }
    check = DNSCheck(config)

    # Mock the resolve_record method with different value
    mock_result = {"success": True, "answers": [{"type": "A", "value": "192.0.2.2"}]}

    with patch.object(check, "resolve_record", return_value=mock_result):
        result = check.validate_records()

        assert result["valid"] is False
        assert result["expected_values"] == ["192.0.2.1"]
        assert result["actual_values"] == ["192.0.2.2"]


def test_dns_check_validate_records_resolution_failure():
    """Test DNS record validation when resolution fails."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
        "expected_values": ["192.0.2.1"],
    }
    check = DNSCheck(config)

    # Mock the resolve_record method with failure
    mock_result = {
        "success": False,
        "error": "Resolution failed",
    }

    with patch.object(check, "resolve_record", return_value=mock_result):
        result = check.validate_records()

        assert result["valid"] is False
        assert result["error"] == "Resolution failed"


def test_dns_check_extract_values():
    """Test extracting values from DNS answers."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    answers = [
        {"type": "A", "value": "192.0.2.1"},
        {"type": "A", "value": "192.0.2.2"},
    ]

    values = check._extract_values(answers)
    assert values == ["192.0.2.1", "192.0.2.2"]


def test_dns_check_format_answers():
    """Test formatting DNS answers."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    # Create mock Answer object with multiple records
    mock_answer = MagicMock()
    mock_rr1 = MagicMock()
    mock_rr1.to_text.return_value = "192.0.2.1"
    mock_rr1.rdtype = dns.rdatatype.A

    mock_rr2 = MagicMock()
    mock_rr2.to_text.return_value = "192.0.2.2"
    mock_rr2.rdtype = dns.rdatatype.A

    mock_answer.rrset = [mock_rr1, mock_rr2]

    formatted = check._format_answers(mock_answer)
    assert len(formatted) == 2
    assert formatted[0]["type"] == "A"
    assert formatted[0]["value"] == "192.0.2.1"
    assert formatted[1]["value"] == "192.0.2.2"


def test_dns_check_get_results():
    """Test getting DNS check results."""
    config = {
        "name": "test-dns",
        "type": "dns",
        "hostname": "test.com",
        "record_type": "A",
    }
    check = DNSCheck(config)

    # Mock the parent method and validation
    mock_results = {"results": [{"dns": {"status": "OK"}}]}

    with patch.object(check, "get_results", return_value=mock_results), patch.object(
        check, "validate_records", return_value={"valid": True}
    ):
        results = check.get_results(include_validation=True)
        assert results == mock_results
        assert results["results"][0]["validation"]["valid"] is True
        check.validate_records.assert_called_once()
