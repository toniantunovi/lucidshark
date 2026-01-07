"""Type checker plugins for lucidscan.

This module provides type checker integrations for the quality pipeline.
Type checkers are discovered via the lucidscan.type_checkers entry point group.
"""

from lucidscan.plugins.type_checkers.base import TypeCheckerPlugin, TypeCheckResult
from lucidscan.plugins.discovery import (
    discover_plugins,
    TYPE_CHECKER_ENTRY_POINT_GROUP,
)


def discover_type_checker_plugins():
    """Discover all installed type checker plugins.

    Returns:
        Dictionary mapping plugin names to plugin classes.
    """
    return discover_plugins(TYPE_CHECKER_ENTRY_POINT_GROUP, TypeCheckerPlugin)


__all__ = [
    "TypeCheckerPlugin",
    "TypeCheckResult",
    "discover_type_checker_plugins",
]
