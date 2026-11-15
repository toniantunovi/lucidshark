"""Tests for lucidshark.core.filtering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from lucidshark.core.filtering import filter_issues_by_changed_files
from lucidshark.core.models import (
    ScanDomain,
    Severity,
    ToolDomain,
    UnifiedIssue,
)


def _issue(
    issue_id: str,
    domain: ScanDomain | ToolDomain,
    file_path: Optional[Path],
) -> UnifiedIssue:
    return UnifiedIssue(
        id=issue_id,
        domain=domain,
        rule_id="rule",
        source_tool="tool",
        severity=Severity.HIGH,
        title=issue_id,
        description="",
        file_path=file_path,
    )


def _ids(issues: list[UnifiedIssue]) -> list[str]:
    return [i.id for i in issues]


class TestFilterIssuesByChangedFiles:
    def test_none_changed_files_returns_everything(self, tmp_path: Path) -> None:
        issues = [_issue("lint", ToolDomain.LINTING, tmp_path / "a.py")]
        assert filter_issues_by_changed_files(issues, None, tmp_path) == issues

    def test_keeps_issues_in_changed_files_only(self, tmp_path: Path) -> None:
        issues = [
            _issue("changed", ToolDomain.LINTING, tmp_path / "a.py"),
            _issue("relative", ToolDomain.TYPE_CHECKING, Path("a.py")),
            _issue("unchanged", ToolDomain.LINTING, tmp_path / "b.py"),
            _issue("sca-unchanged", ScanDomain.SCA, tmp_path / "poetry.lock"),
        ]
        result = filter_issues_by_changed_files(issues, [tmp_path / "a.py"], tmp_path)
        assert _ids(result) == ["changed", "relative"]

    def test_test_failures_are_never_filtered(self, tmp_path: Path) -> None:
        """The full suite runs, so a failure in an unchanged test file counts."""
        issues = [
            _issue("test-unchanged", ToolDomain.TESTING, tmp_path / "tests/test_b.py"),
            _issue("suite-error", ToolDomain.TESTING, None),
        ]
        result = filter_issues_by_changed_files(issues, [tmp_path / "a.py"], tmp_path)
        assert _ids(result) == ["test-unchanged", "suite-error"]

    def test_issues_without_file_path_are_kept(self, tmp_path: Path) -> None:
        """Container findings and similar cannot be attributed to a file."""
        issues = [
            _issue("container", ScanDomain.CONTAINER, None),
            _issue("lint-no-path", ToolDomain.LINTING, None),
        ]
        result = filter_issues_by_changed_files(issues, [tmp_path / "a.py"], tmp_path)
        assert _ids(result) == ["container", "lint-no-path"]

    def test_coverage_and_duplication_summary_issues_are_dropped(
        self, tmp_path: Path
    ) -> None:
        """Their thresholds are evaluated from the filtered summaries instead."""
        issues = [
            _issue("coverage", ToolDomain.COVERAGE, None),
            _issue("duplication", ToolDomain.DUPLICATION, None),
        ]
        result = filter_issues_by_changed_files(issues, [tmp_path / "a.py"], tmp_path)
        assert result == []

    def test_empty_changed_files_keeps_only_unfilterable_issues(
        self, tmp_path: Path
    ) -> None:
        issues = [
            _issue("lint", ToolDomain.LINTING, tmp_path / "a.py"),
            _issue("test", ToolDomain.TESTING, tmp_path / "tests/test_a.py"),
            _issue("coverage", ToolDomain.COVERAGE, None),
        ]
        assert _ids(filter_issues_by_changed_files(issues, [], tmp_path)) == ["test"]
