"""Tests for configuration handling."""

from unittest.mock import mock_open, patch

import pytest

from datadog_healthcheck_deployer.config import load_config, validate_config
from datadog_healthcheck_deployer.utils.exceptions import ConfigError


def test_load_config_basic():
    """Test basic configuration loading."""
    yaml_content = """
    version: "1.0"
    healthchecks:
      - name: test
        type: http
        url: https://test.com
    """
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        config = load_config("dummy.yaml")
        assert config["version"] == "1.0"
        assert len(config["healthchecks"]) == 1


def test_load_config_empty():
    """Test loading empty configuration."""
    with patch("builtins.open", mock_open(read_data="")):
        with pytest.raises(ConfigError, match="Empty configuration"):
            load_config("dummy.yaml")


def test_validate_config_basic(mock_config):
    """Test basic configuration validation."""
    validate_config(mock_config)  # Should not raise


def test_validate_config_missing_version():
    """Test configuration validation without version."""
    config = {"healthchecks": []}
    with pytest.raises(ConfigError, match="Configuration validation failed"):
        validate_config(config)


def test_validate_config_duplicate_names():
    """Test configuration validation with duplicate check names."""
    config = {
        "version": "1.0",
        "healthchecks": [{"name": "test", "type": "http"}, {"name": "test", "type": "http"}],
    }
    with pytest.raises(ConfigError, match="Duplicate check name"):
        validate_config(config)


def test_validate_config_with_variables():
    """Test configuration validation with variables."""
    config = {
        "version": "1.0",
        "variables": {"domain": "example.com", "timeout": 30},
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://{{domain}}/health",
                "timeout": "{{timeout}}",
            }
        ],
    }
    processed = load_config("dummy.yaml", content=config)
    assert processed["healthchecks"][0]["url"] == "https://example.com/health"
    assert processed["healthchecks"][0]["timeout"] == 30
