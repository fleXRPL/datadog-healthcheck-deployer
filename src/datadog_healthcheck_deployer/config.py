"""Configuration handling for the DataDog HealthCheck Deployer."""

import json
import logging
import os
from typing import Any, Dict

import yaml
from jsonschema import ValidationError, validate

from .utils.exceptions import ConfigError

logger = logging.getLogger(__name__)

# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["version", "healthchecks"],
    "properties": {
        "version": {"type": "string"},
        "defaults": {
            "type": "object",
            "properties": {
                "frequency": {"type": "integer", "minimum": 60},
                "timeout": {"type": "integer", "minimum": 1},
                "locations": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        },
        "variables": {
            "type": "object",
            "additionalProperties": {"type": ["string", "number", "boolean"]},
        },
        "templates": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "template": {"type": "string"},
                },
            },
        },
        "healthchecks": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "template": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "locations": {"type": "array", "items": {"type": "string"}},
                    "frequency": {"type": "integer", "minimum": 60},
                    "timeout": {"type": "integer", "minimum": 1},
                    "monitors": {"type": "object"},
                    "dashboards": {"type": "object"},
                },
            },
        },
    },
}


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file.

    Args:
        config_file: Path to configuration file

    Returns:
        Dict containing configuration

    Raises:
        ConfigError: If configuration loading fails
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config:
            raise ConfigError("Empty configuration file")

        config = _process_config(config)
        return config

    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {str(e)}")


def validate_configuration(config: Dict[str, Any], strict: bool = False) -> None:
    """Validate configuration against schema.

    Args:
        config: Configuration dictionary
        strict: Whether to perform strict validation

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        validate(instance=config, schema=CONFIG_SCHEMA)
        _validate_check_names(config)
        _validate_templates(config)
        if strict:
            _validate_strict(config)
    except ValidationError as e:
        raise ConfigError(f"Configuration validation failed: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {str(e)}")


def _process_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Process configuration with variable substitution and template inheritance.

    Args:
        config: Raw configuration dictionary

    Returns:
        Processed configuration dictionary

    Raises:
        ConfigError: If configuration processing fails
    """
    try:
        config = _substitute_variables(config)
        config = _apply_templates(config)
        config = _apply_defaults(config)
        return config
    except Exception as e:
        raise ConfigError(f"Failed to process configuration: {str(e)}")


def _substitute_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """Substitute variables in configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with variables substituted

    Raises:
        ConfigError: If variable substitution fails
    """
    variables = config.get("variables", {})
    variables.update(
        {key: value for key, value in os.environ.items() if key.startswith(("DD_", "DATADOG_"))}
    )

    def _substitute(value: Any) -> Any:
        if isinstance(value, str):
            for var_name, var_value in variables.items():
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in value:
                    value = value.replace(placeholder, str(var_value))
            return value
        if isinstance(value, dict):
            return {k: _substitute(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_substitute(v) for v in value]
        return value

    return _substitute(config)


def _apply_templates(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply templates to health check configurations.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with templates applied

    Raises:
        ConfigError: If template application fails
    """
    templates = config.get("templates", {})
    processed_checks = []

    for check in config.get("healthchecks", []):
        if "template" in check:
            template_name = check["template"]
            if template_name not in templates:
                raise ConfigError(f"Template {template_name} not found")

            template = templates[template_name].copy()
            template.update(check)
            check = template

        processed_checks.append(check)

    config["healthchecks"] = processed_checks
    return config


def _apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default values to health check configurations.

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with defaults applied
    """
    defaults = config.get("defaults", {})
    for check in config.get("healthchecks", []):
        for key, value in defaults.items():
            if key not in check:
                check[key] = value

    return config


def _validate_check_names(config: Dict[str, Any]) -> None:
    """Validate health check names are unique.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigError: If duplicate check names are found
    """
    names = set()
    for check in config.get("healthchecks", []):
        name = check.get("name")
        if name in names:
            raise ConfigError(f"Duplicate check name: {name}")
        names.add(name)


def _validate_templates(config: Dict[str, Any]) -> None:
    """Validate template configurations.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigError: If template configuration is invalid
    """
    templates = config.get("templates", {})
    for name, template in templates.items():
        if "template" in template:
            parent = template["template"]
            if parent not in templates:
                raise ConfigError(f"Parent template {parent} not found for {name}")
            if parent == name:
                raise ConfigError(f"Template {name} cannot inherit from itself")


def _validate_strict(config: Dict[str, Any]) -> None:
    """Perform strict validation of configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigError: If strict validation fails
    """
    for check in config.get("healthchecks", []):
        if not check.get("locations"):
            raise ConfigError(f"No locations specified for check {check['name']}")
        if not check.get("tags"):
            raise ConfigError(f"No tags specified for check {check['name']}")
        if "monitors" in check and not check["monitors"].get("enabled", True):
            logger.warning("Check %s has monitors disabled", check["name"])


def dump_config(config: Dict[str, Any], output_format: str = "yaml") -> str:
    """Dump configuration to string.

    Args:
        config: Configuration dictionary
        output_format: Output format (yaml or json)

    Returns:
        String representation of configuration

    Raises:
        ConfigError: If configuration dumping fails
    """
    try:
        if output_format == "json":
            return json.dumps(config, indent=2)
        return yaml.dump(config, default_flow_style=False)
    except Exception as e:
        raise ConfigError(f"Failed to dump configuration: {str(e)}")


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configurations.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary

    Raises:
        ConfigError: If configuration merging fails
    """
    try:
        result = {}
        for config in configs:
            _deep_merge(result, config)
        return result
    except Exception as e:
        raise ConfigError(f"Failed to merge configurations: {str(e)}")


def _deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """Deep merge two dictionaries.

    Args:
        target: Target dictionary
        source: Source dictionary
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_merge(target[key], value)
        elif key in target and isinstance(target[key], list) and isinstance(value, list):
            target[key].extend(value)
        else:
            target[key] = value
