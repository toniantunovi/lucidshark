"""Tests for tool validation functionality."""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from unittest.mock import patch


from lucidshark.bootstrap.validation import (
    validate_binary,
    is_binary_for_current_platform,
    remove_stale_binary_dir,
    PluginValidationResult,
    ToolStatus,
)


class TestToolStatus:
    """Tests for ToolStatus enum."""

    def test_status_values(self) -> None:
        assert ToolStatus.PRESENT.value == "present"
        assert ToolStatus.MISSING.value == "missing"
        assert ToolStatus.NOT_EXECUTABLE.value == "not_executable"


class TestPluginValidationResult:
    """Tests for PluginValidationResult dataclass."""

    def test_all_valid_when_all_present(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.PRESENT,
                "plugin_b": ToolStatus.PRESENT,
            }
        )
        assert result.all_valid() is True

    def test_all_valid_true_when_empty(self) -> None:
        result = PluginValidationResult()
        assert result.all_valid() is True

    def test_all_valid_false_when_missing(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.MISSING,
                "plugin_b": ToolStatus.PRESENT,
            }
        )
        assert result.all_valid() is False

    def test_all_valid_false_when_not_executable(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.PRESENT,
                "plugin_b": ToolStatus.NOT_EXECUTABLE,
            }
        )
        assert result.all_valid() is False

    def test_missing_plugins_returns_list(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.MISSING,
                "plugin_b": ToolStatus.PRESENT,
                "plugin_c": ToolStatus.NOT_EXECUTABLE,
            }
        )
        missing = result.missing_plugins()
        assert "plugin_a" in missing
        assert "plugin_c" in missing
        assert "plugin_b" not in missing

    def test_get_status(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.PRESENT,
            }
        )
        assert result.get_status("plugin_a") == ToolStatus.PRESENT
        assert result.get_status("unknown") == ToolStatus.MISSING

    def test_to_dict(self) -> None:
        result = PluginValidationResult(
            statuses={
                "plugin_a": ToolStatus.PRESENT,
                "plugin_b": ToolStatus.MISSING,
                "plugin_c": ToolStatus.NOT_EXECUTABLE,
            }
        )
        d = result.to_dict()
        assert d["plugin_a"] == "present"
        assert d["plugin_b"] == "missing"
        assert d["plugin_c"] == "not_executable"


class TestValidateBinary:
    """Tests for validate_binary function."""

    def test_missing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent"
        status = validate_binary(path)
        assert status == ToolStatus.MISSING

    def test_present_executable(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_text("#!/bin/bash\necho hello")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

        status = validate_binary(path)
        assert status == ToolStatus.PRESENT

    def test_present_not_executable(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_text("#!/bin/bash\necho hello")
        # Remove execute permission
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)

        status = validate_binary(path)
        assert status == ToolStatus.NOT_EXECUTABLE


class TestIsBinaryForCurrentPlatform:
    """Tests for is_binary_for_current_platform function."""

    def test_elf_binary_on_linux(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        with patch.object(sys, "platform", "linux"):
            assert is_binary_for_current_platform(path) is True

    def test_elf_binary_on_macos(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_bytes(b"\x7fELF" + b"\x00" * 100)
        with patch.object(sys, "platform", "darwin"):
            assert is_binary_for_current_platform(path) is False

    def test_macho_binary_on_macos(self, tmp_path: Path) -> None:
        # Mach-O 64-bit little-endian magic
        path = tmp_path / "tool"
        path.write_bytes(b"\xcf\xfa\xed\xfe" + b"\x00" * 100)
        with patch.object(sys, "platform", "darwin"):
            assert is_binary_for_current_platform(path) is True

    def test_macho_binary_on_linux(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_bytes(b"\xcf\xfa\xed\xfe" + b"\x00" * 100)
        with patch.object(sys, "platform", "linux"):
            assert is_binary_for_current_platform(path) is False

    def test_macho_big_endian_on_linux(self, tmp_path: Path) -> None:
        # Mach-O 64-bit big-endian magic
        path = tmp_path / "tool"
        path.write_bytes(b"\xfe\xed\xfa\xcf" + b"\x00" * 100)
        with patch.object(sys, "platform", "linux"):
            assert is_binary_for_current_platform(path) is False

    def test_script_file_always_valid(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_text("#!/bin/bash\necho hello")
        assert is_binary_for_current_platform(path) is True

    def test_nonexistent_file_returns_true(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent"
        assert is_binary_for_current_platform(path) is True

    def test_empty_file_returns_true(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_bytes(b"")
        assert is_binary_for_current_platform(path) is True

    def test_short_file_returns_true(self, tmp_path: Path) -> None:
        path = tmp_path / "tool"
        path.write_bytes(b"\x7f")
        assert is_binary_for_current_platform(path) is True


class TestRemoveStaleBinaryDir:
    """Tests for remove_stale_binary_dir function."""

    def test_removes_directory_and_recreates(self, tmp_path: Path) -> None:
        binary_dir = tmp_path / "bin" / "tool" / "1.0"
        binary_dir.mkdir(parents=True)
        (binary_dir / "tool").write_bytes(b"\xcf\xfa\xed\xfe" + b"\x00" * 100)
        (binary_dir / "LICENSE").write_text("MIT")

        remove_stale_binary_dir(binary_dir, "tool")

        assert binary_dir.exists()
        assert not (binary_dir / "tool").exists()
        assert not (binary_dir / "LICENSE").exists()

    def test_handles_nonexistent_directory(self, tmp_path: Path) -> None:
        binary_dir = tmp_path / "nonexistent"
        remove_stale_binary_dir(binary_dir, "tool")
        assert binary_dir.exists()
