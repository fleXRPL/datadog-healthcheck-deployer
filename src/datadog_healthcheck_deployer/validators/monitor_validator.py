"""Validator for monitor configurations."""

from typing import Any, Dict, List

from ..utils.constants import VALID_MONITOR_TYPES
from ..utils.exceptions import ValidationError
from .base import BaseValidator


class MonitorValidator(BaseValidator):
    """Validator for monitor configurations."""

    def __init__(self) -> None:
        """Initialize validator with monitor schema."""
        schema = {
            "type": "object",
            "required": ["name", "type", "query"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "type": {"type": "string", "enum": VALID_MONITOR_TYPES},
                "query": {"type": "string", "minLength": 1},
                "message": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "options": {"type": "object"},
                "thresholds": {"type": "object"},
                "notify_no_data": {"type": "boolean"},
                "no_data_timeframe": {"type": "integer", "minimum": 1},
                "evaluation_delay": {"type": "integer", "minimum": 0},
                "new_host_delay": {"type": "integer", "minimum": 0},
                "renotify_interval": {"type": "integer", "minimum": 0},
                "escalation_message": {"type": "string"},
                "include_tags": {"type": "boolean"},
                "require_full_window": {"type": "boolean"},
            },
        }
        super().__init__(schema)

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate monitor configuration.

        Args:
            data: Monitor configuration to validate
            strict: Whether to perform strict validation

        Raises:
            ValidationError: If validation fails
        """
        super().validate(data, strict)

        # Validate thresholds
        thresholds = data.get("thresholds", {})
        if thresholds:
            self._validate_thresholds(thresholds)

        # Validate options
        options = data.get("options", {})
        if options:
            self._validate_options(options)

    def _validate_thresholds(self, thresholds: Dict[str, Any]) -> None:
        """Validate monitor thresholds.

        Args:
            thresholds: Threshold configuration to validate

        Raises:
            ValidationError: If thresholds are invalid
        """
        valid_levels = ["critical", "warning", "ok", "unknown"]
        for level, value in thresholds.items():
            if level not in valid_levels:
                raise ValidationError(f"Invalid threshold level: {level}")
            if not isinstance(value, (int, float)):
                raise ValidationError(f"Invalid threshold value for {level}: {value}")

    def _validate_options(self, options: Dict[str, Any]) -> None:
        """Validate monitor options.

        Args:
            options: Options configuration to validate

        Raises:
            ValidationError: If options are invalid
        """
        # Validate notification timeout
        timeout = options.get("timeout_h")
        if timeout is not None and (not isinstance(timeout, int) or timeout < 0):
            raise ValidationError(f"Invalid timeout value: {timeout}")

        # Validate renotify interval
        renotify = options.get("renotify_interval")
        if renotify is not None and (not isinstance(renotify, int) or renotify < 0):
            raise ValidationError(f"Invalid renotify interval: {renotify}")

    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for monitor configuration.

        Returns:
            Dictionary of default values
        """
        return {
            "tags": [],
            "notify_no_data": True,
            "no_data_timeframe": 10,
            "include_tags": True,
            "require_full_window": True,
        }

    def get_required_fields(self) -> List[str]:
        """Get required fields for monitor configuration.

        Returns:
            List of required field names
        """
        return ["name", "type", "query"]
