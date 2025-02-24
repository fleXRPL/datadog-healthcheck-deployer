"""Logging configuration and utilities for the DataDog HealthCheck Deployer."""

import logging
import os
import sys
from typing import Optional, Union

# Default log format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default date format
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(
    level: Union[str, int] = logging.INFO,
    format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    log_file: Optional[str] = None,
    file_level: Optional[Union[str, int]] = None,
) -> None:
    """Set up logging configuration.

    Args:
        level: Logging level for console output
        format: Log message format
        date_format: Date format for log messages
        log_file: Path to log file (optional)
        file_level: Logging level for file output (optional)
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    if isinstance(file_level, str):
        file_level = getattr(logging, file_level.upper())

    # Create logger
    logger = logging.getLogger("datadog_healthcheck_deployer")
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to allow all handlers to filter

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler if log file specified
    if log_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level or level)
        file_formatter = logging.Formatter(format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Name of the logger (will be prefixed with 'datadog_healthcheck_deployer')

    Returns:
        Logger instance
    """
    return logging.getLogger(f"datadog_healthcheck_deployer.{name}")

class LoggerMixin:
    """Mixin class to add logging capabilities to a class."""

    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for the class.

        Returns:
            Logger instance
        """
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__.lower())
        return self._logger

def log_call(logger: logging.Logger, level: int = logging.DEBUG):
    """Decorator to log function calls.

    Args:
        logger: Logger instance
        level: Logging level for the message

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.log(level, f"Calling {func.__name__}(args={args}, kwargs={kwargs})")
            result = func(*args, **kwargs)
            logger.log(level, f"{func.__name__} returned {result}")
            return result
        return wrapper
    return decorator

def log_exception(logger: logging.Logger, level: int = logging.ERROR):
    """Decorator to log exceptions.

    Args:
        logger: Logger instance
        level: Logging level for the message

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(level, f"Exception in {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator 