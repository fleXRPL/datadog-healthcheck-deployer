"""Dashboard class for managing individual DataDog dashboards."""

import logging
from typing import Any, Dict, List

from datadog import api

from ..utils.exceptions import DashboardError
from ..utils.logging import LoggerMixin
from ..utils.validation import validate_dashboard_config

logger = logging.getLogger(__name__)


class Dashboard(LoggerMixin):
    """Class for managing DataDog dashboards."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize dashboard with configuration.

        Args:
            config: Dashboard configuration dictionary
        """
        self.config = config
        self.title = config.get("title")
        self.description = config.get("description")
        self.layout_type = config.get("layout_type", "ordered")
        self.widgets = config.get("widgets", [])
        self.template_variables = config.get("template_variables", [])
        self.id = None  # Set when dashboard is created/loaded

    def validate(self) -> None:
        """Validate dashboard configuration.

        Raises:
            DashboardError: If configuration is invalid
        """
        try:
            validate_dashboard_config(self.config)
        except Exception as e:
            raise DashboardError(str(e), self.title)

    def create(self) -> None:
        """Create dashboard in DataDog.

        Raises:
            DashboardError: If dashboard creation fails
        """
        try:
            self.validate()
            payload = self._build_api_payload()
            response = api.Dashboard.create(**payload)
            self.id = response.get("id")
            self.logger.info("Created dashboard %s with ID %s", self.title, self.id)
        except Exception as e:
            raise DashboardError(f"Failed to create dashboard: {str(e)}", self.title)

    def update(self) -> None:
        """Update existing dashboard in DataDog.

        Raises:
            DashboardError: If dashboard update fails
        """
        try:
            self.validate()
            if not self.id:
                raise DashboardError("Dashboard ID not set", self.title)

            payload = self._build_api_payload()
            api.Dashboard.update(self.id, **payload)
            self.logger.info("Updated dashboard %s (ID: %s)", self.title, self.id)
        except Exception as e:
            raise DashboardError(f"Failed to update dashboard: {str(e)}", self.title)

    def delete(self) -> None:
        """Delete dashboard from DataDog.

        Raises:
            DashboardError: If dashboard deletion fails
        """
        try:
            if not self.id:
                raise DashboardError("Dashboard ID not set", self.title)

            api.Dashboard.delete(self.id)
            self.logger.info("Deleted dashboard %s (ID: %s)", self.title, self.id)
            self.id = None
        except Exception as e:
            raise DashboardError(f"Failed to delete dashboard: {str(e)}", self.title)

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for dashboard creation/update.

        Returns:
            Dict containing the API payload
        """
        return {
            "title": self.title,
            "description": self.description,
            "layout_type": self.layout_type,
            "widgets": self.widgets,
            "template_variables": self.template_variables,
        }

    @classmethod
    def get_all(cls) -> List["Dashboard"]:
        """Get all dashboards.

        Returns:
            List of Dashboard instances

        Raises:
            DashboardError: If dashboard retrieval fails
        """
        try:
            response = api.Dashboard.get_all()
            dashboards = []

            for dashboard_data in response.get("dashboards", []):
                config = {
                    "title": dashboard_data.get("title"),
                    "description": dashboard_data.get("description"),
                    "layout_type": dashboard_data.get("layout_type"),
                    "widgets": dashboard_data.get("widgets", []),
                    "template_variables": dashboard_data.get("template_variables", []),
                }
                dashboard = cls(config)
                dashboard.id = dashboard_data.get("id")
                dashboards.append(dashboard)

            return dashboards

        except Exception as e:
            raise DashboardError(f"Failed to get dashboards: {str(e)}", "all")

    def __repr__(self) -> str:
        """Return string representation of the dashboard."""
        return f"Dashboard(title={self.title}, id={self.id})"
