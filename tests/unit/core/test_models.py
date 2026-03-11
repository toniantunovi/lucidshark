"""Tests for core models."""

from __future__ import annotations

from pathlib import Path

from lucidshark.core.models import (
    ScanContext,
    ScanDomain,
    ScanMetadata,
    ScanResult,
    Severity,
    UnifiedIssue,
)


def test_unified_issue_minimal_construction() -> None:
    issue = UnifiedIssue(
        id="test-1",
        domain=ScanDomain.SCA,
        source_tool="trivy",
        severity=Severity.HIGH,
        rule_id="CVE-2021-1234",
        title="Example issue",
        description="Example description",
    )

    assert issue.id == "test-1"
    assert issue.domain is ScanDomain.SCA
    assert issue.severity is Severity.HIGH
    assert issue.rule_id == "CVE-2021-1234"
    assert issue.metadata == {}


def test_scan_context_and_result_roundtrip() -> None:
    project_root = Path("/tmp/example")
    paths = [project_root / "src"]

    context = ScanContext(
        project_root=project_root, paths=paths, enabled_domains=[ScanDomain.SCA]
    )
    issue = UnifiedIssue(
        id="issue-1",
        domain=ScanDomain.SCA,
        source_tool="trivy",
        severity=Severity.LOW,
        rule_id="CVE-2021-5678",
        title="Low severity issue",
        description="Details",
    )

    result = ScanResult(issues=[issue])

    assert context.enabled_domains == [ScanDomain.SCA]
    assert result.issues[0].id == "issue-1"
    assert result.schema_version.startswith("1.")


class TestScanMetadata:
    """Tests for ScanMetadata dataclass."""

    def test_default_enabled_domains_is_empty(self) -> None:
        """Test that enabled_domains defaults to empty list."""
        metadata = ScanMetadata(
            lucidshark_version="0.5.0",
            scan_started_at="2024-01-01T00:00:00",
            scan_finished_at="2024-01-01T00:00:05",
            duration_ms=5000,
            project_root="/project",
        )
        assert metadata.enabled_domains == []

    def test_default_executed_domains_is_empty(self) -> None:
        """Test that executed_domains defaults to empty list."""
        metadata = ScanMetadata(
            lucidshark_version="0.5.0",
            scan_started_at="2024-01-01T00:00:00",
            scan_finished_at="2024-01-01T00:00:05",
            duration_ms=5000,
            project_root="/project",
        )
        assert metadata.executed_domains == []

    def test_enabled_domains_can_be_set(self) -> None:
        """Test that enabled_domains can be set with values."""
        metadata = ScanMetadata(
            lucidshark_version="0.5.0",
            scan_started_at="2024-01-01T00:00:00",
            scan_finished_at="2024-01-01T00:00:05",
            duration_ms=5000,
            project_root="/project",
            enabled_domains=["linting", "sca", "sast"],
        )
        assert metadata.enabled_domains == ["linting", "sca", "sast"]

    def test_executed_domains_can_be_set(self) -> None:
        """Test that executed_domains can be set with values."""
        metadata = ScanMetadata(
            lucidshark_version="0.5.0",
            scan_started_at="2024-01-01T00:00:00",
            scan_finished_at="2024-01-01T00:00:05",
            duration_ms=5000,
            project_root="/project",
            executed_domains=["sca", "sast"],
        )
        assert metadata.executed_domains == ["sca", "sast"]

    def test_enabled_and_executed_domains_can_differ(self) -> None:
        """Test that enabled_domains can be superset of executed_domains."""
        metadata = ScanMetadata(
            lucidshark_version="0.5.0",
            scan_started_at="2024-01-01T00:00:00",
            scan_finished_at="2024-01-01T00:00:05",
            duration_ms=5000,
            project_root="/project",
            enabled_domains=["linting", "testing", "coverage", "sca", "sast"],
            executed_domains=["sca", "sast"],  # Only security domains executed
        )
        assert len(metadata.enabled_domains) == 5
        assert len(metadata.executed_domains) == 2
        # Verify enabled is superset
        for domain in metadata.executed_domains:
            assert domain in metadata.enabled_domains
