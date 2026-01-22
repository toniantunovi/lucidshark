"""Configuration generation module.

This module provides generators for:
- lucidshark.yml configuration files
- Package manager tool installation
"""

from lucidshark.generation.config_generator import ConfigGenerator, InitChoices
from lucidshark.generation.package_installer import PackageInstaller

__all__ = [
    "ConfigGenerator",
    "InitChoices",
    "PackageInstaller",
]
