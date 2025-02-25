"""Monitor management for the DataDog HealthCheck Deployer."""

import logging
from typing import Any, Dict, List

from ..checks.base import BaseCheck
from ..utils.constants import (
    MONITOR_TYPE_METRIC,
    MONITOR_TYPE_SERVICE,
    TAG_CHECK_TYPE,
    TAG_MONITOR_TYPE,
)
from ..utils.exceptions import MonitorError
from ..utils.logging import LoggerMixin
from .monitor import Monitor

logger = logging.getLogger(__name__)


class MonitorManager(LoggerMixin):
    """Class for managing monitor integration with health checks."""

    def __init__(self) -> None:
        """Initialize monitor manager."""
        self.monitors: Dict[str, Monitor] = {}

    def configure(self, check: BaseCheck, config: Dict[str, Any]) -> None:
        """Configure monitors for a health check.

        Args:
            check: Health check instance
            config: Monitor configuration dictionary

        Raises:
            MonitorError: If monitor configuration fails
        """
        try:
            # Delete existing monitors if force is True
            if config.get("force", False):
                self.delete_monitors(check.name)

            # Configure each monitor type
            if config.get("availability", {}).get("enabled", True):
                self._configure_availability_monitor(check, config["availability"])

            if config.get("latency", {}).get("enabled", True):
                self._configure_latency_monitor(check, config["latency"])

            if config.get("ssl", {}).get("enabled", True) and hasattr(check, "ssl"):
                self._configure_ssl_monitor(check, config["ssl"])

            if config.get("custom", []):
                for custom_config in config["custom"]:
                    self._configure_custom_monitor(check, custom_config)

        except Exception as e:
            raise MonitorError(f"Failed to configure monitors: {str(e)}", check.name)

    def _configure_availability_monitor(self, check: BaseCheck, config: Dict[str, Any]) -> None:
        """Configure availability monitor.

        Args:
            check: Health check instance
            config: Monitor configuration dictionary

        Raises:
            MonitorError: If monitor configuration fails
        """
        monitor_name = f"{check.name} Availability"
        monitor_config = {
            "name": monitor_name,
            "type": MONITOR_TYPE_SERVICE,
            "query": self._build_availability_query(check),
            "message": config.get("message", self._build_default_message(check, "availability")),
            "tags": self._build_tags(check, "availability"),
            "options": {
                "notify_no_data": True,
                "no_data_timeframe": config.get("no_data_timeframe", 10),
                "thresholds": {
                    "critical": config.get("threshold", 1),
                    "warning": config.get("warning_threshold"),
                },
                "notify_audit": True,
                "include_tags": True,
            },
        }

        monitor = Monitor(monitor_config)
        self._deploy_monitor(monitor)
        self.monitors[monitor_name] = monitor

    def _configure_latency_monitor(self, check: BaseCheck, config: Dict[str, Any]) -> None:
        """Configure latency monitor.

        Args:
            check: Health check instance
            config: Monitor configuration dictionary

        Raises:
            MonitorError: If monitor configuration fails
        """
        monitor_name = f"{check.name} Latency"
        monitor_config = {
            "name": monitor_name,
            "type": MONITOR_TYPE_METRIC,
            "query": self._build_latency_query(check),
            "message": config.get("message", self._build_default_message(check, "latency")),
            "tags": self._build_tags(check, "latency"),
            "options": {
                "notify_no_data": True,
                "no_data_timeframe": config.get("no_data_timeframe", 10),
                "thresholds": {
                    "critical": config.get("threshold", 1000),  # 1 second
                    "warning": config.get("warning_threshold", 500),  # 500ms
                },
                "notify_audit": True,
                "include_tags": True,
            },
        }

        monitor = Monitor(monitor_config)
        self._deploy_monitor(monitor)
        self.monitors[monitor_name] = monitor

    def _configure_ssl_monitor(self, check: BaseCheck, config: Dict[str, Any]) -> None:
        """Configure SSL certificate monitor.

        Args:
            check: Health check instance
            config: Monitor configuration dictionary

        Raises:
            MonitorError: If monitor configuration fails
        """
        monitor_name = f"{check.name} SSL Certificate"
        monitor_config = {
            "name": monitor_name,
            "type": MONITOR_TYPE_METRIC,
            "query": self._build_ssl_query(check),
            "message": config.get("message", self._build_default_message(check, "ssl")),
            "tags": self._build_tags(check, "ssl"),
            "options": {
                "notify_no_data": True,
                "no_data_timeframe": config.get("no_data_timeframe", 10),
                "thresholds": {
                    "critical": config.get("threshold", 7),  # 7 days
                    "warning": config.get("warning_threshold", 30),  # 30 days
                },
                "notify_audit": True,
                "include_tags": True,
            },
        }

        monitor = Monitor(monitor_config)
        self._deploy_monitor(monitor)
        self.monitors[monitor_name] = monitor

    def _configure_custom_monitor(self, check: BaseCheck, config: Dict[str, Any]) -> None:
        """Configure custom monitor.

        Args:
            check: Health check instance
            config: Monitor configuration dictionary

        Raises:
            MonitorError: If monitor configuration fails
        """
        monitor_name = f"{check.name} {config['name']}"
        monitor_config = {
            "name": monitor_name,
            "type": config.get("type", MONITOR_TYPE_METRIC),
            "query": config["query"],
            "message": config.get("message", self._build_default_message(check, "custom")),
            "tags": self._build_tags(check, "custom"),
            "options": config.get("options", {}),
        }

        monitor = Monitor(monitor_config)
        self._deploy_monitor(monitor)
        self.monitors[monitor_name] = monitor

    def _build_availability_query(self, check: BaseCheck) -> str:
        """Build availability monitor query.

        Args:
            check: Health check instance

        Returns:
            Query string
        """
        return f"avg(last_5m):avg:synthetics.check.status{{name:{check.name}}} < 1"

    def _build_latency_query(self, check: BaseCheck) -> str:
        """Build latency monitor query.

        Args:
            check: Health check instance

        Returns:
            Query string
        """
        return f"avg(last_5m):avg:synthetics.check.response_time{{name:{check.name}}} > 1000"

    def _build_ssl_query(self, check: BaseCheck) -> str:
        """Build SSL certificate monitor query.

        Args:
            check: Health check instance

        Returns:
            Query string
        """
        return f"min(last_5m):synthetics.ssl.days_left{{name:{check.name}}} < 7"

    def _build_default_message(self, check: BaseCheck, monitor_type: str) -> str:
        """Build default monitor message.

        Args:
            check: Health check instance
            monitor_type: Type of monitor

        Returns:
            Message string
        """
        message = f"""{{{{#is_alert}}}}
{check.name} {monitor_type} check failed

Check: {check.name}
Type: {check.type}
Status: {{{{check.status}}}}
"""

        if monitor_type == "availability":
            message += "Error: {{check.error}}\n"
        elif monitor_type == "latency":
            message += "Response Time: {{check.response_time}}ms\n"
        elif monitor_type == "ssl":
            message += "Days until expiration: {{check.days_left}}\n"

        message += """
{{{{/is_alert}}}}

{{{{#is_recovery}}}}
{check.name} {monitor_type} check recovered

Check: {check.name}
Type: {check.type}
Status: {{{{check.status}}}}
{{{{/is_recovery}}}}
"""

        return message

    def _build_tags(self, check: BaseCheck, monitor_type: str) -> List[str]:
        """Build monitor tags.

        Args:
            check: Health check instance
            monitor_type: Type of monitor

        Returns:
            List of tags
        """
        tags = check.tags.copy()
        tags.extend(
            [
                f"{TAG_CHECK_TYPE}:{check.type}",
                f"{TAG_MONITOR_TYPE}:{monitor_type}",
                "managed-by:dd-healthcheck",
            ]
        )
        return tags

    def _deploy_monitor(self, monitor: Monitor) -> None:
        """Deploy monitor to DataDog.

        Args:
            monitor: Monitor instance

        Raises:
            MonitorError: If deployment fails
        """
        try:
            # Check if monitor exists
            existing = Monitor.search(f'name:"{monitor.name}"')
            if existing:
                monitor.id = existing[0].id
                monitor.update()
            else:
                monitor.create()
        except Exception as e:
            raise MonitorError(f"Failed to deploy monitor: {str(e)}", monitor.name)

    def delete_monitors(self, check_name: str) -> None:
        """Delete monitors for a health check.

        Args:
            check_name: Name of the health check

        Raises:
            MonitorError: If monitor deletion fails
        """
        try:
            monitors = Monitor.search(f'name:"{check_name}"')
            for monitor in monitors:
                monitor.delete()
                if monitor.name in self.monitors:
                    del self.monitors[monitor.name]
        except Exception as e:
            raise MonitorError(f"Failed to delete monitors: {str(e)}", check_name)

    def get_monitor_status(self, check_name: str) -> List[Dict[str, Any]]:
        """Get status of all monitors for a health check.

        Args:
            check_name: Name of the health check

        Returns:
            List of monitor status dictionaries

        Raises:
            MonitorError: If status retrieval fails
        """
        try:
            monitors = Monitor.search(f'name:"{check_name}"')
            return [monitor.get_status() for monitor in monitors]
        except Exception as e:
            raise MonitorError(f"Failed to get monitor status: {str(e)}", check_name)

    def __repr__(self) -> str:
        """Return string representation of the monitor manager."""
        return f"MonitorManager(monitors={len(self.monitors)})"
