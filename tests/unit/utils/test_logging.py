"""Tests for logging utilities."""

from unittest.mock import MagicMock, patch

import pytest

from datadog_healthcheck_deployer.utils.logging import (
    LoggerMixin,
    get_logger,
    log_call,
    log_exception,
    setup_logging,
)


def test_setup_logging():
    """Test logging setup."""
    mock_handler = MagicMock()
    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler", return_value=mock_handler
    ) as mock_stream_handler:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        setup_logging(level="INFO")

        mock_stream_handler.assert_called_once()
        mock_logger.addHandler.assert_called_once_with(mock_handler)
        mock_logger.setLevel.assert_called_once()


def test_setup_logging_with_file():
    """Test logging setup with file output."""
    test_log_file = "test.log"
    mock_stream_handler = MagicMock()
    mock_file_handler = MagicMock()

    with patch("logging.getLogger") as mock_get_logger, patch(
        "logging.StreamHandler", return_value=mock_stream_handler
    ), patch("logging.FileHandler", return_value=mock_file_handler), patch("os.makedirs"):

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        setup_logging(level="INFO", log_file=test_log_file)

        assert mock_logger.addHandler.call_count == 2
        mock_logger.addHandler.assert_any_call(mock_stream_handler)
        mock_logger.addHandler.assert_any_call(mock_file_handler)


def test_get_logger():
    """Test logger retrieval."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        logger = get_logger("test")
        mock_get_logger.assert_called_once_with("datadog_healthcheck_deployer.test")
        assert logger == mock_logger


def test_logger_mixin():
    """Test logger mixin functionality."""
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        class TestClass(LoggerMixin):
            pass

        test_instance = TestClass()
        assert test_instance.logger == mock_logger
        mock_get_logger.assert_called_once_with("datadog_healthcheck_deployer.testclass")


def test_log_call_decorator():
    """Test log call decorator."""
    mock_logger = MagicMock()

    @log_call(mock_logger)
    def test_function(arg1, arg2=None):
        return arg1 + str(arg2)

    result = test_function("test", arg2="value")

    assert mock_logger.log.call_count == 2  # Called for entry and exit
    assert result == "testvalue"


def test_log_exception_decorator():
    """Test log exception decorator."""
    mock_logger = MagicMock()

    @log_exception(mock_logger)
    def test_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        test_function()

    assert mock_logger.log.called
    assert "Test error" in str(mock_logger.log.call_args)
