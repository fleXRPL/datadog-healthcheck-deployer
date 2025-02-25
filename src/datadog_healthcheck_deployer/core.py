"""Core functionality for the DataDog HealthCheck Deployer."""

import logging
import os
from typing import Any, Dict, List, Optional

from datadog import api, initialize

from .checks.base import BaseCheck
from .checks.dns import DNSCheck
from .checks.http import HTTPCheck
from .checks.ssl import SSLCheck
from .checks.tcp import TCPCheck
from .config import load_config, validate_config
from .dashboards import DashboardManager
from .monitors import MonitorManager
from .utils.exceptions import DeployerError

logger = logging.getLogger(__name__)


class HealthCheckDeployer:
    """Main class for deploying and managing health checks."""

    def __init__(self) -> None:
        """Initialize the deployer with DataDog credentials."""
        self._initialize_datadog()
        self.monitor_manager = MonitorManager()
        self.dashboard_manager = DashboardManager()

    def _initialize_datadog(self) -> None:
        """Initialize the DataDog API client."""
        api_key = os.getenv("DD_API_KEY")
        app_key = os.getenv("DD_APP_KEY")
        site = os.getenv("DD_SITE", "datadoghq.com")

        if not api_key or not app_key:
            raise DeployerError("DataDog API and application keys are required")

        initialize(
            api_key=api_key,
            app_key=app_key,
            api_host=f"https://api.{site}",
        )

    def _create_check(self, check_config: Dict[str, Any]) -> BaseCheck:
        """Create a health check instance based on type."""
        check_type = check_config.get("type", "").lower()
        check_types = {
            "http": HTTPCheck,
            "ssl": SSLCheck,
            "dns": DNSCheck,
            "tcp": TCPCheck,
        }

        check_class = check_types.get(check_type)
        if not check_class:
            raise DeployerError(f"Unsupported check type: {check_type}")

        return check_class(check_config)

    def deploy(
        self,
        config_file: str,
        check_name: Optional[str] = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> None:
        """Deploy health checks from configuration file."""
        logger.info("Loading configuration from %s", config_file)
        config = load_config(config_file)
        validate_config(config)

        checks = config.get("healthchecks", [])
        for check_config in checks:
            name = check_config.get("name")
            if check_name and name != check_name:
                continue

            logger.info("Deploying check: %s", name)
            try:
                check = self._create_check(check_config)
                if not dry_run:
                    check.deploy(force=force)
                    self._handle_integrations(check_config, check)
            except Exception as e:
                logger.error("Failed to deploy check %s: %s", name, str(e))
                if not force:
                    raise

    def _handle_integrations(self, config: Dict[str, Any], check: BaseCheck) -> None:
        """Handle monitor and dashboard integrations."""
        if "monitors" in config:
            logger.info("Configuring monitors for %s", check.name)
            self.monitor_manager.configure(check, config["monitors"])

        if "dashboards" in config:
            logger.info("Configuring dashboards for %s", check.name)
            self.dashboard_manager.configure(check, config["dashboards"])

    def validate(
        self,
        config_file: str,
        check_name: Optional[str] = None,
        schema_only: bool = False,
        strict: bool = False,
    ) -> None:
        """Validate configuration file."""
        logger.info("Validating configuration from %s", config_file)
        config = load_config(config_file)
        validate_config(config, strict=strict)

        if schema_only:
            return

        checks = config.get("healthchecks", [])
        for check_config in checks:
            name = check_config.get("name")
            if check_name and name != check_name:
                continue

            logger.info("Validating check: %s", name)
            try:
                check = self._create_check(check_config)
                check.validate()
            except Exception as e:
                logger.error("Validation failed for check %s: %s", name, str(e))
                raise

    def status(
        self,
        check_name: Optional[str] = None,
        verbose: bool = False,
        watch: bool = False,
    ) -> None:
        """Check health check status."""
        while True:
            try:
                if check_name:
                    self._check_status(check_name, verbose)
                else:
                    self._check_all_status(verbose)

                if not watch:
                    break

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Status check failed: %s", str(e))
                if not watch:
                    raise

    def _check_status(self, check_name: str, verbose: bool) -> None:
        """Check status of a specific health check."""
        try:
            response = api.Synthetics.get_test(check_name)
            status = response.get("status", "UNKNOWN")
            logger.info("Check %s status: %s", check_name, status)

            if verbose and "last_result" in response:
                self._print_verbose_status(response["last_result"])

        except Exception as e:
            logger.error("Failed to get status for check %s: %s", check_name, str(e))
            raise

    def _check_all_status(self, verbose: bool) -> None:
        """Check status of all health checks."""
        try:
            response = api.Synthetics.get_all_tests()
            tests = response.get("tests", [])

            for test in tests:
                name = test.get("name", "UNKNOWN")
                status = test.get("status", "UNKNOWN")
                logger.info("Check %s status: %s", name, status)

                if verbose and "last_result" in test:
                    self._print_verbose_status(test["last_result"])

        except Exception as e:
            logger.error("Failed to get status for checks: %s", str(e))
            raise

    def _print_verbose_status(self, result: Dict[str, Any]) -> None:
        """Print verbose status information."""
        logger.info("Last check time: %s", result.get("check_time"))
        logger.info("Response time: %s ms", result.get("response_time"))
        logger.info("Result: %s", result.get("result"))

        if "error" in result:
            logger.error("Error: %s", result["error"])

    def list_checks(
        self,
        tag: Optional[str] = None,
        check_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List health checks with optional filtering."""
        try:
            response = api.Synthetics.get_all_tests()
            tests = response.get("tests", [])

            filtered_tests = []
            for test in tests:
                if tag and tag not in test.get("tags", []):
                    continue
                if check_type and test.get("type") != check_type:
                    continue
                filtered_tests.append(test)

            return filtered_tests

        except Exception as e:
            logger.error("Failed to list checks: %s", str(e))
            raise

    def delete(
        self,
        check_name: str,
        force: bool = False,
        keep_monitors: bool = False,
    ) -> None:
        """Delete a health check."""
        try:
            logger.info("Deleting check: %s", check_name)
            api.Synthetics.delete_test(check_name)

            if not keep_monitors:
                logger.info("Deleting associated monitors for %s", check_name)
                self.monitor_manager.delete_monitors(check_name)

        except Exception as e:
            logger.error("Failed to delete check %s: %s", check_name, str(e))
            if not force:
                raise
