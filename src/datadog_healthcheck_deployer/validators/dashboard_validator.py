"""Validator for dashboard configurations."""

from typing import Any, Dict, List

from ..utils.exceptions import ValidationError
from .base import BaseValidator


class DashboardValidator(BaseValidator):
    """Validator for dashboard configurations."""

    def __init__(self) -> None:
        """Initialize validator with dashboard schema."""
        schema = {
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "description": {"type": "string"},
                "layout_type": {"type": "string", "enum": ["ordered", "free"]},
                "widgets": {
                    "type": "array",
                    "items": {"type": "object"},
                },
                "template_variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "prefix": {"type": "string"},
                            "default": {"type": "string"},
                        },
                    },
                },
            },
        }
        super().__init__(schema)

    def validate(self, data: Dict[str, Any], strict: bool = False) -> None:
        """Validate dashboard configuration.

        Args:
            data: Dashboard configuration to validate
            strict: Whether to perform strict validation

        Raises:
            ValidationError: If validation fails
        """
        super().validate(data, strict)

        # Validate widgets
        widgets = data.get("widgets", [])
        if widgets:
            self._validate_widgets(widgets)

        # Validate template variables
        template_variables = data.get("template_variables", [])
        if template_variables:
            self._validate_template_variables(template_variables)

    def _validate_widgets(self, widgets: List[Dict[str, Any]]) -> None:
        """Validate dashboard widgets.

        Args:
            widgets: List of widget configurations to validate

        Raises:
            ValidationError: If widgets are invalid
        """
        valid_types = [
            "timeseries",
            "query_value",
            "toplist",
            "change",
            "event_stream",
            "event_timeline",
            "free_text",
            "iframe",
            "image",
            "note",
            "check_status",
            "group",
            "hostmap",
            "service_map",
            "distribution",
            "alert_graph",
            "alert_value",
            "trace_service",
            "slo",
            "monitor_summary",
        ]

        for widget in widgets:
            if not isinstance(widget, dict):
                raise ValidationError("Widget must be an object")

            widget_type = widget.get("type")
            if not widget_type:
                raise ValidationError("Widget type is required")

            if widget_type not in valid_types:
                raise ValidationError(f"Invalid widget type: {widget_type}")

            if widget_type != "free_text" and "title" not in widget:
                raise ValidationError(f"Title is required for widget type: {widget_type}")

            # Validate nested widgets in group
            if widget_type == "group" and "widgets" in widget:
                self._validate_widgets(widget["widgets"])

    def _validate_template_variables(self, variables: List[Dict[str, Any]]) -> None:
        """Validate dashboard template variables.

        Args:
            variables: List of template variable configurations to validate

        Raises:
            ValidationError: If template variables are invalid
        """
        names = set()
        for variable in variables:
            name = variable.get("name")
            if not name:
                raise ValidationError("Template variable name is required")

            if name in names:
                raise ValidationError(f"Duplicate template variable name: {name}")

            names.add(name)

    def get_defaults(self) -> Dict[str, Any]:
        """Get default values for dashboard configuration.

        Returns:
            Dictionary of default values
        """
        return {
            "layout_type": "ordered",
            "widgets": [],
            "template_variables": [],
        }

    def get_required_fields(self) -> List[str]:
        """Get required fields for dashboard configuration.

        Returns:
            List of required field names
        """
        return ["title"]
