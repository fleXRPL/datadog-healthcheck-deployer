"""Configuration handling for the DataDog HealthCheck Deployer."""

import logging
import os
from typing import Any, Dict, Optional

import yaml

from .utils.exceptions import ConfigError

logger = logging.getLogger(__name__)


def load_config(config_file: str, content: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Load configuration from file or content.

    Args:
        config_file: Path to configuration file
        content: Optional configuration content

    Returns:
        Dict containing configuration

    Raises:
        ConfigError: If configuration loading fails
    """
    try:
        if content is not None:
            config = content
        else:
            if not os.path.exists(config_file):
                raise ConfigError("Configuration file not found")
            with open(config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {str(e)}")

    validate_config(config)
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration structure.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If configuration is invalid
    """
    if not isinstance(config, dict):
        raise ConfigError("Configuration must be a dictionary")

    if "version" not in config:
        raise ConfigError("Configuration version is required")

    if "healthchecks" not in config:
        raise ConfigError("No health checks defined in configuration")

    # Validate check names are unique
    names = set()
    for check in config.get("healthchecks", []):
        name = check.get("name")
        if not name:
            raise ConfigError("Check name is required")
        if name in names:
            raise ConfigError(f"Duplicate check name: {name}")
        names.add(name)

        # Validate required fields
        if "type" not in check:
            raise ConfigError(f"Check type is required for {name}")
        if "locations" not in check:
            raise ConfigError(f"Locations are required for {name}")
