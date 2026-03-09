"""
Bootstrap module for lucidshark plugin binary management.

This module handles:
- Platform detection (OS + architecture)
- Plugin binary directory management (~/.lucidshark/bin/)
- Binary validation utilities

Each scanner plugin is responsible for downloading its own binary
using the utilities provided by this module.
"""

from lucidshark.bootstrap.platform import get_platform_info, PlatformInfo
from lucidshark.bootstrap.paths import get_lucidshark_home, LucidsharkPaths
from lucidshark.bootstrap.validation import (
    validate_binary,
    is_binary_for_current_platform,
    remove_stale_binary_dir,
    PluginValidationResult,
    ToolStatus,
)

__all__ = [
    "get_platform_info",
    "PlatformInfo",
    "get_lucidshark_home",
    "LucidsharkPaths",
    "validate_binary",
    "is_binary_for_current_platform",
    "remove_stale_binary_dir",
    "PluginValidationResult",
    "ToolStatus",
]
