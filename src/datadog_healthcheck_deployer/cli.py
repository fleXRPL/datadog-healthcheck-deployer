"""Command-line interface for the DataDog HealthCheck Deployer."""

from typing import Optional
import logging
import sys

import click

from . import __version__
from .core import HealthCheckDeployer
from .config import load_config, validate_config
from .utils.logging import setup_logging

logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version=__version__)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    help="Set the logging level",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress output")
@click.pass_context
def cli(
    ctx: click.Context,
    config: Optional[str],
    log_level: str,
    output_format: str,
    quiet: bool,
) -> None:
    """Deploy and manage DataDog health checks using configuration as code.

    Example usage:
        dd-healthcheck deploy config.yaml
        dd-healthcheck validate config.yaml
        dd-healthcheck status "check-name"
    """
    ctx.ensure_object(dict)
    setup_logging(log_level, quiet)
    ctx.obj["format"] = output_format
    ctx.obj["quiet"] = quiet

    if config:
        try:
            ctx.obj["config"] = load_config(config)
            validate_config(ctx.obj["config"])
        except Exception as e:
            logger.error("Failed to load configuration: %s", str(e))
            sys.exit(1)

@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--check", help="Deploy specific check")
@click.option("--dry-run", is_flag=True, help="Validate without deploying")
@click.option("--force", is_flag=True, help="Force deployment")
@click.pass_context
def deploy(
    ctx: click.Context,
    config_file: str,
    check: Optional[str],
    dry_run: bool,
    force: bool,
) -> None:
    """Deploy health checks from configuration file."""
    try:
        deployer = HealthCheckDeployer()
        deployer.deploy(config_file, check_name=check, dry_run=dry_run, force=force)
    except Exception as e:
        logger.error("Deployment failed: %s", str(e))
        sys.exit(1)

@cli.command()
@click.argument("config_file", type=click.Path(exists=True))
@click.option("--check", help="Validate specific check")
@click.option("--schema-only", is_flag=True, help="Validate schema only")
@click.option("--strict", is_flag=True, help="Enable strict validation")
@click.pass_context
def validate(
    ctx: click.Context,
    config_file: str,
    check: Optional[str],
    schema_only: bool,
    strict: bool,
) -> None:
    """Validate configuration file."""
    try:
        deployer = HealthCheckDeployer()
        deployer.validate(config_file, check_name=check, schema_only=schema_only, strict=strict)
    except Exception as e:
        logger.error("Validation failed: %s", str(e))
        sys.exit(1)

@cli.command()
@click.argument("check_name", required=False)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed status")
@click.option("--watch", is_flag=True, help="Watch status changes")
@click.pass_context
def status(
    ctx: click.Context,
    check_name: Optional[str],
    verbose: bool,
    watch: bool,
) -> None:
    """Check health check status."""
    try:
        deployer = HealthCheckDeployer()
        deployer.status(check_name=check_name, verbose=verbose, watch=watch)
    except Exception as e:
        logger.error("Status check failed: %s", str(e))
        sys.exit(1)

@cli.command()
@click.option("--tag", help="Filter by tag")
@click.option("--type", "check_type", help="Filter by type")
@click.pass_context
def list(ctx: click.Context, tag: Optional[str], check_type: Optional[str]) -> None:
    """List health checks."""
    try:
        deployer = HealthCheckDeployer()
        deployer.list_checks(tag=tag, check_type=check_type)
    except Exception as e:
        logger.error("List operation failed: %s", str(e))
        sys.exit(1)

@cli.command()
@click.argument("check_name")
@click.option("--force", is_flag=True, help="Force deletion")
@click.option("--keep-monitors", is_flag=True, help="Keep associated monitors")
@click.pass_context
def delete(ctx: click.Context, check_name: str, force: bool, keep_monitors: bool) -> None:
    """Delete health check."""
    try:
        deployer = HealthCheckDeployer()
        deployer.delete(check_name, force=force, keep_monitors=keep_monitors)
    except Exception as e:
        logger.error("Deletion failed: %s", str(e))
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    try:
        cli(obj={})
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        sys.exit(1) 