"""Linter plugins for lucidshark.

This module provides linter integrations for the quality pipeline.
Linters are discovered via the lucidshark.linters entry point group.
"""

from lucidshark.plugins.linters.base import LinterPlugin
from lucidshark.plugins.discovery import (
    discover_plugins,
    LINTER_ENTRY_POINT_GROUP,
)


def discover_linter_plugins():
    """Discover all installed linter plugins.

    Returns:
        Dictionary mapping plugin names to plugin classes.
    """
    return discover_plugins(LINTER_ENTRY_POINT_GROUP, LinterPlugin)


__all__ = [
    "LinterPlugin",
    "discover_linter_plugins",
]
