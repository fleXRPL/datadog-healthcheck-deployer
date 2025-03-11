"""Base validator class for the DataDog HealthCheck Deployer."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from ..utils.exceptions import ValidationError
from ..utils.logging import LoggerMixin

logger = logging.getLogger(__name__)


class BaseValidator(ABC, LoggerMixin):
    """Abstract base class for validators."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        """Initialize validator with schema.

        Args:
            schema: JSON schema for validation
        """
        self.schema = schema

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate data against schema.

        Args:
            data: Data to validate
            strict: Whether to perform strict validation

        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields first
        if "required" in self.schema:
            self._validate_required_fields(data, self.schema["required"])

        # Validate properties
        if "properties" in self.schema:
            for field, field_schema in self.schema["properties"].items():
                if field in data:
                    # Validate type
                    if "type" in field_schema:
                        type_map = {
                            "string": str,
                            "integer": int,
                            "number": (int, float),
                            "boolean": bool,
                            "array": list,
                            "object": dict,
                        }
                        expected_type = type_map.get(field_schema["type"])
                        if expected_type:
                            if not isinstance(data[field], expected_type):
                                if field == "variables":
                                    raise ValidationError("Variables must be a dictionary")
                                elif field == "templates":
                                    raise ValidationError("Templates must be a dictionary")
                                elif field == "defaults":
                                    raise ValidationError("Defaults must be a dictionary")
                                else:
                                    raise ValidationError(f"Invalid type for field {field}")

                    # Validate enum
                    if "enum" in field_schema:
                        if data[field] not in field_schema["enum"]:
                            enum_values = field_schema["enum"]
                            if field == "method":
                                raise ValidationError(
                                    f"'{data[field]}' is not one of {enum_values}"
                                )
                            elif field == "type":
                                raise ValidationError(
                                    f"'{data[field]}' is not one of {enum_values}"
                                )
                            elif field == "record_type":
                                raise ValidationError(
                                    f"'{data[field]}' is not one of {enum_values}"
                                )
                            else:
                                raise ValidationError(
                                    f"'{data[field]}' is not one of {enum_values}"
                                )

                    # Validate minimum length
                    if "minLength" in field_schema:
                        if len(data[field]) < field_schema["minLength"]:
                            raise ValidationError(f"Field {field} is too short")

                    # Validate minimum value
                    if "minimum" in field_schema:
                        if data[field] < field_schema["minimum"]:
                            raise ValidationError(f"Field {field} is too small")

                    # Validate array items
                    if "items" in field_schema:
                        if not isinstance(data[field], list):
                            raise ValidationError(f"Field {field} must be a list")
                        for item in data[field]:
                            if "type" in field_schema["items"]:
                                expected_type = type_map.get(field_schema["items"]["type"])
                                if expected_type and not isinstance(item, expected_type):
                                    raise ValidationError(f"Invalid type for item in {field}")

    @abstractmethod
    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for schema.

        Returns:
            Dictionary of default values
        """
        pass

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """Get required fields from schema.

        Returns:
            List of required field names
        """
        pass

    def _validate_required_fields(self, data: Dict[str, Any], fields: List[str]) -> None:
        """Validate required fields are present.

        Args:
            data: Data to validate
            fields: List of required field names

        Raises:
            ValidationError: If required fields are missing
        """
        missing = [field for field in fields if field not in data]
        if missing:
            field = missing[0]  # Report first missing field
            raise ValidationError(f"'{field}' is a required property")

    def _validate_field_type(self, value: Any, expected_type: type, field: str) -> None:
        """Validate field type.

        Args:
            value: Value to validate
            expected_type: Expected type
            field: Field name

        Raises:
            ValidationError: If field type is invalid
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid type for field {field}. Expected {expected_type.__name__}, got {type(value).__name__}"
            )

    def _validate_enum(self, value: Any, valid_values: List[Any], field: str) -> None:
        """Validate field value is in enum.

        Args:
            value: Value to validate
            valid_values: List of valid values
            field: Field name

        Raises:
            ValidationError: If value is not in enum
        """
        if value not in valid_values:
            raise ValidationError(f"'{value}' is not one of {valid_values}")

    def _validate_range(
        self,
        value: Union[int, float],
        minimum: Optional[Union[int, float]] = None,
        maximum: Optional[Union[int, float]] = None,
        field: str = "",
    ) -> None:
        """Validate numeric field is within range.

        Args:
            value: Value to validate
            minimum: Minimum allowed value
            maximum: Maximum allowed value
            field: Field name

        Raises:
            ValidationError: If value is out of range
        """
        if minimum is not None and value < minimum:
            raise ValidationError(f"Value for field {field} must be >= {minimum}")
        if maximum is not None and value > maximum:
            raise ValidationError(f"Value for field {field} must be <= {maximum}")

    def _validate_string_length(
        self,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        field: str = "",
    ) -> None:
        """Validate string length.

        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            field: Field name

        Raises:
            ValidationError: If string length is invalid
        """
        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"Length of field {field} must be >= {min_length}")
        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"Length of field {field} must be <= {max_length}")

    def _validate_pattern(self, value: str, pattern: str, field: str) -> None:
        """Validate string matches pattern.

        Args:
            value: String to validate
            pattern: Regular expression pattern
            field: Field name

        Raises:
            ValidationError: If string doesn't match pattern
        """
        import re

        if not re.match(pattern, value):
            raise ValidationError(f"Value for field {field} must match pattern: {pattern}")

    def __repr__(self) -> str:
        """Return string representation of the validator."""
        return f"{self.__class__.__name__}()"
