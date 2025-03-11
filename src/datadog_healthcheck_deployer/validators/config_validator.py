"""Validator for configuration files."""

from typing import Any, Dict, List

from ..utils.exceptions import ValidationError
from .base import BaseValidator


class ConfigValidator(BaseValidator):
    """Validator for configuration files."""

    def __init__(self) -> None:
        """Initialize validator with configuration schema."""
        schema = {
            "type": "object",
            "required": ["version", "healthchecks"],
            "properties": {
                "version": {"type": "string"},
                "healthchecks": {
                    "type": "array",
                    "items": {"type": "object"},
                    "minItems": 1,
                },
                "defaults": {"type": "object"},
                "variables": {"type": "object"},
                "templates": {"type": "object"},
            },
        }
        super().__init__(schema)

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate configuration.

        Args:
            data: Configuration to validate
            strict: Whether to perform strict validation

        Raises:
            ValidationError: If validation fails
        """
        super().validate(data, strict)

        # Validate version
        version = data.get("version", "")
        if not version.startswith("1."):
            raise ValidationError(f"Unsupported version: {version}")

        # For MVP, we allow empty healthchecks list
        healthchecks = data.get("healthchecks", [])

        # Check for duplicate check names
        check_names = [check.get("name") for check in healthchecks]
        duplicates = {name for name in check_names if check_names.count(name) > 1}
        if duplicates:
            raise ValidationError(f"Duplicate check names found: {', '.join(duplicates)}")

        # Validate variables
        variables = data.get("variables", {})
        if not isinstance(variables, dict):
            raise ValidationError("Variables must be a dictionary")

        # Validate templates
        templates = data.get("templates", {})
        if not isinstance(templates, dict):
            raise ValidationError("Templates must be a dictionary")

        # Validate defaults
        defaults = data.get("defaults", {})
        if not isinstance(defaults, dict):
            raise ValidationError("Defaults must be a dictionary")

    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for configuration.

        Returns:
            Dictionary of default values
        """
        return {
            "version": "1.0",
            "healthchecks": [],
            "defaults": {},
            "variables": {},
            "templates": {},
        }

    def get_required_fields(self) -> List[str]:
        """Get required fields for configuration.

        Returns:
            List of required field names
        """
        return ["version", "healthchecks"]
