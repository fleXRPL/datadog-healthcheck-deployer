"""Base class for all health check types."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

from datadog import api
from ..utils.exceptions import DeployerError

logger = logging.getLogger(__name__)

class BaseCheck(ABC):
    """Abstract base class for health checks."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize base check with configuration.

        Args:
            config: Check configuration dictionary
        """
        self.config = config
        self.name = config.get("name")
        self.type = config.get("type")
        self.enabled = config.get("enabled", True)
        self.tags = config.get("tags", [])
        self.locations = config.get("locations", [])
        self.frequency = config.get("frequency", 60)
        self.timeout = config.get("timeout", 10)

        if not self.name:
            raise DeployerError("Check name is required")
        if not self.type:
            raise DeployerError("Check type is required")

    @abstractmethod
    def validate(self) -> None:
        """Validate check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        if not self.locations:
            raise DeployerError(f"No locations specified for check {self.name}")

        if self.frequency < 60:
            logger.warning(
                "Check frequency for %s is less than 60 seconds, which may impact performance",
                self.name,
            )

    @abstractmethod
    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for check creation/update.

        Returns:
            Dict containing the API payload
        """
        return {
            "name": self.name,
            "type": self.type,
            "enabled": self.enabled,
            "tags": self.tags,
            "locations": self.locations,
            "frequency": self.frequency,
            "timeout": self.timeout,
        }

    def deploy(self, force: bool = False) -> None:
        """Deploy the health check.

        Args:
            force: Whether to force deployment even if check exists

        Raises:
            DeployerError: If deployment fails
        """
        try:
            self.validate()
            payload = self._build_api_payload()

            existing_check = self._get_existing_check()
            if existing_check:
                if not force:
                    logger.warning("Check %s already exists, use force=True to update", self.name)
                    return
                self._update_check(payload)
            else:
                self._create_check(payload)

        except Exception as e:
            raise DeployerError(f"Failed to deploy check {self.name}: {str(e)}")

    def _get_existing_check(self) -> Optional[Dict[str, Any]]:
        """Get existing check configuration if it exists.

        Returns:
            Existing check configuration or None
        """
        try:
            response = api.Synthetics.get_test(self.name)
            return response if response else None
        except Exception:
            return None

    def _create_check(self, payload: Dict[str, Any]) -> None:
        """Create a new health check.

        Args:
            payload: API payload for check creation

        Raises:
            DeployerError: If check creation fails
        """
        try:
            logger.info("Creating check: %s", self.name)
            api.Synthetics.create_test(payload)
        except Exception as e:
            raise DeployerError(f"Failed to create check {self.name}: {str(e)}")

    def _update_check(self, payload: Dict[str, Any]) -> None:
        """Update an existing health check.

        Args:
            payload: API payload for check update

        Raises:
            DeployerError: If check update fails
        """
        try:
            logger.info("Updating check: %s", self.name)
            api.Synthetics.update_test(self.name, payload)
        except Exception as e:
            raise DeployerError(f"Failed to update check {self.name}: {str(e)}")

    def delete(self) -> None:
        """Delete the health check.

        Raises:
            DeployerError: If check deletion fails
        """
        try:
            logger.info("Deleting check: %s", self.name)
            api.Synthetics.delete_test(self.name)
        except Exception as e:
            raise DeployerError(f"Failed to delete check {self.name}: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get check status.

        Returns:
            Dict containing check status information

        Raises:
            DeployerError: If status retrieval fails
        """
        try:
            response = api.Synthetics.get_test(self.name)
            if not response:
                raise DeployerError(f"Check {self.name} not found")
            return response
        except Exception as e:
            raise DeployerError(f"Failed to get status for check {self.name}: {str(e)}")

    def get_results(self, from_ts: Optional[int] = None, to_ts: Optional[int] = None) -> Dict[str, Any]:
        """Get check results.

        Args:
            from_ts: Start timestamp for results
            to_ts: End timestamp for results

        Returns:
            Dict containing check results

        Raises:
            DeployerError: If results retrieval fails
        """
        try:
            response = api.Synthetics.get_test_results(
                self.name,
                from_ts=from_ts,
                to_ts=to_ts,
            )
            return response
        except Exception as e:
            raise DeployerError(f"Failed to get results for check {self.name}: {str(e)}")

    def pause(self) -> None:
        """Pause the health check.

        Raises:
            DeployerError: If check pause fails
        """
        try:
            logger.info("Pausing check: %s", self.name)
            api.Synthetics.update_test(self.name, {"enabled": False})
        except Exception as e:
            raise DeployerError(f"Failed to pause check {self.name}: {str(e)}")

    def resume(self) -> None:
        """Resume the health check.

        Raises:
            DeployerError: If check resume fails
        """
        try:
            logger.info("Resuming check: %s", self.name)
            api.Synthetics.update_test(self.name, {"enabled": True})
        except Exception as e:
            raise DeployerError(f"Failed to resume check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the check."""
        return f"{self.__class__.__name__}(name={self.name}, type={self.type})" 