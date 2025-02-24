"""TCP health check implementation."""

from typing import Dict, Any, List, Optional, Union
import logging
import socket
import time
import ssl

from .base import BaseCheck
from ..utils.exceptions import DeployerError
from ..utils.validation import validate_tcp_connection
from ..utils.constants import TIMEOUT_TCP

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
        self.send_string = config.get("send_string")
        self.expect_string = config.get("expect_string")
        self.connection_timeout = config.get("connection_timeout", TIMEOUT_TCP)
        self.read_timeout = config.get("read_timeout", TIMEOUT_TCP)
        self.retry = config.get("retry", {
            "count": 2,
            "interval": 5,
        })

    def validate(self) -> None:
        """Validate TCP check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        super().validate()

        if not self.hostname:
            raise DeployerError(f"Hostname is required for TCP check {self.name}")

        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise DeployerError(f"Invalid port {self.port} for check {self.name}")

        if not isinstance(self.connection_timeout, (int, float)) or self.connection_timeout < 1:
            raise DeployerError(
                f"Invalid connection timeout {self.connection_timeout} for check {self.name}"
            )

        if not isinstance(self.read_timeout, (int, float)) or self.read_timeout < 1:
            raise DeployerError(
                f"Invalid read timeout {self.read_timeout} for check {self.name}"
            )

        if self.send_string and not isinstance(self.send_string, str):
            raise DeployerError(f"Invalid send string for check {self.name}")

        if self.expect_string and not isinstance(self.expect_string, str):
            raise DeployerError(f"Invalid expect string for check {self.name}")

        try:
            validate_tcp_connection(self.hostname, self.port)
        except Exception as e:
            logger.warning(
                "TCP connection validation failed for %s:%d: %s",
                self.hostname,
                self.port,
                str(e)
            )

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for TCP check creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = super()._build_api_payload()
        payload.update({
            "config": {
                "hostname": self.hostname,
                "port": self.port,
                "ssl": self.ssl,
                "timeout": self.connection_timeout,
                "assertions": self._build_assertions(),
            }
        })

        if self.send_string:
            payload["config"]["send_string"] = self.send_string
        if self.expect_string:
            payload["config"]["expect_string"] = self.expect_string

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
            }
        ]

        if self.expect_string:
            assertions.append({
                "type": "response",
                "operator": "contains",
                "target": self.expect_string,
            })

        return assertions

    def check_connection(self, retry: bool = True) -> Dict[str, Any]:
        """Check TCP connection.

        Args:
            retry: Whether to retry failed connections

        Returns:
            Dictionary containing connection results

        Raises:
            DeployerError: If connection check fails
        """
        attempts = self.retry["count"] if retry else 1
        interval = self.retry["interval"]

        for attempt in range(attempts):
            try:
                start_time = time.time()
                sock = self._create_socket()
                sock.settimeout(self.connection_timeout)

                # Connect
                sock.connect((self.hostname, self.port))
                connection_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                # Send/receive data if configured
                response = None
                if self.send_string:
                    sock.send(self.send_string.encode())
                    if self.expect_string:
                        sock.settimeout(self.read_timeout)
                        response = sock.recv(4096).decode()

                sock.close()

                result = {
                    "status": "success",
                    "connection_time": connection_time,
                    "attempt": attempt + 1,
                }

                if response is not None:
                    result["response"] = response
                    result["matches_expected"] = self.expect_string in response

                return result

            except socket.timeout:
                error = "Connection timeout" if sock is None else "Read timeout"
                if attempt == attempts - 1 or not retry:
                    return {
                        "status": "error",
                        "error": error,
                        "error_type": "TIMEOUT",
                        "attempt": attempt + 1,
                    }
            except socket.error as e:
                if attempt == attempts - 1 or not retry:
                    return {
                        "status": "error",
                        "error": str(e),
                        "error_type": "SOCKET_ERROR",
                        "attempt": attempt + 1,
                    }
            except Exception as e:
                if attempt == attempts - 1 or not retry:
                    return {
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "attempt": attempt + 1,
                    }

            time.sleep(interval)

    def _create_socket(self) -> Union[socket.socket, ssl.SSLSocket]:
        """Create TCP socket with optional SSL wrapper.

        Returns:
            Socket object (plain or SSL)

        Raises:
            DeployerError: If socket creation fails
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.ssl:
                context = ssl.create_default_context()
                return context.wrap_socket(sock, server_hostname=self.hostname)
            return sock
        except Exception as e:
            raise DeployerError(f"Failed to create socket: {str(e)}")

    def validate_service(self) -> Dict[str, Any]:
        """Validate TCP service.

        Returns:
            Dictionary containing validation results
        """
        results = {
            "valid": True,
            "checks": [],
            "errors": [],
        }

        # Basic connection check
        connection = self.check_connection(retry=False)
        if connection["status"] == "success":
            results["checks"].append({
                "type": "connection",
                "connection_time": connection["connection_time"],
            })
        else:
            results["valid"] = False
            results["errors"].append({
                "type": "connection",
                "error": connection["error"],
                "error_type": connection["error_type"],
            })

        # SSL validation if enabled
        if self.ssl and results["valid"]:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((self.hostname, self.port)) as sock:
                    with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                        cipher = ssock.cipher()
                        protocol = ssock.version()

                results["checks"].append({
                    "type": "ssl",
                    "protocol": protocol,
                    "cipher_suite": cipher[0],
                    "cipher_bits": cipher[1],
                })
            except Exception as e:
                results["valid"] = False
                results["errors"].append({
                    "type": "ssl",
                    "error": str(e),
                    "error_type": type(e).__name__,
                })

        # Data exchange validation if configured
        if self.send_string and self.expect_string and results["valid"]:
            connection = self.check_connection(retry=False)
            if connection["status"] == "success" and "response" in connection:
                results["checks"].append({
                    "type": "data_exchange",
                    "matches_expected": connection["matches_expected"],
                    "response": connection["response"],
                })
                if not connection["matches_expected"]:
                    results["valid"] = False
            else:
                results["valid"] = False
                results["errors"].append({
                    "type": "data_exchange",
                    "error": connection.get("error", "Failed to receive response"),
                    "error_type": connection.get("error_type", "RESPONSE_ERROR"),
                })

        return results

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
                    result["validation"] = self.validate_service()
            return results
        except Exception as e:
            raise DeployerError(f"Failed to get results for TCP check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the TCP check."""
        return f"TCPCheck(name={self.name}, hostname={self.hostname}, port={self.port})" 