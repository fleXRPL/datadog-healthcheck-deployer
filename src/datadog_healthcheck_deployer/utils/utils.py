"""Utility functions and helpers for the DataDog HealthCheck Deployer."""

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
import yaml

from .logging import get_logger

logger = get_logger(__name__)


def load_yaml(file_path: str) -> Dict[str, Any]:
    """Load YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary containing YAML data

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If YAML parsing fails
    """
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML file {file_path}: {str(e)}")
        raise


def dump_yaml(data: Dict[str, Any], file_path: str) -> None:
    """Dump data to YAML file.

    Args:
        data: Data to dump
        file_path: Path to output file

    Raises:
        OSError: If file cannot be written
        yaml.YAMLError: If YAML dumping fails
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
    except OSError as e:
        logger.error(f"Failed to write YAML file {file_path}: {str(e)}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Failed to dump YAML data to {file_path}: {str(e)}")
        raise


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (overrides dict1)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def substitute_variables(data: Any, variables: Dict[str, Any]) -> Any:
    """Substitute variables in data.

    Args:
        data: Data to process
        variables: Dictionary of variables

    Returns:
        Data with variables substituted
    """
    if isinstance(data, str):
        for var_name, var_value in variables.items():
            pattern = f"\\${{{var_name}}}"
            data = re.sub(pattern, str(var_value), data)
        return data
    elif isinstance(data, dict):
        return {k: substitute_variables(v, variables) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_variables(item, variables) for item in data]
    else:
        return data


def validate_url(url: str) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def calculate_hash(data: Union[str, Dict[str, Any], List[Any]]) -> str:
    """Calculate SHA-256 hash of data.

    Args:
        data: Data to hash (string, dict, or list)

    Returns:
        Hash string
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def retry_with_backoff(
    func: callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True,
) -> Any:
    """Retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        base_delay: Base delay between attempts in seconds
        max_delay: Maximum delay between attempts in seconds
        exponential: Whether to use exponential backoff

    Returns:
        Function result

    Raises:
        Exception: If all attempts fail
    """
    from .exceptions import RetryError

    last_exception = None
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt == max_attempts - 1:
                break

            delay = min(base_delay * (2**attempt if exponential else 1), max_delay)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}")
            import time

            time.sleep(delay)

    raise RetryError(str(last_exception), max_attempts)


def format_timestamp(timestamp: Optional[Union[int, float, str, datetime]] = None) -> str:
    """Format timestamp as ISO 8601 string.

    Args:
        timestamp: Timestamp to format (defaults to current time)

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        dt = datetime.now(timezone.utc)
    elif isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp, timezone.utc)
    elif isinstance(timestamp, str):
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.fromtimestamp(float(timestamp), timezone.utc)
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        raise ValueError(f"Invalid timestamp type: {type(timestamp)}")

    return dt.isoformat()


def parse_duration(duration: str) -> int:
    """Parse duration string to seconds.

    Args:
        duration: Duration string (e.g., "1h", "30m", "60s")

    Returns:
        Duration in seconds

    Raises:
        ValueError: If duration format is invalid
    """
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}

    match = re.match(r"^(\d+)([smhdw])$", duration)
    if not match:
        raise ValueError(f"Invalid duration format: {duration}")

    value, unit = match.groups()
    return int(value) * units[unit]


def make_request(method: str, url: str, **kwargs) -> requests.Response:
    """Make HTTP request with retry and logging.

    Args:
        method: HTTP method
        url: Request URL
        **kwargs: Additional arguments for requests.request()

    Returns:
        Response object

    Raises:
        requests.exceptions.RequestException: If request fails
    """

    def _make_request():
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    logger.debug(f"Making {method} request to {url}")
    try:
        return retry_with_backoff(_make_request)
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise
