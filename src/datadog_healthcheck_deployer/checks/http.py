"""HTTP health check implementation."""

import logging
from typing import Any, Dict, List, Optional

from ..utils.exceptions import DeployerError
from .base import BaseCheck

logger = logging.getLogger(__name__)


class HTTPCheck(BaseCheck):
    """HTTP health check implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize HTTP check with configuration.

        Args:
            config: Check configuration dictionary
        """
        super().__init__(config)
        self.url = config.get("url")
        self.method = config.get("method", "GET")
        self.headers = config.get("headers", {})
        self.body = config.get("body")
        self.follow_redirects = config.get("follow_redirects", True)
        self.verify_ssl = config.get("verify_ssl", True)
        self.success_criteria = config.get("success_criteria", [])

    def validate(self) -> None:
        """Validate HTTP check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        super().validate()

        if not self.url:
            raise DeployerError(f"URL is required for HTTP check {self.name}")

        if self.method not in ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
            raise DeployerError(f"Invalid HTTP method {self.method} for check {self.name}")

        self._validate_success_criteria()

    def _validate_success_criteria(self) -> None:
        """Validate success criteria configuration.

        Raises:
            DeployerError: If success criteria is invalid
        """
        for criterion in self.success_criteria:
            if not isinstance(criterion, dict):
                raise DeployerError(
                    f"Invalid success criterion format for check {self.name}: {criterion}"
                )

            if "status_code" in criterion:
                code = criterion["status_code"]
                if not isinstance(code, int) or code < 100 or code > 599:
                    raise DeployerError(f"Invalid status code {code} for check {self.name}")

            if "response_time" in criterion:
                time = criterion["response_time"]
                if not isinstance(time, (int, float)) or time <= 0:
                    raise DeployerError(f"Invalid response time {time} for check {self.name}")

            if "content" in criterion:
                self._validate_content_criterion(criterion["content"])

    def _validate_content_criterion(self, content: Dict[str, Any]) -> None:
        """Validate content validation criterion.

        Args:
            content: Content validation configuration

        Raises:
            DeployerError: If content validation configuration is invalid
        """
        content_type = content.get("type", "").lower()
        if content_type not in ["json", "text", "regex", "xml"]:
            raise DeployerError(
                f"Invalid content validation type {content_type} for check {self.name}"
            )

        if "path" in content and content_type == "json":
            if not content["path"].startswith("$."):
                raise DeployerError(
                    f"Invalid JSONPath expression for check {self.name}: {content['path']}"
                )

        if "operator" in content:
            operator = content["operator"]
            valid_operators = ["equals", "contains", "matches", "greater", "less"]
            if operator not in valid_operators:
                raise DeployerError(
                    f"Invalid content validation operator {operator} for check {self.name}"
                )

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for HTTP check creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = super()._build_api_payload()
        payload.update(
            {
                "config": {
                    "request": {
                        "url": self.url,
                        "method": self.method,
                        "headers": self.headers,
                        "body": self.body,
                        "timeout": self.timeout,
                        "follow_redirects": self.follow_redirects,
                        "verify_ssl": self.verify_ssl,
                    },
                    "assertions": self._build_assertions(),
                }
            }
        )
        return payload

    def _build_assertions(self) -> List[Dict[str, Any]]:
        """Build assertions list from success criteria.

        Returns:
            List of assertion configurations
        """
        assertions = []

        for criterion in self.success_criteria:
            if "status_code" in criterion:
                assertions.append(
                    {
                        "type": "statusCode",
                        "operator": "is",
                        "target": criterion["status_code"],
                    }
                )

            if "response_time" in criterion:
                assertions.append(
                    {
                        "type": "responseTime",
                        "operator": "lessThan",
                        "target": criterion["response_time"],
                    }
                )

            if "content" in criterion:
                assertions.extend(self._build_content_assertions(criterion["content"]))

        return assertions

    def _build_content_assertions(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build content validation assertions.

        Args:
            content: Content validation configuration

        Returns:
            List of content assertion configurations
        """
        assertions = []
        content_type = content.get("type", "").lower()

        if content_type == "json":
            assertions.append(
                {
                    "type": "header",
                    "property": "content-type",
                    "operator": "contains",
                    "target": "application/json",
                }
            )

            if "path" in content:
                assertions.append(
                    {
                        "type": "body",
                        "property": content["path"],
                        "operator": content.get("operator", "equals"),
                        "target": content.get("value"),
                    }
                )

        elif content_type == "text":
            assertions.append(
                {
                    "type": "body",
                    "operator": content.get("operator", "contains"),
                    "target": content.get("value"),
                }
            )

        elif content_type == "regex":
            assertions.append(
                {
                    "type": "body",
                    "operator": "matches",
                    "target": content.get("value"),
                }
            )

        return assertions

    def get_results(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        include_response: bool = False,
    ) -> Dict[str, Any]:
        """Get HTTP check results.

        Args:
            from_ts: Start timestamp for results
            to_ts: End timestamp for results
            include_response: Whether to include response bodies

        Returns:
            Dict containing check results

        Raises:
            DeployerError: If results retrieval fails
        """
        try:
            response = super().get_results(from_ts, to_ts)
            if not include_response:
                for result in response.get("results", []):
                    result.pop("response", None)
            return response
        except Exception as e:
            raise DeployerError(f"Failed to get results for HTTP check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the HTTP check."""
        return f"HTTPCheck(name={self.name}, url={self.url}, method={self.method})"
