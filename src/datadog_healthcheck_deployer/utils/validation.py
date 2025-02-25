"""Validation utilities for the DataDog HealthCheck Deployer."""

import logging
import re
import socket
import ssl
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import dns.resolver

from .constants import (
    INTERVAL_MAX,
    INTERVAL_MIN,
    LOCATIONS,
    REQUIRED_TAGS,
    VALID_CHECK_TYPES,
    VALID_CRITERIA,
    VALID_HTTP_METHODS,
    VALID_MONITOR_STATES,
    VALID_MONITOR_TYPES,
    VALID_NOTIFY_TYPES,
)
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_check_type(check_type: str) -> None:
    """Validate health check type.

    Args:
        check_type: Health check type

    Raises:
        ValidationError: If check type is invalid
    """
    if check_type not in VALID_CHECK_TYPES:
        raise ValidationError(
            f"Invalid check type: {check_type}. Must be one of: {', '.join(VALID_CHECK_TYPES)}"
        )


def validate_http_method(method: str) -> None:
    """Validate HTTP method.

    Args:
        method: HTTP method

    Raises:
        ValidationError: If method is invalid
    """
    if method not in VALID_HTTP_METHODS:
        raise ValidationError(
            f"Invalid HTTP method: {method}. Must be one of: {', '.join(VALID_HTTP_METHODS)}"
        )


def validate_monitor_type(monitor_type: str) -> None:
    """Validate monitor type.

    Args:
        monitor_type: Monitor type

    Raises:
        ValidationError: If monitor type is invalid
    """
    if monitor_type not in VALID_MONITOR_TYPES:
        raise ValidationError(
            f"Invalid monitor type: {monitor_type}. Must be one of: {', '.join(VALID_MONITOR_TYPES)}"
        )


def validate_monitor_state(state: str) -> None:
    """Validate monitor state.

    Args:
        state: Monitor state

    Raises:
        ValidationError: If state is invalid
    """
    if state not in VALID_MONITOR_STATES:
        raise ValidationError(
            f"Invalid monitor state: {state}. Must be one of: {', '.join(VALID_MONITOR_STATES)}"
        )


def validate_notify_type(notify_type: str) -> None:
    """Validate notification type.

    Args:
        notify_type: Notification type

    Raises:
        ValidationError: If notification type is invalid
    """
    if notify_type not in VALID_NOTIFY_TYPES:
        raise ValidationError(
            f"Invalid notification type: {notify_type}. Must be one of: {', '.join(VALID_NOTIFY_TYPES)}"
        )


def validate_criteria(criteria: str) -> None:
    """Validate success criteria.

    Args:
        criteria: Success criteria

    Raises:
        ValidationError: If criteria is invalid
    """
    if criteria not in VALID_CRITERIA:
        raise ValidationError(
            f"Invalid success criteria: {criteria}. Must be one of: {', '.join(VALID_CRITERIA)}"
        )


def validate_location(location: str) -> None:
    """Validate location.

    Args:
        location: Location string (e.g., "aws:us-east-1")

    Raises:
        ValidationError: If location is invalid
    """
    try:
        provider, region = location.split(":")
    except ValueError:
        raise ValidationError(f"Invalid location format: {location}. Must be 'provider:region'")

    if provider not in LOCATIONS:
        raise ValidationError(
            f"Invalid provider: {provider}. Must be one of: {', '.join(LOCATIONS.keys())}"
        )

    if region not in LOCATIONS[provider]:
        raise ValidationError(
            f"Invalid region {region} for provider {provider}. Must be one of: {', '.join(LOCATIONS[provider])}"
        )


def validate_tags(tags: Dict[str, str]) -> None:
    """Validate tags.

    Args:
        tags: Dictionary of tags

    Raises:
        ValidationError: If required tags are missing or tag format is invalid
    """
    # Check required tags
    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
    if missing_tags:
        raise ValidationError(f"Missing required tags: {', '.join(missing_tags)}")

    # Validate tag format
    tag_pattern = re.compile(r"^[a-z0-9_\-\.\/]+$")
    for key, value in tags.items():
        if not tag_pattern.match(key):
            raise ValidationError(f"Invalid tag key format: {key}")
        if not tag_pattern.match(value):
            raise ValidationError(f"Invalid tag value format: {value}")


def validate_interval(interval: int) -> None:
    """Validate check interval.

    Args:
        interval: Check interval in seconds

    Raises:
        ValidationError: If interval is invalid
    """
    if not isinstance(interval, int):
        raise ValidationError(f"Invalid interval type: {type(interval)}. Must be an integer")
    if interval < INTERVAL_MIN or interval > INTERVAL_MAX:
        raise ValidationError(
            f"Invalid interval: {interval}. Must be between {INTERVAL_MIN} and {INTERVAL_MAX} seconds"
        )


def validate_url(url: str) -> None:
    """Validate URL format and accessibility.

    Args:
        url: URL to validate

    Raises:
        ValidationError: If URL is invalid or inaccessible
    """
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            raise ValidationError(f"Invalid URL format: {url}")
    except Exception as e:
        raise ValidationError(f"Failed to parse URL {url}: {str(e)}")


def validate_ssl_certificate(hostname: str, port: int = 443) -> None:
    """Validate SSL certificate.

    Args:
        hostname: Hostname to validate
        port: Port number (default: 443)

    Raises:
        ValidationError: If SSL certificate is invalid
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    raise ValidationError(f"No SSL certificate found for {hostname}:{port}")
    except Exception as e:
        raise ValidationError(f"Failed to validate SSL certificate for {hostname}:{port}: {str(e)}")


def validate_dns_record(hostname: str, record_type: str = "A") -> None:
    """Validate DNS record.

    Args:
        hostname: Hostname to validate
        record_type: DNS record type (default: A)

    Raises:
        ValidationError: If DNS record is invalid
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        resolver.query(hostname, record_type)
    except Exception as e:
        raise ValidationError(
            f"Failed to resolve DNS record for {hostname} (type {record_type}): {str(e)}"
        )


def validate_tcp_connection(host: str, port: int) -> None:
    """Validate TCP connection.

    Args:
        host: Host to connect to
        port: Port number

    Raises:
        ValidationError: If TCP connection fails
    """
    try:
        with socket.create_connection((host, port), timeout=5):
            pass
    except Exception as e:
        raise ValidationError(f"Failed to establish TCP connection to {host}:{port}: {str(e)}")


def validate_content_match(pattern: str) -> None:
    """Validate content match pattern.

    Args:
        pattern: Regular expression pattern

    Raises:
        ValidationError: If pattern is invalid
    """
    try:
        re.compile(pattern)
    except Exception as e:
        raise ValidationError(f"Invalid regular expression pattern: {str(e)}")


def validate_thresholds(
    warning: Optional[Union[int, float]], critical: Optional[Union[int, float]]
) -> None:
    """Validate warning and critical thresholds.

    Args:
        warning: Warning threshold
        critical: Critical threshold

    Raises:
        ValidationError: If thresholds are invalid
    """
    if warning is not None and critical is not None:
        if not isinstance(warning, (int, float)) or not isinstance(critical, (int, float)):
            raise ValidationError("Thresholds must be numeric values")
        if warning <= critical:
            raise ValidationError(
                f"Warning threshold ({warning}) must be greater than critical threshold ({critical})"
            )


def validate_variables(variables: Dict[str, Any]) -> None:
    """Validate variables.

    Args:
        variables: Dictionary of variables

    Raises:
        ValidationError: If variables are invalid
    """
    for key, value in variables.items():
        if not isinstance(key, str):
            raise ValidationError(f"Variable key must be a string: {key}")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", key):
            raise ValidationError(f"Invalid variable name format: {key}")
        if value is None:
            raise ValidationError(f"Variable value cannot be None: {key}")


def validate_template(template: Dict[str, Any]) -> None:
    """Validate template.

    Args:
        template: Template dictionary

    Raises:
        ValidationError: If template is invalid
    """
    required_fields = ["name", "type"]
    missing_fields = [field for field in required_fields if field not in template]
    if missing_fields:
        raise ValidationError(f"Missing required template fields: {', '.join(missing_fields)}")

    validate_check_type(template["type"])

    if "variables" in template:
        validate_variables(template["variables"])


def validate_notification_channel(channel: Dict[str, Any]) -> None:
    """Validate notification channel configuration.

    Args:
        channel: Notification channel dictionary

    Raises:
        ValidationError: If channel configuration is invalid
    """
    required_fields = ["type", "name"]
    missing_fields = [field for field in required_fields if field not in channel]
    if missing_fields:
        raise ValidationError(
            f"Missing required notification channel fields: {', '.join(missing_fields)}"
        )

    validate_notify_type(channel["type"])

    # Type-specific validation
    if channel["type"] == "webhook":
        if "url" not in channel:
            raise ValidationError("Webhook notification channel requires 'url' field")
        validate_url(channel["url"])
    elif channel["type"] == "email":
        if "addresses" not in channel:
            raise ValidationError("Email notification channel requires 'addresses' field")
        if not isinstance(channel["addresses"], list):
            raise ValidationError("Email addresses must be a list")
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        for address in channel["addresses"]:
            if not email_pattern.match(address):
                raise ValidationError(f"Invalid email address: {address}")


def validate_monitor_config(config: Dict[str, Any]) -> None:
    """Validate monitor configuration.

    Args:
        config: Monitor configuration dictionary

    Raises:
        ValidationError: If monitor configuration is invalid
    """
    required_fields = ["name", "type", "query"]
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValidationError(f"Missing required monitor fields: {', '.join(missing_fields)}")

    validate_monitor_type(config["type"])

    if "tags" in config:
        validate_tags(config["tags"])

    if "thresholds" in config:
        validate_thresholds(
            config["thresholds"].get("warning"), config["thresholds"].get("critical")
        )

    if "notify" in config:
        for channel in config["notify"]:
            validate_notification_channel(channel)
