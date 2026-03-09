"""Tool validation for lucidshark bootstrap.

Validates that scanner plugin tools are present and executable.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from lucidshark.core.logging import get_logger

LOGGER = get_logger(__name__)

# ELF magic bytes (Linux binaries)
_ELF_MAGIC = b"\x7fELF"
# Mach-O magic bytes (macOS binaries) — both 32-bit and 64-bit, both endiannesses
_MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",
    b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe",
    b"\xcf\xfa\xed\xfe",
}


class ToolStatus(str, Enum):
    """Status of a tool binary."""

    PRESENT = "present"
    MISSING = "missing"
    NOT_EXECUTABLE = "not_executable"


@dataclass
class PluginValidationResult:
    """Result of validating scanner plugin tools.

    Stores validation status for each discovered plugin by name.
    """

    statuses: Dict[str, ToolStatus] = field(default_factory=dict)

    def all_valid(self) -> bool:
        """Check if all validated plugins are present and executable."""
        if not self.statuses:
            return True
        return all(status == ToolStatus.PRESENT for status in self.statuses.values())

    def missing_plugins(self) -> List[str]:
        """Return list of plugins that are missing or not executable."""
        return [
            name
            for name, status in self.statuses.items()
            if status != ToolStatus.PRESENT
        ]

    def get_status(self, plugin_name: str) -> ToolStatus:
        """Get status for a specific plugin."""
        return self.statuses.get(plugin_name, ToolStatus.MISSING)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {name: status.value for name, status in self.statuses.items()}


def validate_binary(path: Path) -> ToolStatus:
    """Validate a single binary file.

    Args:
        path: Path to the binary file.

    Returns:
        ToolStatus indicating whether the binary is present and executable.
    """
    if not path.exists():
        return ToolStatus.MISSING

    # Check if executable
    if not os.access(path, os.X_OK):
        return ToolStatus.NOT_EXECUTABLE

    return ToolStatus.PRESENT


def is_binary_for_current_platform(path: Path) -> bool:
    """Check if a native binary matches the current platform.

    Reads the magic bytes to determine if the binary is ELF (Linux) or
    Mach-O (macOS) and compares against the running OS. This catches stale
    binaries cached from a different platform (e.g. macOS binaries in a
    Linux devcontainer).

    Args:
        path: Path to the binary file.

    Returns:
        True if the binary format matches the current OS, or if the format
        cannot be determined (non-native binaries like scripts are allowed).
    """
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
    except OSError:
        return True  # Can't read — let the caller handle it

    if len(magic) < 4:
        return True  # Too small to be a native binary, likely a script

    current_os = sys.platform  # "linux", "darwin", etc.

    if magic == _ELF_MAGIC:
        # ELF binary — only valid on Linux
        if current_os != "linux":
            LOGGER.warning(f"Binary {path} is ELF (Linux) but running on {current_os}")
            return False
        return True

    if magic in _MACHO_MAGICS:
        # Mach-O binary — only valid on macOS
        if current_os != "darwin":
            LOGGER.warning(
                f"Binary {path} is Mach-O (macOS) but running on {current_os}"
            )
            return False
        return True

    # Unknown format (script, JAR, etc.) — assume valid
    return True


def remove_stale_binary_dir(binary_dir: Path, binary_name: str) -> None:
    """Remove a binary directory containing a wrong-platform binary.

    Args:
        binary_dir: The version-specific binary directory to clean up.
        binary_name: Name of the binary file that was invalid.
    """
    LOGGER.info(
        f"Removing stale {binary_name} binary at {binary_dir} "
        f"(wrong platform, will re-download)"
    )
    shutil.rmtree(binary_dir, ignore_errors=True)
    binary_dir.mkdir(parents=True, exist_ok=True)
