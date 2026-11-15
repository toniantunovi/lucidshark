"""Utilities for filtering scan results to changed files.

Provides functions for incremental scanning - filtering results to only
show issues/metrics for files that have changed since a base branch.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Set

from lucidshark.core.models import ToolDomain, UnifiedIssue

# Coverage and duplication report against a threshold through their summaries,
# which are filtered separately; their summary issues carry no file path and
# are dropped here on purpose.
_SUMMARY_DOMAINS = frozenset({ToolDomain.COVERAGE, ToolDomain.DUPLICATION})


def _always_reported(issue: UnifiedIssue) -> bool:
    """Return True for issues that changed-file filtering must not hide.

    - Test failures: the whole suite runs, so a failing test is a real
      failure even when the test file itself did not change.
    - Issues with no file path outside coverage/duplication (container image
      findings, tool failures, suite-level test errors): they cannot be
      attributed to a file, so dropping them would hide them entirely.
    """
    if issue.domain == ToolDomain.TESTING:
        return True
    return issue.file_path is None and issue.domain not in _SUMMARY_DOMAINS


def filter_issues_by_changed_files(
    issues: List[UnifiedIssue],
    changed_files: Optional[List[Path]],
    project_root: Path,
) -> List[UnifiedIssue]:
    """Filter issues to only those in changed files.

    Test failures and issues that have no file path (except coverage and
    duplication summary issues) are always kept; see ``_always_reported``.

    Args:
        issues: List of issues to filter.
        changed_files: List of changed file paths (absolute), or None.
            If None (git command failed), returns original issues unfiltered.
            If empty list (no changes), only always-reported issues remain.
        project_root: Project root for path resolution.

    Returns:
        Filtered list containing only issues in changed files.
        Returns original issues if changed_files is None.
    """
    # If changed_files is None (git failed), return original issues unfiltered
    # This is a defensive fallback - callers should handle None explicitly
    if changed_files is None:
        return issues

    # If empty list (git worked but no changes), keep only what is never filtered
    if not changed_files:
        return [issue for issue in issues if _always_reported(issue)]

    # Build set of changed file paths (both absolute and relative)
    changed_set: Set[str] = set()
    for f in changed_files:
        changed_set.add(str(f))  # Absolute path
        try:
            changed_set.add(str(f.relative_to(project_root)))  # Relative path
        except ValueError:
            pass

    filtered = []
    for issue in issues:
        if _always_reported(issue):
            filtered.append(issue)
            continue
        if issue.file_path is None:
            continue

        file_str = str(issue.file_path)
        try:
            rel_str = str(issue.file_path.relative_to(project_root))
        except ValueError:
            rel_str = file_str

        if file_str in changed_set or rel_str in changed_set:
            filtered.append(issue)

    return filtered
