"""Tests for utility functions."""

import hashlib
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from datadog_healthcheck_deployer.utils.utils import (
    calculate_hash,
    dump_yaml,
    format_timestamp,
    load_yaml,
    make_request,
    merge_dicts,
    parse_duration,
    retry_with_backoff,
    substitute_variables,
)


def test_load_yaml_file():
    """Test loading YAML from file."""
    test_data = {"key": "value"}
    mock_file = mock_open(read_data=yaml.dump(test_data))

    with patch("builtins.open", mock_file), patch("os.path.exists", return_value=True):
        result = load_yaml("dummy.yaml")
        assert result == test_data


def test_load_yaml_file_not_found():
    """Test loading YAML from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_yaml("nonexistent.yaml")


def test_dump_yaml():
    """Test dumping data to YAML file."""
    test_data = {"key": "value"}
    mock_file = mock_open()

    with patch("builtins.open", mock_file), patch("os.makedirs"):
        dump_yaml(test_data, "test.yaml")
        # The mock is called multiple times because yaml.dump writes line by line
        assert mock_file().write.called
        # Verify the content was written
        written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
        assert "key: value" in written_content


def test_merge_dicts():
    """Test dictionary merging."""
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"b": {"d": 3}, "e": 4}
    expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    result = merge_dicts(dict1, dict2)
    assert result == expected


def test_substitute_variables():
    """Test variable substitution in data."""
    variables = {"name": "test", "value": 123}
    data = {
        "string": "Hello ${name}",
        "number": "${value}",
        "list": ["${name}", "${value}"],
        "nested": {"key": "${name}"},
    }

    expected = {
        "string": "Hello test",
        "number": "123",
        "list": ["test", "123"],
        "nested": {"key": "test"},
    }

    result = substitute_variables(data, variables)
    assert result == expected


def test_calculate_hash():
    """Test hash calculation."""
    test_data = {"key": "value"}
    expected_hash = hashlib.sha256(json.dumps(test_data, sort_keys=True).encode()).hexdigest()

    result = calculate_hash(test_data)
    assert result == expected_hash


def test_retry_with_backoff_success():
    """Test retry mechanism with successful execution."""
    mock_func = MagicMock(return_value="success")
    result = retry_with_backoff(mock_func, max_attempts=3)
    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_with_backoff_failure():
    """Test retry mechanism with all attempts failing."""
    mock_func = MagicMock(side_effect=Exception("Test error"))

    with pytest.raises(Exception):
        retry_with_backoff(mock_func, max_attempts=3, base_delay=0.1)
    assert mock_func.call_count == 3


def test_format_timestamp():
    """Test timestamp formatting."""
    # Test with datetime object
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert format_timestamp(dt) == "2024-01-01T00:00:00+00:00"

    # Test with timestamp
    assert format_timestamp(1704067200) == "2024-01-01T00:00:00+00:00"

    # Test with ISO string
    assert format_timestamp("2024-01-01T00:00:00Z") == "2024-01-01T00:00:00+00:00"


def test_parse_duration():
    """Test duration string parsing."""
    assert parse_duration("60s") == 60
    assert parse_duration("5m") == 300
    assert parse_duration("2h") == 7200
    assert parse_duration("1d") == 86400
    assert parse_duration("1w") == 604800

    with pytest.raises(ValueError):
        parse_duration("invalid")


@patch("requests.request")
def test_make_request(mock_request):
    """Test HTTP request making."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_request.return_value = mock_response

    result = make_request("GET", "https://example.com")
    assert result == mock_response
    mock_request.assert_called_once_with("GET", "https://example.com")
