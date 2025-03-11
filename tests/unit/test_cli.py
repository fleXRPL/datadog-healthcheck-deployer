"""Tests for CLI implementation."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from datadog_healthcheck_deployer.cli import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_deployer():
    """Create a mock deployer."""
    with patch("datadog_healthcheck_deployer.cli.HealthCheckDeployer") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def valid_config():
    """Create a valid configuration file content."""
    return """
version: "1.0"
healthchecks:
  - name: "test-check"
    type: "http"
    url: "https://example.com/health"
    locations:
      - "aws:us-east-1"
"""


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_cli_deploy(runner, mock_deployer, tmp_path, valid_config):
    """Test deploy command."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(valid_config)

    result = runner.invoke(cli, ["deploy", str(config_file)])
    assert result.exit_code == 0
    mock_deployer.deploy.assert_called_once_with(
        str(config_file), check_name=None, dry_run=False, force=False
    )


def test_cli_deploy_with_check(runner, mock_deployer, tmp_path, valid_config):
    """Test deploy command with specific check."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(valid_config)

    result = runner.invoke(cli, ["deploy", str(config_file), "--check", "test-check"])
    assert result.exit_code == 0
    mock_deployer.deploy.assert_called_once_with(
        str(config_file), check_name="test-check", dry_run=False, force=False
    )


def test_cli_validate(runner, mock_deployer, tmp_path, valid_config):
    """Test validate command."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(valid_config)

    result = runner.invoke(cli, ["validate", str(config_file)])
    assert result.exit_code == 0
    mock_deployer.validate.assert_called_once_with(
        str(config_file), check_name=None, schema_only=False, strict=False
    )


def test_cli_status(runner, mock_deployer):
    """Test status command."""
    result = runner.invoke(cli, ["status", "test-check"])
    assert result.exit_code == 0
    mock_deployer.status.assert_called_once_with(
        check_name="test-check", verbose=False, watch=False
    )


def test_cli_list(runner, mock_deployer):
    """Test list command."""
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    mock_deployer.list_checks.assert_called_once_with(tag=None, check_type=None)


def test_cli_delete(runner, mock_deployer):
    """Test delete command."""
    result = runner.invoke(cli, ["delete", "test-check"])
    assert result.exit_code == 0
    mock_deployer.delete.assert_called_once_with("test-check", force=False, keep_monitors=False)


def test_cli_invalid_config(runner, mock_deployer, tmp_path):
    """Test CLI with invalid configuration."""
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid: yaml: content")

    # Mock the deployer to raise an exception
    mock_deployer.deploy.side_effect = Exception("Failed to load configuration")

    result = runner.invoke(cli, ["deploy", str(config_file)])
    assert result.exit_code == 1
    assert "Failed to load configuration" in result.output


def test_cli_missing_config(runner):
    """Test CLI with missing configuration file."""
    result = runner.invoke(cli, ["deploy", "nonexistent.yaml"])
    assert result.exit_code == 2  # File not found error code


def test_cli_deploy_error(runner, mock_deployer, tmp_path, valid_config):
    """Test deploy command error handling."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(valid_config)
    mock_deployer.deploy.side_effect = Exception("Deploy failed")

    result = runner.invoke(cli, ["deploy", str(config_file)])
    assert result.exit_code == 1
    assert "Deploy failed" in result.output


def test_cli_validate_error(runner, mock_deployer, tmp_path, valid_config):
    """Test validate command error handling."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(valid_config)
    mock_deployer.validate.side_effect = Exception("Validation failed")

    result = runner.invoke(cli, ["validate", str(config_file)])
    assert result.exit_code == 1
    assert "Validation failed" in result.output


def test_cli_status_error(runner, mock_deployer):
    """Test status command error handling."""
    mock_deployer.status.side_effect = Exception("Status check failed")

    result = runner.invoke(cli, ["status", "test-check"])
    assert result.exit_code == 1
    assert "Status check failed" in result.output


def test_cli_list_error(runner, mock_deployer):
    """Test list command error handling."""
    mock_deployer.list_checks.side_effect = Exception("List operation failed")

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 1
    assert "List operation failed" in result.output


def test_cli_delete_error(runner, mock_deployer):
    """Test delete command error handling."""
    mock_deployer.delete.side_effect = Exception("Deletion failed")

    result = runner.invoke(cli, ["delete", "test-check"])
    assert result.exit_code == 1
    assert "Deletion failed" in result.output
