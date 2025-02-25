"""Configuration handling for the DataDog HealthCheck Deployer."""

import json
import logging
import os
from typing import Any, Dict

import yaml

from .utils.exceptions import ConfigError
from .validators.config_validator import ConfigValidator

logger = logging.getLogger(__name__)

def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from file.

    Args:
        config_file: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigError: If configuration loading fails
    """
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            if not config:
                raise ConfigError("Empty configuration file")
            return config
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {str(e)}")

def validate_config(config: Dict[str, Any], strict: bool = False) -> None:
    """Validate configuration.

    Args:
        config: Configuration to validate
        strict: Whether to perform strict validation

    Raises:
        ConfigError: If validation fails
    """
    try:
        validator = ConfigValidator()
        validator.validate(config, strict)
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {str(e)}")

def dump_config(config: Dict[str, Any], output_format: str = "yaml") -> str:
    """Dump configuration to string.

    Args:
        config: Configuration to dump
        output_format: Output format (yaml or json)

    Returns:
        Configuration string

    Raises:
        ConfigError: If configuration dumping fails
    """
    try:
        if output_format == "json":
            return json.dumps(config, indent=2)
        return yaml.dump(config, default_flow_style=False)
    except Exception as e:
        raise ConfigError(f"Failed to dump configuration: {str(e)}")
