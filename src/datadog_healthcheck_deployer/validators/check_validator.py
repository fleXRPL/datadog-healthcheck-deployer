"""Validator for health check configurations."""

from typing import Any, Dict, List

from ..utils.constants import VALID_CHECK_TYPES
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
                "enabled": {"type": "boolean"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "locations": {"type": "array", "items": {"type": "string"}},
                "frequency": {"type": "integer", "minimum": 60},
                "timeout": {"type": "integer", "minimum": 1},
                # HTTP check fields
                "url": {"type": "string"},
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
                },
                "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                "body": {"type": "string"},
                "status_code": {"type": "integer", "minimum": 100, "maximum": 599},
                # SSL check fields
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                # DNS check fields
                "domain": {"type": "string"},
                "record_type": {
                    "type": "string",
                    "enum": ["A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT"],
                },
                "resolver": {"type": "string"},
                # TCP check fields
                "target_host": {"type": "string"},
                "target_port": {"type": "integer", "minimum": 1, "maximum": 65535},
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
        super().validate(data, strict)

        # Validate check type specific fields
        check_type = data.get("type", "").lower()
        if check_type == "http":
            self._validate_http_check(data)
        elif check_type == "ssl":
            self._validate_ssl_check(data)
        elif check_type == "dns":
            self._validate_dns_check(data)
        elif check_type == "tcp":
            self._validate_tcp_check(data)

    def _validate_http_check(self, data: Dict[str, Any]) -> None:
        """Validate HTTP check specific fields."""
        if "url" not in data:
            raise ValidationError("URL is required for HTTP check")

        method = data.get("method", "GET").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
            raise ValidationError(f"Invalid HTTP method: {method}")

    def _validate_ssl_check(self, data: Dict[str, Any]) -> None:
        """Validate SSL check specific fields."""
        if "hostname" not in data:
            raise ValidationError("Hostname is required for SSL check")

        port = data.get("port", 443)
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValidationError(f"Invalid port: {port}")

    def _validate_dns_check(self, data: Dict[str, Any]) -> None:
        """Validate DNS check specific fields."""
        if "hostname" not in data:
            raise ValidationError("Hostname is required for DNS check")

        record_type = data.get("record_type", "A").upper()
        if record_type not in ["A", "AAAA", "CNAME", "MX", "NS", "PTR", "SOA", "SRV", "TXT"]:
            raise ValidationError(f"Invalid DNS record type: {record_type}")

    def _validate_tcp_check(self, data: Dict[str, Any]) -> None:
        """Validate TCP check specific fields."""
        if "hostname" not in data:
            raise ValidationError("Hostname is required for TCP check")

        if "port" not in data:
            raise ValidationError("Port is required for TCP check")

        port = data.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValidationError(f"Invalid port: {port}")

    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for check configuration.

        Returns:
            Dictionary of default values
        """
        return {
            "enabled": True,
            "tags": [],
            "locations": ["aws:us-east-1"],
            "frequency": 60,
            "timeout": 10,
        }

    def get_required_fields(self) -> List[str]:
        """Get required fields for check configuration.

        Returns:
            List of required field names
        """
        return ["name", "type"]
