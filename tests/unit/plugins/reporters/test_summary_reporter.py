"""Unit tests for Summary reporter plugin."""

from __future__ import annotations

import io

import pytest

from lucidshark.core.models import (
    CoverageSummary,
    DuplicationSummary,
    ScanMetadata,
    ScanResult,
    ScanSummary,
)
from lucidshark.plugins.reporters.summary_reporter import SummaryReporter


@pytest.fixture
def reporter() -> SummaryReporter:
    return SummaryReporter()


def _make_metadata() -> ScanMetadata:
    return ScanMetadata(
        lucidshark_version="0.5.0",
        scan_started_at="2024-01-01T00:00:00",
        scan_finished_at="2024-01-01T00:00:05",
        duration_ms=5000,
        project_root="/project",
    )


# --- Properties ---


class TestSummaryReporterProperties:
    def test_name(self, reporter: SummaryReporter) -> None:
        assert reporter.name == "summary"


# --- report ---


class TestSummaryReporterReport:
    def test_report_writes_to_output(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            summary=ScanSummary(total=5),
            metadata=_make_metadata(),
        )
        output = io.StringIO()
        reporter.report(result, output)
        output.seek(0)
        content = output.read()
        assert "Total issues: 5" in content

    def test_report_ends_with_newline(self, reporter: SummaryReporter) -> None:
        result = ScanResult(metadata=_make_metadata())
        output = io.StringIO()
        reporter.report(result, output)
        output.seek(0)
        content = output.read()
        assert content.endswith("\n")


# --- _format_summary ---


class TestSummaryFormatSummary:
    def test_no_summary(self, reporter: SummaryReporter) -> None:
        result = ScanResult()
        lines = reporter._format_summary(result)
        assert any("No issues found" in line for line in lines)

    def test_total_issues(self, reporter: SummaryReporter) -> None:
        result = ScanResult(summary=ScanSummary(total=42))
        lines = reporter._format_summary(result)
        assert "Total issues: 42" in lines[0]

    def test_severity_breakdown(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            summary=ScanSummary(
                total=10,
                by_severity={
                    "critical": 2,
                    "high": 3,
                    "medium": 4,
                    "low": 1,
                },
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "By severity:" in text
        assert "CRITICAL: 2" in text
        assert "HIGH: 3" in text
        assert "MEDIUM: 4" in text
        assert "LOW: 1" in text

    def test_zero_severity_hidden(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            summary=ScanSummary(
                total=2,
                by_severity={"critical": 0, "high": 2},
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "CRITICAL" not in text
        assert "HIGH: 2" in text

    def test_scanner_breakdown(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            summary=ScanSummary(
                total=5,
                by_scanner={"sca": 3, "iac": 2},
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "By domain:" in text
        assert "SCA: 3" in text
        assert "IAC: 2" in text

    def test_metadata(self, reporter: SummaryReporter) -> None:
        result = ScanResult(metadata=_make_metadata())
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Scan duration: 5000ms" in text
        assert "Project: /project" in text

    def test_no_metadata(self, reporter: SummaryReporter) -> None:
        result = ScanResult(summary=ScanSummary(total=0))
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Scan duration" not in text

    def test_coverage_summary_passed(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            coverage_summary=CoverageSummary(
                coverage_percentage=85.5,
                threshold=80.0,
                total_lines=1000,
                covered_lines=855,
                missing_lines=145,
                passed=True,
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Coverage: 85.5% (PASSED)" in text
        assert "Threshold: 80.0%" in text
        assert "Lines: 855/1000 covered" in text

    def test_coverage_summary_failed(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            coverage_summary=CoverageSummary(
                coverage_percentage=60.0,
                threshold=80.0,
                total_lines=1000,
                covered_lines=600,
                missing_lines=400,
                passed=False,
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Coverage: 60.0% (FAILED)" in text

    def test_duplication_summary_passed(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            duplication_summary=DuplicationSummary(
                files_analyzed=50,
                total_lines=5000,
                duplicate_blocks=3,
                duplicate_lines=45,
                duplication_percent=0.9,
                threshold=10.0,
                passed=True,
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Duplication: 0.9% (PASSED)" in text
        assert "Threshold: 10.0%" in text
        assert "Blocks: 3, Lines: 45" in text

    def test_duplication_summary_failed(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            duplication_summary=DuplicationSummary(
                files_analyzed=50,
                total_lines=5000,
                duplicate_blocks=20,
                duplicate_lines=800,
                duplication_percent=16.0,
                threshold=10.0,
                passed=False,
            )
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Duplication: 16.0% (FAILED)" in text

    def test_full_report(self, reporter: SummaryReporter) -> None:
        result = ScanResult(
            summary=ScanSummary(
                total=5,
                by_severity={"high": 3, "medium": 2},
                by_scanner={"sast": 5},
            ),
            metadata=_make_metadata(),
            coverage_summary=CoverageSummary(
                coverage_percentage=85.0,
                threshold=80.0,
                total_lines=1000,
                covered_lines=850,
                passed=True,
            ),
            duplication_summary=DuplicationSummary(
                duplication_percent=5.0,
                threshold=10.0,
                duplicate_blocks=2,
                duplicate_lines=30,
                passed=True,
            ),
        )
        lines = reporter._format_summary(result)
        text = "\n".join(lines)
        assert "Total issues: 5" in text
        assert "HIGH: 3" in text
        assert "SAST: 5" in text
        assert "Coverage: 85.0% (PASSED)" in text
        assert "Duplication: 5.0% (PASSED)" in text
        assert "Scan duration: 5000ms" in text


# --- _format_domain_status ---


class TestSummaryFormatDomainStatus:
    """Tests for _format_domain_status method."""

    def test_no_metadata_falls_back_to_by_scanner(
        self, reporter: SummaryReporter
    ) -> None:
        """When no metadata, fall back to showing domains with issues."""
        result = ScanResult(
            summary=ScanSummary(
                total=5,
                by_scanner={"sca": 3, "sast": 2},
            )
        )
        lines = reporter._format_domain_status(result)
        text = "\n".join(lines)
        assert "By domain:" in text
        assert "SCA: 3 issues" in text
        assert "SAST: 2 issues" in text

    def test_shows_all_enabled_domains(self, reporter: SummaryReporter) -> None:
        """Shows all configured domains with their status."""
        metadata = _make_metadata()
        metadata.enabled_domains = ["linting", "type_checking", "sca", "sast"]
        metadata.executed_domains = ["linting", "type_checking", "sca", "sast"]

        result = ScanResult(
            summary=ScanSummary(
                total=3,
                by_scanner={"linting": 3},
            ),
            metadata=metadata,
        )
        lines = reporter._format_domain_status(result)
        text = "\n".join(lines)

        assert "LINTING: 3 issues" in text
        assert "TYPE_CHECKING: PASS" in text
        assert "SCA: PASS" in text
        assert "SAST: PASS" in text

    def test_shows_skipped_for_not_executed(self, reporter: SummaryReporter) -> None:
        """Domains not in executed_domains show as SKIPPED."""
        metadata = _make_metadata()
        metadata.enabled_domains = ["linting", "testing", "coverage", "sca"]
        metadata.executed_domains = ["sca"]  # Only SCA executed

        result = ScanResult(
            summary=ScanSummary(total=0),
            metadata=metadata,
        )
        lines = reporter._format_domain_status(result)
        text = "\n".join(lines)

        assert "LINTING: SKIPPED" in text
        assert "TESTING: SKIPPED" in text
        assert "COVERAGE: SKIPPED" in text
        assert "SCA: PASS" in text

    def test_all_domains_skipped(self, reporter: SummaryReporter) -> None:
        """When no domains executed, all show as SKIPPED."""
        metadata = _make_metadata()
        metadata.enabled_domains = ["linting", "type_checking", "testing"]
        metadata.executed_domains = []

        result = ScanResult(
            summary=ScanSummary(total=0),
            metadata=metadata,
        )
        lines = reporter._format_domain_status(result)
        text = "\n".join(lines)

        assert "LINTING: SKIPPED" in text
        assert "TYPE_CHECKING: SKIPPED" in text
        assert "TESTING: SKIPPED" in text

    def test_mixed_pass_fail_skipped(self, reporter: SummaryReporter) -> None:
        """Test mix of pass, fail, and skipped domains."""
        metadata = _make_metadata()
        metadata.enabled_domains = [
            "linting",
            "type_checking",
            "testing",
            "sca",
            "sast",
        ]
        metadata.executed_domains = ["linting", "sca", "sast"]

        result = ScanResult(
            summary=ScanSummary(
                total=5,
                by_scanner={"linting": 3, "sast": 2},
            ),
            metadata=metadata,
        )
        lines = reporter._format_domain_status(result)
        text = "\n".join(lines)

        assert "LINTING: 3 issues" in text  # fail
        assert "TYPE_CHECKING: SKIPPED" in text
        assert "TESTING: SKIPPED" in text
        assert "SCA: PASS" in text
        assert "SAST: 2 issues" in text  # fail

    def test_empty_enabled_domains_returns_empty(
        self, reporter: SummaryReporter
    ) -> None:
        """When enabled_domains is empty and no by_scanner, return minimal output."""
        metadata = _make_metadata()
        metadata.enabled_domains = []
        metadata.executed_domains = []

        result = ScanResult(
            summary=ScanSummary(total=0),
            metadata=metadata,
        )
        lines = reporter._format_domain_status(result)
        # Should return empty since no domains configured
        assert lines == []
