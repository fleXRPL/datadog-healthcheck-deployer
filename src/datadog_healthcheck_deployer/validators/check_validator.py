"""Validator for health check configurations."""

from typing import Any, Dict, List

from ..utils.constants import (
    VALID_CHECK_TYPES,
    VALID_CRITERIA,
    VALID_DNS_RECORD_TYPES,
    VALID_HTTP_METHODS,
)
from ..utils.exceptions import ValidationError
from .base import BaseValidator


class CheckValidator(BaseValidator):
    """Validator for health check configurations."""

    def __init__(self) -> None:
        """Initialize validator with check schema."""
        schema = {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "type": {"type": "string", "enum": VALID_CHECK_TYPES},
                "url": {"type": "string", "minLength": 1},
                "method": {"type": "string", "enum": VALID_HTTP_METHODS},
                "locations": {"type": "array", "items": {"type": "string"}},
                "hostname": {"type": "string", "minLength": 1},
                "record_type": {"type": "string", "enum": VALID_DNS_RECORD_TYPES},
                "timeout": {"type": "integer", "minimum": 1},
                "frequency": {"type": "integer", "minimum": 1},
                "success_criteria": {"type": "string", "enum": VALID_CRITERIA},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        }
        super().__init__(schema)

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate health check configuration.

        Args:
            data: Check configuration to validate
            strict: Whether to perform strict validation

        Raises:
            ValidationError: If validation fails
        """
        # First validate required fields
        super()._validate_required_fields(data, ["name", "type"])

        # Validate check type
        check_type = data.get("type", "").lower()
        if check_type not in VALID_CHECK_TYPES:
            raise ValidationError(f"Invalid check type: {check_type}")

        # Validate type-specific fields first
        if check_type == "http":
            if "url" not in data:
                raise ValidationError("URL is required for HTTP check")
            if "method" in data and data["method"] not in VALID_HTTP_METHODS:
                raise ValidationError(f"Invalid HTTP method: {data['method']}")
        elif check_type == "ssl":
            if "hostname" not in data:
                raise ValidationError("Hostname is required for SSL check")
            if "port" in data:
                port = data["port"]
                if not isinstance(port, int) or port < 1 or port > 65535:
                    raise ValidationError(f"Invalid port: {port}")
        elif check_type == "dns":
            if "hostname" not in data:
                raise ValidationError("Hostname is required for DNS check")
            if "record_type" in data:
                record_type = data["record_type"].upper()
                if record_type not in VALID_DNS_RECORD_TYPES:
                    raise ValidationError(f"Invalid DNS record type: {record_type}")
        elif check_type == "tcp":
            if "hostname" not in data:
                raise ValidationError("Hostname is required for TCP check")
            if "port" not in data:
                raise ValidationError("Port is required for TCP check")
            if "port" in data:
                port = data["port"]
                if not isinstance(port, int) or port < 1 or port > 65535:
                    raise ValidationError(f"Invalid port: {port}")

        # Then validate the rest of the fields
        super().validate(data, strict)

    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for optional fields."""
        return {
            "enabled": True,
            "method": "GET",
            "timeout": 10,
            "frequency": 60,
            "success_criteria": "status_code",
            "tags": [],
            "locations": ["aws:us-east-1"],
        }

    def get_required_fields(self) -> List[str]:
        """Get list of required fields."""
        return ["name", "type"]
