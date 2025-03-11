"""Tests for configuration handling."""

from unittest.mock import mock_open, patch

import pytest
import yaml

from datadog_healthcheck_deployer.config import load_config, validate_config
from datadog_healthcheck_deployer.utils.exceptions import ConfigError


def test_load_config_from_file():
    """Test loading configuration from file."""
    config_data = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://example.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }

    mock_file = mock_open(read_data=yaml.dump(config_data))
    with patch("builtins.open", mock_file), patch("os.path.exists", return_value=True):
        config = load_config("dummy.yaml")
        assert config == config_data


def test_load_config_from_content():
    """Test loading configuration from content."""
    config_data = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-http",
                "type": "http",
                "url": "https://example.com/health",
                "locations": ["aws:us-east-1"],
            }
        ],
    }
    config = load_config("dummy.yaml", content=config_data)
    assert config == config_data


def test_load_config_file_not_found():
    """Test loading configuration with missing file."""
    with pytest.raises(ConfigError, match="Configuration file not found"):
        load_config("nonexistent.yaml")


def test_validate_config_invalid_type():
    """Test validation with invalid config type."""
    with pytest.raises(ConfigError, match="Configuration must be a dictionary"):
        validate_config([])


def test_validate_config_missing_version():
    """Test validation with missing version."""
    with pytest.raises(ConfigError, match="Configuration version is required"):
        validate_config({"healthchecks": []})


def test_validate_config_missing_healthchecks():
    """Test validation with missing healthchecks."""
    with pytest.raises(ConfigError, match="No health checks defined"):
        validate_config({"version": "1.0"})


def test_validate_config_duplicate_names():
    """Test validation with duplicate check names."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {"name": "test", "type": "http", "locations": ["aws:us-east-1"]},
            {"name": "test", "type": "http", "locations": ["aws:us-east-1"]},
        ],
    }
    with pytest.raises(ConfigError, match="Duplicate check name"):
        validate_config(config)
