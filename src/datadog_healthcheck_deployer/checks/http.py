"""HTTP health check implementation."""

import logging
from typing import Any, Dict, List

from datadog import api

from ..utils.exceptions import DeployerError
from .base import BaseCheck

logger = logging.getLogger(__name__)


class HTTPCheck(BaseCheck):
    """HTTP health check implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize HTTP check."""
        super().__init__(config)
        self.url = config.get("url")
        self.method = config.get("method", "GET")
        self.headers = config.get("headers", {})
        self.body = config.get("body")
        self.success_criteria = config.get("success_criteria", [])

    def validate(self) -> None:
        """Validate HTTP check configuration."""
        super().validate()
        if not self.url:
            raise DeployerError(f"URL is required for HTTP check {self.name}")
        if self.method not in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]:
            raise DeployerError(f"Invalid HTTP method {self.method} for check {self.name}")

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for HTTP check."""
        payload = super()._build_api_payload()
        request = {
            "url": self.url,
            "method": self.method,
            "headers": self.headers,
        }
        if self.body:
            request["body"] = self.body

        payload["config"] = {"request": request}

        if self.success_criteria:
            payload["config"]["assertions"] = self._build_assertions()

        return payload

    def _build_assertions(self) -> List[Dict[str, Any]]:
        """Build assertions from success criteria."""
        assertions = []
        for criteria in self.success_criteria:
            if "content" in criteria:
                assertions.append(
                    {
                        "type": "body",
                        "operator": criteria["content"].get("type", "contains"),
                        "target": criteria["content"].get("target", ""),
                    }
                )
        return assertions

    def update(self) -> None:
        """Update the HTTP check."""
        try:
            payload = self._build_api_payload()
            api.Synthetics.update_test(self.name, payload)
        except Exception as e:
            raise DeployerError(f"Failed to update check {self.name}: {str(e)}")
