"""Core functionality for the DataDog HealthCheck Deployer."""

import logging
import os
from typing import Any, Dict, List, Optional

from datadog import api, initialize

from .checks.http import HTTPCheck
from .config import load_config
from .utils.exceptions import DeployerError

logger = logging.getLogger(__name__)


class HealthCheckDeployer:
    """Main class for deploying and managing health checks."""

    def __init__(self) -> None:
        """Initialize the deployer."""
        self._initialize_datadog()

    def _initialize_datadog(self) -> None:
        """Initialize the DataDog API client."""
        api_key = os.getenv("DD_API_KEY")
        app_key = os.getenv("DD_APP_KEY")

        if not api_key or not app_key:
            raise DeployerError("DataDog API and application keys are required")

        initialize(api_key=api_key, app_key=app_key)

    def deploy(
        self,
        config_file: str,
        check_name: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """Deploy health checks from configuration."""
        config = load_config(config_file)

        for check_config in config.get("healthchecks", []):
            name = check_config.get("name")
            if check_name and name != check_name:
                continue

            check = HTTPCheck(check_config)
            check.deploy(force=force)

    def delete(self, check_name: str) -> None:
        """Delete a health check."""
        try:
            api.Synthetics.delete_test(public_id=check_name)
        except Exception as e:
            raise DeployerError(f"Failed to delete check {check_name}: {str(e)}")

    def list_checks(self) -> List[Dict[str, Any]]:
        """List all health checks."""
        try:
            response = api.Synthetics.get_all_tests()
            return response.get("tests", [])
        except Exception as e:
            raise DeployerError(f"Failed to list checks: {str(e)}")
