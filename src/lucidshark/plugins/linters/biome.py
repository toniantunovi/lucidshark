"""Biome linter plugin.

Biome is a fast linter and formatter for JavaScript, TypeScript, and more.
https://biomejs.dev/
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lucidshark.core.logging import get_logger
from lucidshark.core.models import (
    ScanContext,
    Severity,
    ToolDomain,
    UnifiedIssue,
)
from lucidshark.plugins.linters.base import FixResult, LinterPlugin
from lucidshark.plugins.utils import ensure_node_binary, get_cli_version

LOGGER = get_logger(__name__)

# Biome severity mapping
SEVERITY_MAP = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "info": Severity.LOW,
}


def _location_position(
    location: Dict[str, Any],
) -> Tuple[int, int, int, Optional[int]]:
    """Return (line_start, column_start, line_end, column_end), 1-based.

    Biome 2 reports ``start``/``end`` objects with ``line`` and ``column``.
    Biome 1 reports a byte ``span`` into ``sourceCode``. Flat ``lineStart``
    style keys are accepted as a fallback.
    """
    start = location.get("start")
    if isinstance(start, dict) and "line" in start:
        end_field = location.get("end")
        end: Dict[str, Any] = end_field if isinstance(end_field, dict) else {}
        line_start = int(start["line"])
        column_start = int(start.get("column", 1))
        return (
            line_start,
            column_start,
            int(end.get("line", line_start)),
            end.get("column"),
        )

    span = location.get("span")
    source = location.get("sourceCode")
    if isinstance(span, list) and len(span) == 2 and isinstance(source, str):
        encoded = source.encode("utf-8")

        def to_line_col(offset: int) -> Tuple[int, int]:
            before = encoded[: max(offset, 0)].decode("utf-8", errors="ignore")
            line = before.count("\n") + 1
            column = len(before) - (before.rfind("\n") + 1) + 1
            return line, column

        line_start, column_start = to_line_col(int(span[0]))
        line_end, column_end = to_line_col(int(span[1]))
        return line_start, column_start, line_end, column_end

    line_start = location.get("lineStart", 1)
    return (
        line_start,
        location.get("columnStart", 1),
        location.get("lineEnd", line_start),
        location.get("columnEnd"),
    )


def _rule_documentation_url(category: str) -> Optional[str]:
    """Return the docs page for a lint rule, or None for other diagnostics.

    ``lint/suspicious/noDoubleEquals`` is documented at
    ``https://biomejs.dev/linter/rules/no-double-equals``. Parse errors,
    format diagnostics and the like have no rule page.
    """
    parts = category.split("/")
    if len(parts) < 3 or parts[0] != "lint" or not parts[-1]:
        return None
    slug = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "-", parts[-1]
    ).lower()
    return f"https://biomejs.dev/linter/rules/{slug}"


class BiomeLinter(LinterPlugin):
    """Biome linter plugin for JavaScript/TypeScript code analysis."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize BiomeLinter.

        Args:
            project_root: Optional project root for finding Biome installation.
        """
        self._project_root = project_root

    @property
    def name(self) -> str:
        """Plugin identifier."""
        return "biome"

    @property
    def languages(self) -> List[str]:
        """Supported languages."""
        return ["javascript", "typescript", "json"]

    @property
    def supports_fix(self) -> bool:
        """Biome supports auto-fix."""
        return True

    def get_version(self) -> str:
        """Get Biome version."""
        try:
            binary = self.ensure_binary()
            return get_cli_version(binary)
        except FileNotFoundError:
            return "unknown"

    def _resolve_target_paths(self, context: ScanContext) -> List[str]:
        """Resolve target paths for linting/checking.

        Args:
            context: Scan context with paths and configuration.

        Returns:
            List of path strings to check.
        """
        if context.paths:
            return [p.as_posix() for p in context.paths]

        src_dir = context.project_root / "src"
        if src_dir.exists():
            return [src_dir.as_posix()]

        return ["."]

    def ensure_binary(self) -> Path:
        """Ensure Biome binary is available.

        Checks for Biome in project node_modules or system PATH.

        Returns:
            Path to Biome binary.

        Raises:
            FileNotFoundError: If Biome is not installed.
        """
        return ensure_node_binary(
            self._project_root,
            "biome",
            "Biome is not installed. Install it with:\n"
            "  npm install @biomejs/biome --save-dev\n"
            "  OR\n"
            "  npm install -g @biomejs/biome",
        )

    def lint(self, context: ScanContext) -> List[UnifiedIssue]:
        """Run Biome linting.

        Args:
            context: Scan context with paths and configuration.

        Returns:
            List of linting issues.
        """
        binary = self._ensure_binary_safe()
        if binary is None:
            return []

        cmd = [
            str(binary),
            "lint",
            "--reporter",
            "json",
        ]
        cmd.extend(self._resolve_target_paths(context))

        LOGGER.debug(f"Running: {' '.join(cmd)}")

        stdout = self._run_linter_command(cmd, context, tool_label="biome")
        if stdout is None:
            return []

        issues = self._parse_output(stdout, context.project_root)

        LOGGER.info(f"Biome found {len(issues)} issues")
        return issues

    def fix(self, context: ScanContext) -> FixResult:
        """Apply Biome auto-fixes.

        Args:
            context: Scan context with paths and configuration.

        Returns:
            FixResult with statistics.
        """
        binary = self._ensure_binary_safe()
        if binary is None:
            return FixResult()

        pre_issues = self.lint(context)

        # `--write` replaced `--apply` in Biome 1.8; Biome 2 removed `--apply`.
        cmd = [str(binary), "check", "--write"]
        cmd.extend(self._resolve_target_paths(context))

        LOGGER.debug(f"Running: {' '.join(cmd)}")

        if self._run_linter_command(cmd, context, tool_label="biome-fix") is None:
            return FixResult()

        post_issues = self.lint(context)
        return self._calculate_fix_stats(pre_issues, post_issues)

    def _parse_output(self, output: str, project_root: Path) -> List[UnifiedIssue]:
        """Parse Biome JSON output.

        Args:
            output: JSON output from Biome.
            project_root: Project root directory.

        Returns:
            List of UnifiedIssue objects.
        """
        if not output.strip():
            return []

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            LOGGER.warning("Failed to parse Biome output as JSON")
            return []

        issues = []
        diagnostics = data.get("diagnostics", [])

        for diagnostic in diagnostics:
            issue = self._diagnostic_to_issue(diagnostic, project_root)
            if issue:
                issues.append(issue)

        return issues

    def _diagnostic_to_issue(
        self,
        diagnostic: Dict[str, Any],
        project_root: Path,
    ) -> Optional[UnifiedIssue]:
        """Convert Biome diagnostic to UnifiedIssue.

        Args:
            diagnostic: Biome diagnostic dict.
            project_root: Project root directory.

        Returns:
            UnifiedIssue or None.
        """
        try:
            severity_str = diagnostic.get("severity", "error")
            message = diagnostic.get("message", "")
            # Biome 1 splits the message into parts that carry their own spacing
            if isinstance(message, list):
                message = "".join(
                    m.get("content", "") if isinstance(m, dict) else str(m)
                    for m in message
                )

            category = diagnostic.get("category", "")
            location = diagnostic.get("location") or {}

            # Biome 2 gives the path as a string, Biome 1 as {"file": ...}
            path_field = location.get("path") or ""
            if isinstance(path_field, dict):
                file_path_str = str(path_field.get("file") or "")
            else:
                file_path_str = str(path_field)

            line_start, column_start, line_end, column_end = _location_position(
                location
            )

            # Get severity
            severity = SEVERITY_MAP.get(severity_str, Severity.MEDIUM)

            # Build file path
            file_path = Path(file_path_str) if file_path_str else Path("unknown")
            if not file_path.is_absolute() and file_path_str:
                file_path = project_root / file_path

            # Generate deterministic ID
            issue_id = self._generate_issue_id(
                category, file_path_str, line_start, column_start, message
            )

            # Build title
            title = f"[{category}] {message}" if category else message

            # Biome 1 marks fixable diagnostics with a "fixable" tag
            fixable = bool(diagnostic.get("fixable")) or "fixable" in (
                diagnostic.get("tags") or []
            )

            return UnifiedIssue(
                id=issue_id,
                domain=ToolDomain.LINTING,
                source_tool="biome",
                severity=severity,
                rule_id=category or "unknown",
                title=title,
                description=message,
                documentation_url=_rule_documentation_url(category),
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                column_start=column_start,
                column_end=column_end,
                fixable=fixable,
                metadata={
                    "severity_raw": severity_str,
                },
            )
        except Exception as e:
            LOGGER.warning(f"Failed to parse Biome diagnostic: {e}")
            return None

    def _generate_issue_id(
        self,
        category: str,
        file: str,
        line: int,
        column: int,
        message: str,
    ) -> str:
        """Generate deterministic issue ID.

        Args:
            category: Rule category.
            file: File path.
            line: Line number.
            column: Column number.
            message: Error message.

        Returns:
            Unique issue ID.
        """
        content = f"{category}:{file}:{line}:{column}:{message}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:12]
        return f"biome-{category}-{hash_val}" if category else f"biome-{hash_val}"
