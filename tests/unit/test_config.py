"""Tests for configuration handling."""

from unittest.mock import mock_open, patch

import pytest
import yaml

from datadog_healthcheck_deployer.config import (
    _apply_defaults,
    _apply_templates,
    _process_config,
    _substitute_variables,
    _validate_check_names,
    _validate_strict,
    _validate_templates,
    dump_config,
    load_config,
    merge_configs,
    validate_config,
)
from datadog_healthcheck_deployer.utils.exceptions import ConfigError


def test_load_config(tmp_path):
    """Test loading configuration from file."""
    config_file = tmp_path / "config.yaml"
    test_config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-check",
                "type": "http",
                "url": "https://example.com",
            }
        ],
    }
    
    with open(config_file, "w") as f:
        yaml.dump(test_config, f)
    
    loaded_config = load_config(str(config_file))
    assert loaded_config == test_config


def test_load_config_empty():
    """Test loading empty configuration file."""
    with pytest.raises(ConfigError, match="Empty configuration file"):
        load_config("nonexistent.yaml")


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


def test_load_config_invalid_yaml():
    """Test loading invalid YAML configuration."""
    yaml_content = """
    version: "1.0"
    healthchecks:
      - name: test
      type: http  # Indentation error
    """
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        with pytest.raises(yaml.YAMLError):
            load_config("dummy.yaml")


def test_load_config_with_content():
    """Test loading configuration from content."""
    config_content = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://test.com",
            }
        ],
    }
    result = load_config("dummy.yaml", content=config_content)
    assert result["version"] == "1.0"
    assert len(result["healthchecks"]) == 1


def test_validate_config():
    """Test basic configuration validation."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test-check",
                "type": "http",
            }
        ],
    }
    validate_config(config)  # Should not raise


def test_validate_config_missing_version():
    """Test validation with missing version."""
    config = {
        "healthchecks": [],
    }
    with pytest.raises(ConfigError):
        validate_config(config)


def test_validate_config_invalid_version():
    """Test configuration validation with invalid version."""
    config = {"version": "invalid", "healthchecks": []}
    with pytest.raises(ConfigError, match="Configuration validation failed"):
        validate_config(config)


def test_validate_config_missing_healthchecks():
    """Test configuration validation without healthchecks."""
    config = {"version": "1.0"}
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


def test_validate_config_undefined_variable():
    """Test configuration validation with undefined variable."""
    config = {
        "version": "1.0",
        "variables": {"domain": "example.com"},
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://{{domain}}/health",
                "timeout": "{{undefined}}",
            }
        ],
    }
    # This should not raise in normal mode
    processed = load_config("dummy.yaml", content=config)

    # But should raise in strict mode
    with pytest.raises(ConfigError, match="Undefined variable"):
        validate_config(processed, strict=True)


def test_validate_config_with_templates():
    """Test configuration validation with templates."""
    config = {
        "version": "1.0",
        "templates": {
            "api_check": {
                "type": "http",
                "timeout": 30,
                "method": "GET",
            }
        },
        "healthchecks": [
            {
                "name": "test",
                "template": "api_check",
                "url": "https://test.com/health",
            }
        ],
    }
    processed = load_config("dummy.yaml", content=config)
    assert processed["healthchecks"][0]["type"] == "http"
    assert processed["healthchecks"][0]["timeout"] == 30
    assert processed["healthchecks"][0]["method"] == "GET"


def test_validate_config_undefined_template():
    """Test configuration validation with undefined template."""
    config = {
        "version": "1.0",
        "templates": {
            "api_check": {
                "type": "http",
                "timeout": 30,
            }
        },
        "healthchecks": [
            {
                "name": "test",
                "template": "undefined_template",
                "url": "https://test.com/health",
            }
        ],
    }
    with pytest.raises(ConfigError, match="Template .* not found"):
        validate_config(config)


def test_validate_config_with_defaults():
    """Test configuration validation with defaults."""
    config = {
        "version": "1.0",
        "defaults": {
            "timeout": 30,
            "frequency": 60,
            "locations": ["aws:us-east-1"],
        },
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://test.com/health",
            }
        ],
    }
    processed = load_config("dummy.yaml", content=config)
    assert processed["healthchecks"][0]["timeout"] == 30
    assert processed["healthchecks"][0]["frequency"] == 60
    assert processed["healthchecks"][0]["locations"] == ["aws:us-east-1"]


def test_validate_config_override_defaults():
    """Test configuration validation with defaults being overridden."""
    config = {
        "version": "1.0",
        "defaults": {
            "timeout": 30,
            "frequency": 60,
        },
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://test.com/health",
                "timeout": 10,
            }
        ],
    }
    processed = load_config("dummy.yaml", content=config)
    assert processed["healthchecks"][0]["timeout"] == 10  # Overridden
    assert processed["healthchecks"][0]["frequency"] == 60  # From defaults


def test_validate_config_strict():
    """Test strict configuration validation."""
    config = {
        "version": "1.0",
        "healthchecks": [
            {
                "name": "test",
                "type": "http",
                "url": "https://test.com/health",
                "unknown_field": "value",
            }
        ],
    }
    # Should not raise in normal mode
    validate_config(config)

    # But should raise in strict mode
    with pytest.raises(ConfigError, match="Unknown field"):
        validate_config(config, strict=True)


def test_process_config():
    """Test processing configuration."""
    config = {
        "version": "1.0",
        "variables": {"domain": "example.com"},
        "templates": {
            "api_check": {
                "type": "http",
                "timeout": 30,
            }
        },
        "defaults": {
            "frequency": 60,
        },
        "healthchecks": [
            {
                "name": "test",
                "template": "api_check",
                "url": "https://{{domain}}/health",
            }
        ],
    }

    processed = _process_config(config)

    assert processed["healthchecks"][0]["url"] == "https://example.com/health"
    assert processed["healthchecks"][0]["type"] == "http"
    assert processed["healthchecks"][0]["timeout"] == 30
    assert processed["healthchecks"][0]["frequency"] == 60


def test_substitute_variables():
    """Test variable substitution."""
    data = {
        "string": "Hello {{name}}!",
        "number": "{{count}}",
        "boolean": "{{enabled}}",
        "nested": {
            "string": "{{name}}'s value",
            "list": ["{{name}}", "{{count}}"],
        },
    }
    variables = {
        "name": "test",
        "count": 42,
        "enabled": True,
    }

    result = _substitute_variables(data, variables)

    assert result["string"] == "Hello test!"
    assert result["number"] == 42
    assert result["boolean"] is True
    assert result["nested"]["string"] == "test's value"
    assert result["nested"]["list"][0] == "test"
    assert result["nested"]["list"][1] == 42


def test_apply_templates():
    """Test applying templates."""
    config = {
        "templates": {
            "api_check": {
                "type": "http",
                "timeout": 30,
                "method": "GET",
                "headers": {
                    "Content-Type": "application/json",
                },
            }
        },
        "healthchecks": [
            {
                "name": "test1",
                "template": "api_check",
                "url": "https://test1.com/health",
            },
            {
                "name": "test2",
                "template": "api_check",
                "url": "https://test2.com/health",
                "method": "POST",  # Override template
            },
        ],
    }

    result = _apply_templates(config)

    assert result["healthchecks"][0]["type"] == "http"
    assert result["healthchecks"][0]["timeout"] == 30
    assert result["healthchecks"][0]["method"] == "GET"
    assert result["healthchecks"][0]["headers"]["Content-Type"] == "application/json"

    assert result["healthchecks"][1]["type"] == "http"
    assert result["healthchecks"][1]["timeout"] == 30
    assert result["healthchecks"][1]["method"] == "POST"  # Overridden
    assert result["healthchecks"][1]["headers"]["Content-Type"] == "application/json"


def test_apply_defaults():
    """Test applying defaults."""
    config = {
        "defaults": {
            "timeout": 30,
            "frequency": 60,
            "locations": ["aws:us-east-1"],
            "tags": ["env:prod"],
        },
        "healthchecks": [
            {
                "name": "test1",
                "type": "http",
                "url": "https://test1.com/health",
            },
            {
                "name": "test2",
                "type": "http",
                "url": "https://test2.com/health",
                "timeout": 10,  # Override default
                "tags": ["service:api"],  # Will be merged with defaults
            },
        ],
    }

    result = _apply_defaults(config)

    assert result["healthchecks"][0]["timeout"] == 30
    assert result["healthchecks"][0]["frequency"] == 60
    assert result["healthchecks"][0]["locations"] == ["aws:us-east-1"]
    assert result["healthchecks"][0]["tags"] == ["env:prod"]

    assert result["healthchecks"][1]["timeout"] == 10  # Overridden
    assert result["healthchecks"][1]["frequency"] == 60
    assert result["healthchecks"][1]["locations"] == ["aws:us-east-1"]
    # Tags should be merged
    assert "env:prod" in result["healthchecks"][1]["tags"]
    assert "service:api" in result["healthchecks"][1]["tags"]


def test_validate_check_names():
    """Test validating check names."""
    config = {
        "healthchecks": [
            {"name": "check1", "type": "http"},
            {"name": "check2", "type": "http"},
        ],
    }

    # Should not raise
    _validate_check_names(config)

    # Should raise with duplicate names
    config["healthchecks"].append({"name": "check1", "type": "http"})
    with pytest.raises(ConfigError, match="Duplicate check name"):
        _validate_check_names(config)


def test_validate_templates():
    """Test validating templates."""
    config = {
        "templates": {
            "template1": {"type": "http"},
            "template2": {"type": "ssl"},
        },
        "healthchecks": [
            {"name": "check1", "template": "template1"},
            {"name": "check2", "template": "template2"},
        ],
    }

    # Should not raise
    _validate_templates(config)

    # Should raise with undefined template
    config["healthchecks"].append({"name": "check3", "template": "undefined"})
    with pytest.raises(ConfigError, match="Template .* not found"):
        _validate_templates(config)


def test_validate_strict():
    """Test strict validation."""
    config = {
        "healthchecks": [
            {
                "name": "check1",
                "type": "http",
                "url": "https://test.com",
                "valid_field": "value",
            },
        ],
    }

    # Mock the valid fields
    valid_fields = ["name", "type", "url", "valid_field"]

    with patch(
        "datadog_healthcheck_deployer.config.CheckValidator.get_check_fields",
        return_value=valid_fields,
    ):
        # Should not raise
        _validate_strict(config)

        # Add an invalid field
        config["healthchecks"][0]["invalid_field"] = "value"

        # Should raise in strict mode
        with pytest.raises(ConfigError, match="Unknown field"):
            _validate_strict(config)


def test_dump_config():
    """Test dumping configuration to string."""
    config = {
        "version": "1.0",
        "healthchecks": [],
    }
    yaml_output = dump_config(config, "yaml")
    assert "version" in yaml_output
    assert "healthchecks" in yaml_output

    json_output = dump_config(config, "json")
    assert "version" in json_output
    assert "healthchecks" in json_output


def test_merge_configs():
    """Test merging configurations."""
    config1 = {
        "version": "1.0",
        "defaults": {
            "timeout": 30,
        },
        "healthchecks": [
            {
                "name": "check1",
                "type": "http",
            },
        ],
    }

    config2 = {
        "version": "1.0",
        "defaults": {
            "frequency": 60,
        },
        "healthchecks": [
            {
                "name": "check2",
                "type": "ssl",
            },
        ],
    }

    merged = merge_configs(config1, config2)

    # Version should be taken from the first config
    assert merged["version"] == "1.0"

    # Defaults should be merged
    assert merged["defaults"]["timeout"] == 30
    assert merged["defaults"]["frequency"] == 60

    # Healthchecks should be combined
    assert len(merged["healthchecks"]) == 2
    assert merged["healthchecks"][0]["name"] == "check1"
    assert merged["healthchecks"][1]["name"] == "check2"


def test_merge_configs_with_override():
    """Test merging configurations with override."""
    config1 = {
        "version": "1.0",
        "defaults": {
            "timeout": 30,
        },
        "healthchecks": [
            {
                "name": "check1",
                "type": "http",
                "url": "https://test1.com",
            },
        ],
    }

    config2 = {
        "version": "1.1",  # Different version
        "defaults": {
            "timeout": 60,  # Override timeout
            "frequency": 60,
        },
        "healthchecks": [
            {
                "name": "check1",  # Same name, will be updated
                "url": "https://updated.com",
            },
            {
                "name": "check2",
                "type": "ssl",
            },
        ],
    }

    merged = merge_configs(config1, config2)

    # Version should be taken from the second config (override)
    assert merged["version"] == "1.1"

    # Defaults should be merged with override
    assert merged["defaults"]["timeout"] == 60
    assert merged["defaults"]["frequency"] == 60

    # First check should be updated, and second check added
    assert len(merged["healthchecks"]) == 2
    assert merged["healthchecks"][0]["name"] == "check1"
    assert merged["healthchecks"][0]["url"] == "https://updated.com"
    assert merged["healthchecks"][0]["type"] == "http"  # Preserved from first config
    assert merged["healthchecks"][1]["name"] == "check2"
