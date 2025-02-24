"""SSL certificate check implementation."""

from typing import Dict, Any, List, Optional
import logging
import ssl
import socket
from datetime import datetime, timezone

from .base import BaseCheck
from ..utils.exceptions import DeployerError
from ..utils.validation import validate_ssl_certificate
from ..utils.constants import (
    THRESHOLD_SSL_DAYS_WARNING,
    THRESHOLD_SSL_DAYS_CRITICAL
)

logger = logging.getLogger(__name__)

class SSLCheck(BaseCheck):
    """SSL certificate check implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize SSL check with configuration.

        Args:
            config: Check configuration dictionary
        """
        super().__init__(config)
        self.hostname = config.get("hostname")
        self.port = config.get("port", 443)
        self.expiry_threshold = config.get("expiry_threshold", THRESHOLD_SSL_DAYS_WARNING)
        self.check_chain = config.get("check_chain", True)
        self.expected_issuer = config.get("expected_issuer")
        self.minimum_key_strength = config.get("minimum_key_strength", 2048)
        self.protocols = config.get("protocols", ["TLSv1.2", "TLSv1.3"])

    def validate(self) -> None:
        """Validate SSL check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        super().validate()

        if not self.hostname:
            raise DeployerError(f"Hostname is required for SSL check {self.name}")

        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise DeployerError(f"Invalid port {self.port} for check {self.name}")

        if not isinstance(self.expiry_threshold, int) or self.expiry_threshold < 1:
            raise DeployerError(
                f"Invalid expiry threshold {self.expiry_threshold} for check {self.name}"
            )

        if not isinstance(self.minimum_key_strength, int) or self.minimum_key_strength < 1:
            raise DeployerError(
                f"Invalid minimum key strength {self.minimum_key_strength} for check {self.name}"
            )

        for protocol in self.protocols:
            if protocol not in ["TLSv1.2", "TLSv1.3"]:
                raise DeployerError(
                    f"Invalid SSL protocol {protocol} for check {self.name}"
                )

        try:
            validate_ssl_certificate(self.hostname, self.port)
        except Exception as e:
            logger.warning(
                "SSL certificate validation failed for %s:%d: %s",
                self.hostname,
                self.port,
                str(e)
            )

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for SSL check creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = super()._build_api_payload()
        payload.update({
            "config": {
                "hostname": self.hostname,
                "port": self.port,
                "check_chain": self.check_chain,
                "protocols": self.protocols,
                "assertions": self._build_assertions(),
            }
        })
        return payload

    def _build_assertions(self) -> List[Dict[str, Any]]:
        """Build assertions list for SSL check.

        Returns:
            List of assertion configurations
        """
        assertions = [
            {
                "type": "certificate",
                "operator": "isValid",
            },
            {
                "type": "expirationDays",
                "operator": "greaterThan",
                "target": self.expiry_threshold,
            }
        ]

        if self.expected_issuer:
            assertions.append({
                "type": "issuer",
                "operator": "equals",
                "target": self.expected_issuer,
            })

        if self.minimum_key_strength:
            assertions.append({
                "type": "keyStrength",
                "operator": "greaterThan",
                "target": self.minimum_key_strength,
            })

        return assertions

    def get_certificate_info(self) -> Dict[str, Any]:
        """Get detailed certificate information.

        Returns:
            Dictionary containing certificate information

        Raises:
            DeployerError: If certificate information cannot be retrieved
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.hostname, self.port)) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert = ssock.getpeercert()

            if not cert:
                raise DeployerError(f"No certificate found for {self.hostname}:{self.port}")

            # Parse certificate information
            not_after = datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            ).replace(tzinfo=timezone.utc)

            days_remaining = (not_after - datetime.now(timezone.utc)).days

            return {
                "subject": dict(x[0] for x in cert["subject"]),
                "issuer": dict(x[0] for x in cert["issuer"]),
                "version": cert["version"],
                "serial_number": cert["serialNumber"],
                "not_before": cert["notBefore"],
                "not_after": cert["notAfter"],
                "days_remaining": days_remaining,
                "expired": days_remaining <= 0,
                "expiring_soon": days_remaining <= self.expiry_threshold,
            }

        except ssl.SSLError as e:
            raise DeployerError(f"SSL error for {self.hostname}:{self.port}: {str(e)}")
        except socket.error as e:
            raise DeployerError(f"Connection error for {self.hostname}:{self.port}: {str(e)}")
        except Exception as e:
            raise DeployerError(
                f"Failed to get certificate info for {self.hostname}:{self.port}: {str(e)}"
            )

    def validate_certificate_chain(self) -> Dict[str, Any]:
        """Validate the certificate chain.

        Returns:
            Dictionary containing chain validation results

        Raises:
            DeployerError: If chain validation fails
        """
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.hostname, self.port)) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    protocol = ssock.version()

            return {
                "valid": True,
                "protocol": protocol,
                "cipher_suite": cipher[0],
                "cipher_bits": cipher[1],
                "issuer_chain": self._get_issuer_chain(cert),
            }

        except ssl.SSLError as e:
            return {
                "valid": False,
                "error": str(e),
                "error_code": e.reason if hasattr(e, "reason") else None,
            }
        except Exception as e:
            raise DeployerError(
                f"Failed to validate certificate chain for {self.hostname}:{self.port}: {str(e)}"
            )

    def _get_issuer_chain(self, cert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract issuer chain from certificate.

        Args:
            cert: Certificate dictionary

        Returns:
            List of issuer dictionaries
        """
        chain = []
        current = cert
        seen = set()

        while current and "issuer" in current:
            issuer = dict(x[0] for x in current["issuer"])
            issuer_hash = tuple(sorted(issuer.items()))

            if issuer_hash in seen:
                break

            chain.append(issuer)
            seen.add(issuer_hash)
            current = None  # In practice, we'd need to fetch the issuer cert

        return chain

    def get_results(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        include_chain: bool = False,
    ) -> Dict[str, Any]:
        """Get SSL check results.

        Args:
            from_ts: Start timestamp for results
            to_ts: End timestamp for results
            include_chain: Whether to include chain validation results

        Returns:
            Dict containing check results

        Raises:
            DeployerError: If results retrieval fails
        """
        try:
            results = super().get_results(from_ts, to_ts)
            if include_chain:
                for result in results.get("results", []):
                    if "certificate" in result:
                        result["chain_validation"] = self.validate_certificate_chain()
            return results
        except Exception as e:
            raise DeployerError(f"Failed to get results for SSL check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the SSL check."""
        return f"SSLCheck(name={self.name}, hostname={self.hostname}, port={self.port})" 