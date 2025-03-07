"""Base class for all health check types."""

import logging
from abc import ABC
from typing import Any, Dict, Optional

from datadog import api

from ..utils.exceptions import DeployerError

logger = logging.getLogger(__name__)


class BaseCheck(ABC):
    """Base check class."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize base check."""
        self.name = config.get("name")
        self.type = config.get("type")
        self.locations = config.get("locations", [])
        self.enabled = config.get("enabled", True)
        self.frequency = config.get("frequency", 60)
        self.timeout = config.get("timeout", 10)

    def validate(self) -> None:
        """Validate check configuration."""
        if not self.name:
            raise DeployerError("Check name is required")
        if not self.type:
            raise DeployerError("Check type is required")
        if not self.locations:
            raise DeployerError("At least one location is required")

    def deploy(self, force: bool = False) -> None:
        """Deploy the check."""
        try:
            self.validate()
            payload = self._build_api_payload()

            try:
                existing = self._get_existing_check()
                if existing and not force:
                    logger.warning("Check %s already exists, use force=True to update", self.name)
                    return
                elif existing and force:
                    self._update_check(payload)
                else:
                    self._create_check(payload)
            except Exception as e:
                raise DeployerError(f"Failed to deploy check {self.name}: {str(e)}")
        except DeployerError:
            raise
        except Exception as e:
            raise DeployerError(f"Failed to deploy check {self.name}: {str(e)}")

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload."""
        return {
            "name": self.name,
            "type": self.type,
            "locations": self.locations,
            "status": "live" if self.enabled else "paused",
        }

    def _get_existing_check(self) -> Optional[Dict[str, Any]]:
        """Get existing check configuration if it exists."""
        try:
            response = api.Synthetics.get_test(self.name)
            return response if response else None
        except Exception as e:
            raise DeployerError(f"Failed to get check {self.name}: {str(e)}")

    def _create_check(self, payload: Dict[str, Any]) -> None:
        """Create a new health check.

        Args:
            payload: API payload for check creation

        Raises:
            DeployerError: If check creation fails
        """
        try:
            logger.info("Creating check: %s", self.name)
            api.Synthetics.create_test(**payload)
        except Exception as e:
            raise DeployerError(f"Failed to create check {self.name}: {str(e)}")

    def _update_check(self, payload: Dict[str, Any]) -> None:
        """Update an existing health check.

        Args:
            payload: API payload for check update

        Raises:
            DeployerError: If check update fails
        """
        logger.info("Updating check: %s", self.name)
        api.Synthetics.update_test(self.name, payload)

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

    def get_results(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        include_response: bool = True,
    ) -> Dict[str, Any]:
        """Get check results.

        Args:
            from_ts: Start timestamp for results
            to_ts: End timestamp for results
            include_response: Whether to include response details

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
            if not include_response and "results" in response:
                for result in response["results"]:
                    result.pop("response", None)
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
