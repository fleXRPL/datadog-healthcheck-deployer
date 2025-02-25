"""Dashboard manager for the DataDog HealthCheck Deployer."""

import logging
from typing import Any, Dict, List, Optional

from ..utils.exceptions import DashboardError
from ..utils.logging import LoggerMixin
from .dashboard import Dashboard

logger = logging.getLogger(__name__)


class DashboardManager(LoggerMixin):
    """Class for managing dashboard deployments."""

    def __init__(self) -> None:
        """Initialize the dashboard manager."""
        self.dashboards: Dict[str, Dashboard] = {}

    def configure(self, check: Any, config: Dict[str, Any]) -> None:
        """Configure dashboards for a health check.

        Args:
            check: Health check instance
            config: Dashboard configuration dictionary

        Raises:
            DashboardError: If dashboard configuration fails
        """
        try:
            if not config.get("enabled", True):
                self.logger.info("Dashboards disabled for check %s", check.name)
                return

            template = config.get("template")
            widgets = config.get("widgets", [])

            if template:
                dashboard_config = self._apply_template(template, check)
            else:
                dashboard_config = self._build_dashboard_config(check, widgets)

            dashboard = Dashboard(dashboard_config)
            self.dashboards[check.name] = dashboard
            self._deploy_dashboard(dashboard)

        except Exception as e:
            raise DashboardError(f"Failed to configure dashboards: {str(e)}", check.name)

    def _apply_template(self, template: str, check: Any) -> Dict[str, Any]:
        """Apply dashboard template for a check.

        Args:
            template: Template name
            check: Health check instance

        Returns:
            Dashboard configuration dictionary

        Raises:
            DashboardError: If template application fails
        """
        templates = {
            "basic_health": self._basic_health_template,
            "service_health": self._service_health_template,
            "detailed_health": self._detailed_health_template,
        }

        template_func = templates.get(template)
        if not template_func:
            raise DashboardError(f"Unknown template: {template}", check.name)

        return template_func(check)

    def _basic_health_template(self, check: Any) -> Dict[str, Any]:
        """Build basic health dashboard configuration.

        Args:
            check: Health check instance

        Returns:
            Dashboard configuration dictionary
        """
        return {
            "title": f"{check.name} Health Overview",
            "description": f"Basic health dashboard for {check.name}",
            "layout_type": "ordered",
            "widgets": [
                {
                    "title": "Health Check Status",
                    "type": "check_status",
                    "check": check.name,
                },
                {
                    "title": "Response Time",
                    "type": "timeseries",
                    "query": f"avg:healthcheck.response_time{{check:{check.name}}}",
                },
                {
                    "title": "Success Rate",
                    "type": "query_value",
                    "query": f"avg:healthcheck.success{{check:{check.name}}}",
                },
            ],
        }

    def _service_health_template(self, check: Any) -> Dict[str, Any]:
        """Build service health dashboard configuration.

        Args:
            check: Health check instance

        Returns:
            Dashboard configuration dictionary
        """
        return {
            "title": f"{check.name} Service Health",
            "description": f"Service health dashboard for {check.name}",
            "layout_type": "ordered",
            "widgets": [
                {
                    "title": "Service Status",
                    "type": "group",
                    "widgets": [
                        {
                            "title": "Health Check Status",
                            "type": "check_status",
                            "check": check.name,
                        },
                        {
                            "title": "Uptime",
                            "type": "query_value",
                            "query": f"avg:healthcheck.uptime{{check:{check.name}}}",
                        },
                    ],
                },
                {
                    "title": "Performance Metrics",
                    "type": "group",
                    "widgets": [
                        {
                            "title": "Response Time",
                            "type": "timeseries",
                            "query": f"avg:healthcheck.response_time{{check:{check.name}}}",
                        },
                        {
                            "title": "Success Rate",
                            "type": "timeseries",
                            "query": f"avg:healthcheck.success{{check:{check.name}}}",
                        },
                    ],
                },
            ],
        }

    def _detailed_health_template(self, check: Any) -> Dict[str, Any]:
        """Build detailed health dashboard configuration.

        Args:
            check: Health check instance

        Returns:
            Dashboard configuration dictionary
        """
        return {
            "title": f"{check.name} Detailed Health",
            "description": f"Detailed health dashboard for {check.name}",
            "layout_type": "ordered",
            "widgets": [
                {
                    "title": "Health Overview",
                    "type": "group",
                    "widgets": [
                        {
                            "title": "Health Check Status",
                            "type": "check_status",
                            "check": check.name,
                        },
                        {
                            "title": "Uptime",
                            "type": "query_value",
                            "query": f"avg:healthcheck.uptime{{check:{check.name}}}",
                        },
                    ],
                },
                {
                    "title": "Performance",
                    "type": "group",
                    "widgets": [
                        {
                            "title": "Response Time",
                            "type": "timeseries",
                            "query": f"avg:healthcheck.response_time{{check:{check.name}}}",
                        },
                        {
                            "title": "Success Rate",
                            "type": "timeseries",
                            "query": f"avg:healthcheck.success{{check:{check.name}}}",
                        },
                    ],
                },
                {
                    "title": "Errors",
                    "type": "group",
                    "widgets": [
                        {
                            "title": "Error Rate",
                            "type": "timeseries",
                            "query": f"sum:healthcheck.errors{{check:{check.name}}}.as_rate()",
                        },
                        {
                            "title": "Error Types",
                            "type": "toplist",
                            "query": (
                                f"top(sum:healthcheck.errors{{check:{check.name}}} "
                                "by {error_type}, 10, 'sum', 'desc')"
                            ),
                        },
                    ],
                },
            ],
        }

    def _build_dashboard_config(self, check: Any, widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build custom dashboard configuration.

        Args:
            check: Health check instance
            widgets: List of widget configurations

        Returns:
            Dashboard configuration dictionary
        """
        return {
            "title": f"{check.name} Dashboard",
            "description": f"Custom dashboard for {check.name}",
            "layout_type": "ordered",
            "widgets": widgets,
        }

    def _deploy_dashboard(self, dashboard: Dashboard) -> None:
        """Deploy a dashboard.

        Args:
            dashboard: Dashboard instance

        Raises:
            DashboardError: If dashboard deployment fails
        """
        try:
            if dashboard.id:
                dashboard.update()
            else:
                dashboard.create()
        except Exception as e:
            raise DashboardError(f"Failed to deploy dashboard: {str(e)}", dashboard.title)

    def delete_dashboards(self, check_name: str) -> None:
        """Delete dashboards for a health check.

        Args:
            check_name: Name of the health check

        Raises:
            DashboardError: If dashboard deletion fails
        """
        try:
            dashboard = self.dashboards.get(check_name)
            if dashboard:
                dashboard.delete()
                del self.dashboards[check_name]
        except Exception as e:
            raise DashboardError(f"Failed to delete dashboards: {str(e)}", check_name)

    def get_dashboard_status(self, check_name: str) -> Optional[Dict[str, Any]]:
        """Get dashboard status for a health check.

        Args:
            check_name: Name of the health check

        Returns:
            Dashboard status dictionary or None

        Raises:
            DashboardError: If status retrieval fails
        """
        try:
            dashboard = self.dashboards.get(check_name)
            if not dashboard:
                return None

            return {
                "title": dashboard.title,
                "id": dashboard.id,
                "widgets_count": len(dashboard.widgets),
            }
        except Exception as e:
            raise DashboardError(f"Failed to get dashboard status: {str(e)}", check_name)

    def __repr__(self) -> str:
        """Return string representation of the dashboard manager."""
        return f"DashboardManager(dashboards={len(self.dashboards)})"
