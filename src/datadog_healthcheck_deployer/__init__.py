"""
DataDog HealthCheck Deployer.

A tool for deploying and managing DataDog health checks using configuration as code.
"""

from typing import Tuple

__version__: str = "0.1.0"
__author__: str = "fleXRPL"
__email__: str = "info@flexrpl.com"

version_info: Tuple[int, int, int] = tuple(map(int, __version__.split(".")))
