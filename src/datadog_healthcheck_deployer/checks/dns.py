"""DNS health check implementation."""

from typing import Dict, Any, List, Optional, Union
import logging
import dns.resolver
import dns.exception

from .base import BaseCheck
from ..utils.exceptions import DeployerError
from ..utils.validation import validate_dns_record
from ..utils.constants import TIMEOUT_DNS

logger = logging.getLogger(__name__)

class DNSCheck(BaseCheck):
    """DNS health check implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize DNS check with configuration.

        Args:
            config: Check configuration dictionary
        """
        super().__init__(config)
        self.hostname = config.get("hostname")
        self.record_type = config.get("record_type", "A")
        self.nameservers = config.get("nameservers", ["8.8.8.8", "8.8.4.4"])
        self.expected_values = config.get("expected_values", [])
        self.resolution_timeout = config.get("resolution_timeout", TIMEOUT_DNS)
        self.check_all_servers = config.get("check_all_servers", False)

    def validate(self) -> None:
        """Validate DNS check configuration.

        Raises:
            DeployerError: If configuration is invalid
        """
        super().validate()

        if not self.hostname:
            raise DeployerError(f"Hostname is required for DNS check {self.name}")

        if self.record_type not in ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "PTR", "SRV"]:
            raise DeployerError(
                f"Invalid DNS record type {self.record_type} for check {self.name}"
            )

        if not isinstance(self.nameservers, list) or not self.nameservers:
            raise DeployerError(f"Invalid nameservers configuration for check {self.name}")

        if not isinstance(self.resolution_timeout, (int, float)) or self.resolution_timeout < 1:
            raise DeployerError(
                f"Invalid resolution timeout {self.resolution_timeout} for check {self.name}"
            )

        try:
            validate_dns_record(self.hostname, self.record_type)
        except Exception as e:
            logger.warning(
                "DNS record validation failed for %s (type %s): %s",
                self.hostname,
                self.record_type,
                str(e)
            )

    def _build_api_payload(self) -> Dict[str, Any]:
        """Build API payload for DNS check creation/update.

        Returns:
            Dict containing the API payload
        """
        payload = super()._build_api_payload()
        payload.update({
            "config": {
                "hostname": self.hostname,
                "record_type": self.record_type,
                "nameservers": self.nameservers,
                "timeout": self.resolution_timeout,
                "check_all_servers": self.check_all_servers,
                "assertions": self._build_assertions(),
            }
        })
        return payload

    def _build_assertions(self) -> List[Dict[str, Any]]:
        """Build assertions list for DNS check.

        Returns:
            List of assertion configurations
        """
        assertions = [
            {
                "type": "recordPresent",
                "operator": "exists",
            },
            {
                "type": "resolutionTime",
                "operator": "lessThan",
                "target": self.resolution_timeout * 1000,  # Convert to milliseconds
            }
        ]

        if self.expected_values:
            assertions.append({
                "type": "recordValue",
                "operator": "contains",
                "target": self.expected_values,
            })

        return assertions

    def resolve_record(self, nameserver: Optional[str] = None) -> Dict[str, Any]:
        """Resolve DNS record.

        Args:
            nameserver: Specific nameserver to use (optional)

        Returns:
            Dictionary containing resolution results

        Raises:
            DeployerError: If resolution fails
        """
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.resolution_timeout
            resolver.lifetime = self.resolution_timeout

            if nameserver:
                resolver.nameservers = [nameserver]
            else:
                resolver.nameservers = self.nameservers

            start_time = dns.utils.now()
            answers = resolver.resolve(self.hostname, self.record_type)
            resolution_time = (dns.utils.now() - start_time).total_seconds()

            return {
                "status": "success",
                "answers": self._format_answers(answers),
                "resolution_time": resolution_time,
                "nameserver": nameserver or resolver.nameservers[0],
            }

        except dns.resolver.NXDOMAIN:
            return {
                "status": "error",
                "error": "Domain does not exist",
                "error_type": "NXDOMAIN",
            }
        except dns.resolver.NoAnswer:
            return {
                "status": "error",
                "error": "No answer received",
                "error_type": "NOANSWER",
            }
        except dns.resolver.Timeout:
            return {
                "status": "error",
                "error": "Resolution timeout",
                "error_type": "TIMEOUT",
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _format_answers(self, answers: dns.resolver.Answer) -> List[Dict[str, Any]]:
        """Format DNS answers.

        Args:
            answers: DNS resolver answers

        Returns:
            List of formatted answer dictionaries
        """
        formatted = []
        for answer in answers:
            if self.record_type == "A":
                formatted.append({"address": str(answer)})
            elif self.record_type == "AAAA":
                formatted.append({"address": str(answer)})
            elif self.record_type == "CNAME":
                formatted.append({"target": str(answer.target)})
            elif self.record_type == "MX":
                formatted.append({
                    "preference": answer.preference,
                    "exchange": str(answer.exchange),
                })
            elif self.record_type == "TXT":
                formatted.append({"text": str(answer)})
            elif self.record_type == "NS":
                formatted.append({"nameserver": str(answer)})
            elif self.record_type == "PTR":
                formatted.append({"target": str(answer)})
            elif self.record_type == "SRV":
                formatted.append({
                    "priority": answer.priority,
                    "weight": answer.weight,
                    "port": answer.port,
                    "target": str(answer.target),
                })
            else:
                formatted.append({"value": str(answer)})

        return formatted

    def validate_records(self) -> Dict[str, Any]:
        """Validate DNS records against expected values.

        Returns:
            Dictionary containing validation results
        """
        results = {
            "valid": True,
            "servers": [],
            "errors": [],
        }

        for nameserver in self.nameservers:
            resolution = self.resolve_record(nameserver)
            if resolution["status"] == "success":
                server_result = {
                    "nameserver": nameserver,
                    "resolution_time": resolution["resolution_time"],
                    "answers": resolution["answers"],
                }

                if self.expected_values:
                    actual_values = self._extract_values(resolution["answers"])
                    server_result["matches_expected"] = all(
                        expected in actual_values for expected in self.expected_values
                    )
                    if not server_result["matches_expected"]:
                        results["valid"] = False

                results["servers"].append(server_result)
            else:
                results["valid"] = False
                results["errors"].append({
                    "nameserver": nameserver,
                    "error": resolution["error"],
                    "error_type": resolution["error_type"],
                })

        return results

    def _extract_values(self, answers: List[Dict[str, Any]]) -> List[str]:
        """Extract values from formatted answers.

        Args:
            answers: List of formatted answers

        Returns:
            List of extracted values
        """
        values = []
        for answer in answers:
            if "address" in answer:
                values.append(answer["address"])
            elif "target" in answer:
                values.append(answer["target"])
            elif "text" in answer:
                values.append(answer["text"])
            elif "nameserver" in answer:
                values.append(answer["nameserver"])
            elif "exchange" in answer:
                values.append(f"{answer['preference']} {answer['exchange']}")
            elif "value" in answer:
                values.append(answer["value"])
        return values

    def get_results(
        self,
        from_ts: Optional[int] = None,
        to_ts: Optional[int] = None,
        include_validation: bool = False,
    ) -> Dict[str, Any]:
        """Get DNS check results.

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
                    result["validation"] = self.validate_records()
            return results
        except Exception as e:
            raise DeployerError(f"Failed to get results for DNS check {self.name}: {str(e)}")

    def __repr__(self) -> str:
        """Return string representation of the DNS check."""
        return f"DNSCheck(name={self.name}, hostname={self.hostname}, type={self.record_type})" 