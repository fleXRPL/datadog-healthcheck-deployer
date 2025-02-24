"""Monitor management for the DataDog HealthCheck Deployer."""

from typing import Dict, Any, List, Optional
import logging

from datadog import api
from ..utils.exceptions import MonitorError
from ..utils.validation import validate_monitor_config
from ..utils.logging import LoggerMixin
from ..utils.constants import (
    MONITOR_TYPE_SERVICE,
    MONITOR_TYPE_METRIC,
    MONITOR_OK,
    MONITOR_WARN,
    MONITOR_ALERT,
    MONITOR_NO_DATA
)

logger = logging.getLogger(__name__)

class Monitor(LoggerMixin):
    """Class for managing DataDog monitors."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize monitor with configuration.

        Args:
            config: Monitor configuration dictionary
        """
        self.config = config
        self.name = config.get("name")
        self.type = config.get("type", MONITOR_TYPE_SERVICE)
        self.query = config.get("query")
        self.message = config.get("message")
        self.tags = config.get("tags", [])
        self.options = config.get("options", {})
        self.id = None  # Set when monitor is created/loaded

    def validate(self) -> None:
        """Validate monitor configuration.

        Raises:
            MonitorError: If configuration is invalid
        """
        try:
            validate_monitor_config(self.config)
        except Exception as e:
            raise MonitorError(str(e), self.name)

    def create(self) -> None:
        """Create monitor in DataDog.

        Raises:
            MonitorError: If monitor creation fails
        """
        try:
            self.validate()
            payload = self._build_api_payload()
            response = api.Monitor.create(**payload)
            self.id = response.get("id")
            self.logger.info("Created monitor %s with ID %s", self.name, self.id)
        except Exception as e:
            raise MonitorError(f"Failed to create monitor: {str(e)}", self.name)

    def update(self) -> None:
        """Update existing monitor in DataDog.

        Raises:
            MonitorError: If monitor update fails
        """
        try:
            self.validate()
            if not self.id:
                raise MonitorError("Monitor ID not set", self.name)

            payload = self._build_api_payload()
            api.Monitor.update(self.id, **payload)
            self.logger.info("Updated monitor %s (ID: %s)", self.name, self.id)
        except Exception as e:
            raise MonitorError(f"Failed to update monitor: {str(e)}", self.name)

    def delete(self) -> None:
        """Delete monitor from DataDog.

        Raises:
            MonitorError: If monitor deletion fails
        """
        try:
            if not self.id:
                raise MonitorError("Monitor ID not set", self.name)

            api.Monitor.delete(self.id)
            self.logger.info("Deleted monitor %s (ID: %s)", self.name, self.id)
            self.id = None
        except Exception as e:
            raise MonitorError(f"Failed to delete monitor: {str(e)}", self.name)

    def get_status(self) -> Dict[str, Any]:
        """Get monitor status.

        Returns:
            Dictionary containing monitor status

        Raises:
            MonitorError: If status retrieval fails
        """
        try:
            if not self.id:
                raise MonitorError("Monitor ID not set", self.name)

            response = api.Monitor.get(self.id)
            return {
                "id": self.id,
                "name": self.name,
                "overall_state": response.get("overall_state"),
                "type": response.get("type"),
                "created": response.get("created"),
                "modified": response.get("modified"),
            }
        except Exception as e:
            raise MonitorError(f"Failed to get monitor status: {str(e)}", self.name)

    def mute(self, scope: Optional[str] = None, end: Optional[int] = None) -> None:
        """Mute monitor notifications.

        Args:
            scope: Scope to mute (optional)
            end: End timestamp for muting (optional)

        Raises:
            MonitorError: If muting fails
        """
        try:
            if not self.id:
                raise MonitorError("Monitor ID not set", self.name)

            api.Monitor.mute(self.id, scope=scope, end=end)
            self.logger.info("Muted monitor %s (ID: %s)", self.name, self.id)
        except Exception as e:
            raise MonitorError(f"Failed to mute monitor: {str(e)}", self.name)

    def unmute(self, scope: Optional[str] = None, all_scopes: bool = False) -> None:
        """Unmute monitor notifications.

        Args:
            scope: Scope to unmute (optional)
            all_scopes: Whether to unmute all scopes

        Raises:
            MonitorError: If unmuting fails
        """
        try:
            if not self.id:
                raise MonitorError("Monitor ID not set", self.name)

            api.Monitor.unmute(self.id, scope=scope, all_scopes=all_scopes)
            self.logger.info("Unmuted monitor %s (ID: %s)", self.name, self.id)
        except Exception as e:
            raise MonitorError(f"Failed to unmute monitor: {str(e)}", self.name)

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for monitor creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = {
            "name": self.name,
            "type": self.type,
            "query": self.query,
            "message": self.message,
            "tags": self.tags,
        }

        # Add options if present
        if self.options:
            payload["options"] = self._build_options()

        return payload

    def _build_options(self) -> Dict[str, Any]:
        """Build monitor options.

        Returns:
            Dict containing monitor options
        """
        options = self.options.copy()

        # Set default thresholds if not present
        if "thresholds" not in options:
            options["thresholds"] = {
                "critical": 1,
                "warning": None,
                "ok": None,
            }

        # Set default notification settings
        if "notify_no_data" not in options:
            options["notify_no_data"] = True
        if "no_data_timeframe" not in options:
            options["no_data_timeframe"] = 10  # 10 minutes

        # Set default renotification settings
        if "renotify_interval" not in options:
            options["renotify_interval"] = 60  # 1 hour

        # Set default timeout settings
        if "timeout_h" not in options:
            options["timeout_h"] = 24  # 24 hours

        return options

    @classmethod
    def get_all(cls, tag: Optional[str] = None) -> List["Monitor"]:
        """Get all monitors.

        Args:
            tag: Filter by tag (optional)

        Returns:
            List of Monitor instances

        Raises:
            MonitorError: If monitor retrieval fails
        """
        try:
            params = {"with_downtimes": True}
            if tag:
                params["tag"] = tag

            response = api.Monitor.get_all(**params)
            monitors = []

            for monitor_data in response:
                config = {
                    "name": monitor_data.get("name"),
                    "type": monitor_data.get("type"),
                    "query": monitor_data.get("query"),
                    "message": monitor_data.get("message"),
                    "tags": monitor_data.get("tags", []),
                    "options": monitor_data.get("options", {}),
                }
                monitor = cls(config)
                monitor.id = monitor_data.get("id")
                monitors.append(monitor)

            return monitors

        except Exception as e:
            raise MonitorError(f"Failed to get monitors: {str(e)}", "all")

    @classmethod
    def search(cls, query: str) -> List["Monitor"]:
        """Search for monitors.

        Args:
            query: Search query

        Returns:
            List of Monitor instances

        Raises:
            MonitorError: If search fails
        """
        try:
            response = api.Monitor.search(query=query)
            monitors = []

            for monitor_data in response.get("monitors", []):
                config = {
                    "name": monitor_data.get("name"),
                    "type": monitor_data.get("type"),
                    "query": monitor_data.get("query"),
                    "message": monitor_data.get("message"),
                    "tags": monitor_data.get("tags", []),
                    "options": monitor_data.get("options", {}),
                }
                monitor = cls(config)
                monitor.id = monitor_data.get("id")
                monitors.append(monitor)

            return monitors

        except Exception as e:
            raise MonitorError(f"Failed to search monitors: {str(e)}", query)

    def __repr__(self) -> str:
        """Return string representation of the monitor."""
        return f"Monitor(name={self.name}, type={self.type}, id={self.id})" 