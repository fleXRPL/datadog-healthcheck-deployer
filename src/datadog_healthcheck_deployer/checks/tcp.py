"""TCP health check implementation."""

import logging
import socket
import ssl
import time
from typing import Any, Dict, List, Optional, Union

from ..utils.constants import TIMEOUT_TCP
from ..utils.exceptions import DeployerError
from ..utils.validation import validate_tcp_connection
from .base import BaseCheck

logger = logging.getLogger(__name__)


class TCPCheck(BaseCheck):
    """TCP health check implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize TCP check with configuration.

        Args:
            config: Check configuration dictionary
        """
        super().__init__(config)
        self.hostname = config.get("hostname")
        self.port = config.get("port")
        self.ssl = config.get("ssl", False)
        self.ssl_config = config.get("ssl_config", {})
        self.send_string = config.get("send_string")
        self.expect_string = config.get("expect_string")
        self.connection_timeout = config.get("connection_timeout", TIMEOUT_TCP)
        self.read_timeout = config.get("read_timeout", TIMEOUT_TCP)
        self.retry = config.get("retry", {})

    def _validate_hostname(self) -> None:
        """Validate hostname configuration.

        Raises:
            DeployerError: If hostname is invalid
        """
        if not self.hostname:
            raise DeployerError(f"Hostname is required for TCP check {self.name}")

    def _validate_port(self) -> None:
        """Validate port configuration.

        Raises:
            DeployerError: If port is invalid
        """
        if not self.port:
            raise DeployerError(f"Port is required for TCP check {self.name}")

        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise DeployerError(f"Invalid port {self.port} for check {self.name}")

    def _validate_ssl_config(self) -> None:
        """Validate SSL configuration.

        Raises:
            DeployerError: If SSL configuration is invalid
        """
        if self.ssl and not isinstance(self.ssl_config, dict):
            raise DeployerError(f"Invalid SSL configuration for check {self.name}")

    def _validate_retry_config(self) -> None:
        """Validate retry configuration.

        Raises:
            DeployerError: If retry configuration is invalid
        """
        if self.retry and not isinstance(self.retry, dict):
            raise DeployerError(f"Invalid retry configuration for check {self.name}")

    def validate(self) -> None:
        """Validate TCP check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        super().validate()
        self._validate_hostname()
        self._validate_port()
        self._validate_ssl_config()
        self._validate_retry_config()

        if not isinstance(self.connection_timeout, (int, float)) or self.connection_timeout < 1:
            raise DeployerError(
                f"Invalid connection timeout {self.connection_timeout} for check {self.name}"
            )

        if not isinstance(self.read_timeout, (int, float)) or self.read_timeout < 1:
            raise DeployerError(f"Invalid read timeout {self.read_timeout} for check {self.name}")

        if self.send_string and not isinstance(self.send_string, str):
            raise DeployerError(f"Invalid send string for check {self.name}")

        if self.expect_string and not isinstance(self.expect_string, str):
            raise DeployerError(f"Invalid expect string for check {self.name}")

        try:
            validate_tcp_connection(self.hostname, self.port)
        except Exception as e:
            logger.warning(
                "TCP connection validation failed for %s:%d: %s", self.hostname, self.port, str(e)
            )

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for TCP check creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = super()._build_api_payload()
        payload.update(
            {
                "config": {
                    "hostname": self.hostname,
                    "port": self.port,
                    "ssl": self.ssl,
                    "ssl_config": self.ssl_config,
                    "send_string": self.send_string,
                    "expect_string": self.expect_string,
                    "retry": self.retry,
                    "timeout": self.connection_timeout,
                    "assertions": self._build_assertions(),
                }
            }
        )
        return payload

    def _build_assertions(self) -> List[Dict[str, Any]]:
        """Build assertions list for TCP check.

        Returns:
            List of assertion configurations
        """
        assertions = [
            {
                "type": "connection",
                "operator": "succeeds",
            },
            {
                "type": "responseTime",
                "operator": "lessThan",
                "target": self.connection_timeout * 1000,  # Convert to milliseconds
            },
        ]

        if self.expect_string:
            assertions.append(
                {
                    "type": "response",
                    "operator": "contains",
                    "target": self.expect_string,
                }
            )

        return assertions

    def _handle_connection_error(self, error: Exception) -> Dict[str, Any]:
        """Handle connection errors.

        Args:
            error: The caught exception

        Returns:
            Dict containing error information
        """
        error_type = type(error).__name__
        error_message = str(error)

        if isinstance(error, (socket.timeout, TimeoutError)):
            return {
                "success": False,
                "error": "Connection timeout",
                "error_type": error_type,
                "error_message": error_message,
            }
        elif isinstance(error, ssl.SSLError):
            return {
                "success": False,
                "error": "SSL error",
                "error_type": error_type,
                "error_message": error_message,
            }
        else:
            return {
                "success": False,
                "error": "Connection failed",
                "error_type": error_type,
                "error_message": error_message,
            }

    def _validate_response(self, response: Optional[str]) -> Dict[str, Any]:
        """Validate the response against expected string.

        Args:
            response: The received response

        Returns:
            Dict containing validation results
        """
        if not self.expect_string:
            return {"success": True}

        if not response:
            return {
                "success": False,
                "error": "No response received",
                "expected": self.expect_string,
                "received": None,
            }

        if self.expect_string not in response:
            return {
                "success": False,
                "error": "Response did not match expected string",
                "expected": self.expect_string,
                "received": response,
            }

        return {"success": True}

    def _send_and_receive(self, sock: Union[socket.socket, ssl.SSLSocket]) -> Optional[str]:
        """Send and receive data if configured.

        Args:
            sock: Connected socket

        Returns:
            Received response or None
        """
        if self.send_string:
            sock.send(self.send_string.encode())

        if self.expect_string:
            return sock.recv(1024).decode()

        return None

    def _perform_single_connection(self) -> Dict[str, Any]:
        """Perform a single connection attempt.

        Returns:
            Dict containing connection results
        """
        sock = self._create_socket()
        try:
            sock.connect((self.hostname, self.port))
            response = self._send_and_receive(sock)
            validation_result = self._validate_response(response)

            if not validation_result["success"]:
                return validation_result

            return {
                "success": True,
                "response": response,
            }

        except Exception as e:
            return self._handle_connection_error(e)
        finally:
            sock.close()

    def _get_retry_params(self, retry: bool) -> tuple[int, int]:
        """Get retry parameters.

        Args:
            retry: Whether to retry failed connections

        Returns:
            Tuple of (retry_count, retry_interval)
        """
        if not retry:
            return 1, 0

        return self.retry.get("count", 3), self.retry.get("interval", 5)

    def check_connection(self, retry: bool = True) -> Dict[str, Any]:
        """Check TCP connection.

        Args:
            retry: Whether to retry failed connections

        Returns:
            Dict containing check results

        Raises:
            DeployerError: If connection check fails
        """
        retry_count, retry_interval = self._get_retry_params(retry)

        for attempt in range(retry_count):
            result = self._perform_single_connection()
            if result["success"] or attempt == retry_count - 1:
                return result

            logger.warning(
                "Connection attempt %d/%d failed for %s:%d, retrying in %d seconds",
                attempt + 1,
                retry_count,
                self.hostname,
                self.port,
                retry_interval,
            )
            time.sleep(retry_interval)

        return result

    def _create_socket(self) -> Union[socket.socket, ssl.SSLSocket]:
        """Create appropriate socket based on configuration.

        Returns:
            Socket instance

        Raises:
            DeployerError: If socket creation fails
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.connection_timeout)

        if self.ssl:
            context = ssl.create_default_context()
            for key, value in self.ssl_config.items():
                setattr(context, key, value)
            return context.wrap_socket(sock, server_hostname=self.hostname)

        return sock

    def validate_service(self) -> Dict[str, Any]:
        """Validate TCP service.

        Returns:
            Dict containing validation results

        Raises:
            DeployerError: If service validation fails
        """
        try:
            result = self.check_connection(retry=False)
            if not result["success"]:
                return {
                    "valid": False,
                    "error": result["error"],
                    "details": result,
                }

            return {
                "valid": True,
                "details": result,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "details": {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            }

    def get_results(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        include_validation: bool = False,
    ) -> Dict[str, Any]:
        """Get TCP check results.

        Args:
            from_ts: Start timestamp for results
            to_ts: End timestamp for results
            include_validation: Whether to include validation results

        Returns:
            Dict containing check results

        Raises:
            DeployerError: If results retrieval fails
        """
        try:
            results = super().get_results(from_ts, to_ts)
            if include_validation:
                for result in results.get("results", []):
                    if "tcp" in result:
                        result["validation"] = self.validate_service()
            return results
        except Exception as e:
            raise DeployerError(f"Failed to get results for TCP check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the TCP check."""
        return f"TCPCheck(name={self.name}, hostname={self.hostname}, port={self.port})"
