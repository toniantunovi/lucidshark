"""Unit tests for the QUALITY.md overview generator."""

from __future__ import annotations

from lucidshark.core.models import ScanMetadata, ScanResult
from lucidshark.overview.generator import create_snapshot_from_scan


def _scan_with_executed(executed: list[str]) -> ScanResult:
    result = ScanResult(issues=[])
    result.metadata = ScanMetadata(
        lucidshark_version="0.0.0",
        scan_started_at="",
        scan_finished_at="",
        duration_ms=0,
        project_root=".",
        executed_domains=executed,
    )
    return result


def test_duplicate_executed_domains_give_one_row_each() -> None:
    """Scans cached by older versions listed tool domains twice."""
    scan = _scan_with_executed(
        ["linting", "type_checking", "sca", "sast", "linting", "type_checking"]
    )

    snapshot = create_snapshot_from_scan(scan, commit="abc", branch="main")

    assert [d.domain for d in snapshot.domains] == [
        "linting",
        "type_checking",
        "sca",
        "sast",
    ]
