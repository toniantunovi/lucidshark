"""Regression tests for the second round of review fixes."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from lucidshark.cli.commands.overview import OverviewCommand
from lucidshark.cli.commands.scan import ScanCommand
from lucidshark.cli.runner import auto_update_enabled
from lucidshark.config import LucidSharkConfig
from lucidshark.config.loader import _parse_overview_config
from lucidshark.config.models import (
    DEFAULT_OVERVIEW_DOMAINS,
    CoveragePipelineConfig,
    DuplicationPipelineConfig,
    FailOnConfig,
    OverviewConfig,
    PipelineConfig,
)
from lucidshark.config.validation import validate_config
from lucidshark.core.domain_runner import PLUGIN_LANGUAGES
from lucidshark.core.models import (
    CoverageSummary,
    DuplicationSummary,
    ScanResult,
    Severity,
    ToolDomain,
    UnifiedIssue,
)
from lucidshark.core.tool_validation import AUTO_DOWNLOADABLE_TOOLS
from lucidshark.detection.languages import detect_languages
from lucidshark.mcp.formatter import InstructionFormatter
from lucidshark.mcp.tools import MCPToolExecutor
from lucidshark.overview.generator import OverviewConfig as GeneratorOverviewConfig
from lucidshark.plugins import discovery
from lucidshark.plugins.linters.biome import _rule_documentation_url
from lucidshark.plugins.test_runners.sbt import SbtTestRunner


class TestAutoUpdateSetting:
    """The startup update step reads settings.auto_update."""

    def test_off_when_config_says_false(self, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "lucidshark.yml").write_text("settings:\n  auto_update: false\n")
        monkeypatch.chdir(tmp_path)
        assert auto_update_enabled() is False

    def test_on_without_config(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        with patch("lucidshark.cli.runner.find_project_config", return_value=None):
            assert auto_update_enabled() is True

    def test_on_when_config_is_unreadable(self, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / "lucidshark.yml").write_text("settings: [unclosed\n")
        monkeypatch.chdir(tmp_path)
        assert auto_update_enabled() is True

    def test_main_passes_the_setting_to_the_updater(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        (tmp_path / "lucidshark.yml").write_text("settings:\n  auto_update: false\n")
        monkeypatch.chdir(tmp_path)
        from lucidshark import __version__
        from lucidshark.cli import main

        with (
            patch("lucidshark.updater.maybe_apply_pending_and_reexec") as mock_apply,
            patch("lucidshark.cli.CLIRunner") as mock_runner_cls,
        ):
            mock_runner_cls.return_value.run.return_value = 0
            main([])

        mock_apply.assert_called_once_with(__version__, auto_update=False)


def _threshold_args() -> Namespace:
    return Namespace(
        base_branch=None,
        linting_threshold_scope=None,
        type_checking_threshold_scope=None,
        coverage_threshold_scope=None,
        duplication_threshold_scope=None,
    )


def _issue(domain: ToolDomain = ToolDomain.LINTING) -> UnifiedIssue:
    return UnifiedIssue(
        id="i-1",
        domain=domain,
        source_tool="tool",
        severity=Severity.HIGH,
        rule_id="rule",
        title="Title",
        description="Description",
    )


class TestFailOnKeepsPercentageRules:
    """--fail-on replaces severity rules, not coverage and duplication rules."""

    DOMAINS = ("coverage", "duplication")

    def _check(self, result: ScanResult, fail_on: FailOnConfig):
        config = LucidSharkConfig(fail_on=fail_on)
        return ScanCommand(version="1.0.0")._check_domain_thresholds(
            result, config, _threshold_args(), domains=self.DOMAINS
        )

    def test_coverage_below_threshold_still_fails(self) -> None:
        result = ScanResult(issues=[])
        result.coverage_summary = CoverageSummary(
            coverage_percentage=40.0, threshold=80.0, passed=False
        )
        reason = self._check(result, FailOnConfig(coverage="below_threshold"))
        assert reason is not None and "coverage" in reason

    def test_duplication_above_threshold_still_fails(self) -> None:
        result = ScanResult(issues=[])
        result.duplication_summary = DuplicationSummary(
            duplication_percent=30.0, threshold=10.0, passed=False
        )
        reason = self._check(result, FailOnConfig(duplication="above_threshold"))
        assert reason is not None and "duplication" in reason

    def test_duplication_percent_rule_still_fails(self) -> None:
        result = ScanResult(issues=[])
        result.duplication_summary = DuplicationSummary(duplication_percent=7.0)
        assert self._check(result, FailOnConfig(duplication="5%")) is not None

    def test_severity_rules_from_config_are_replaced(self) -> None:
        result = ScanResult(issues=[_issue()])
        assert self._check(result, FailOnConfig(linting="any")) is None

    def test_non_percentage_coverage_rule_is_replaced(self) -> None:
        result = ScanResult(issues=[_issue(ToolDomain.COVERAGE)])
        assert self._check(result, FailOnConfig(coverage="any")) is None

    def test_passing_coverage_does_not_fail(self) -> None:
        result = ScanResult(issues=[])
        result.coverage_summary = CoverageSummary(coverage_percentage=90.0)
        assert self._check(result, FailOnConfig(coverage="below_threshold")) is None


class TestMcpThresholdScope:
    """MCP reads threshold_scope from lucidshark.yml when no argument is given."""

    def _executor(self, tmp_path: Path) -> MCPToolExecutor:
        config = LucidSharkConfig(
            pipeline=PipelineConfig(
                coverage=CoveragePipelineConfig(enabled=True, threshold_scope="both"),
                duplication=DuplicationPipelineConfig(
                    enabled=True, threshold_scope="project"
                ),
            )
        )
        return MCPToolExecutor(tmp_path, config)

    def test_config_value_is_used(self, tmp_path: Path) -> None:
        executor = self._executor(tmp_path)
        assert executor._threshold_scope("coverage", None, "changed") == "both"
        assert executor._threshold_scope("duplication", None, "both") == "project"

    def test_argument_wins_over_config(self, tmp_path: Path) -> None:
        executor = self._executor(tmp_path)
        assert executor._threshold_scope("coverage", "project", "changed") == "project"

    def test_default_without_config_section(self, tmp_path: Path) -> None:
        executor = MCPToolExecutor(tmp_path, LucidSharkConfig())
        assert executor._threshold_scope("coverage", None, "changed") == "changed"
        assert executor._threshold_scope("duplication", None, "both") == "both"


class TestMcpDuplicationDefaults:
    """Without a duplication section MCP uses the same defaults as the CLI."""

    @pytest.mark.asyncio
    async def test_defaults_match_the_config_model(self, tmp_path: Path) -> None:
        executor = MCPToolExecutor(tmp_path, LucidSharkConfig())
        executor._runner = MagicMock()
        executor._runner.run_duplication.return_value = []

        await executor._run_duplication(MagicMock())

        kwargs = executor._runner.run_duplication.call_args.kwargs
        model = DuplicationPipelineConfig()
        assert kwargs["threshold"] == model.threshold == 10.0
        assert kwargs["min_lines"] == model.min_lines == 4
        assert kwargs["min_chars"] == model.min_chars


class TestJvmLanguageDetection:
    """pom.xml and build.gradle are not proof of Java."""

    def _names(self, root: Path) -> set[str]:
        return {lang.name for lang in detect_languages(root)}

    def test_kotlin_gradle_project_is_not_java(self, tmp_path: Path) -> None:
        (tmp_path / "build.gradle.kts").write_text('plugins { kotlin("jvm") }\n')
        src = tmp_path / "src" / "main" / "kotlin"
        src.mkdir(parents=True)
        (src / "App.kt").write_text("fun main() {}\n")
        assert self._names(tmp_path) == {"kotlin"}

    def test_kotlin_maven_project_is_not_java(self, tmp_path: Path) -> None:
        (tmp_path / "pom.xml").write_text("<project/>\n")
        (tmp_path / "App.kt").write_text("fun main() {}\n")
        assert self._names(tmp_path) == {"kotlin"}

    def test_java_project_with_kotlin_build_script_is_not_kotlin(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "build.gradle.kts").write_text("plugins { java }\n")
        (tmp_path / "settings.gradle.kts").write_text('rootProject.name = "x"\n')
        (tmp_path / "App.java").write_text("class App {}\n")
        assert self._names(tmp_path) == {"java"}

    def test_mixed_project_keeps_both(self, tmp_path: Path) -> None:
        (tmp_path / "build.gradle").write_text("")
        (tmp_path / "App.java").write_text("class App {}\n")
        (tmp_path / "Util.kt").write_text("fun util() {}\n")
        assert self._names(tmp_path) == {"java", "kotlin"}

    def test_build_file_alone_still_means_java(self, tmp_path: Path) -> None:
        (tmp_path / "pom.xml").write_text("<project/>\n")
        assert self._names(tmp_path) == {"java"}


class TestSbtCoverageReport:
    """sbt writes a fresh Scoverage report when the plugin is installed."""

    def _run(self, project_root: Path) -> list[str]:
        runner = SbtTestRunner(project_root=project_root)
        context = MagicMock()
        context.project_root = project_root
        with patch(
            "lucidshark.plugins.test_runners.sbt.run_with_streaming"
        ) as mock_run:
            runner._run_sbt_tests(Path("/usr/bin/sbt"), context)
        return mock_run.call_args.kwargs["cmd"]

    def test_with_scoverage_plugin(self, tmp_path: Path) -> None:
        (tmp_path / "project").mkdir()
        (tmp_path / "project" / "plugins.sbt").write_text(
            'addSbtPlugin("org.scoverage" % "sbt-scoverage" % "2.0.11")\n'
        )
        assert self._run(tmp_path)[-3:] == ["coverage", "test", "coverageReport"]

    def test_without_scoverage_plugin(self, tmp_path: Path) -> None:
        (tmp_path / "project").mkdir()
        (tmp_path / "project" / "plugins.sbt").write_text("// no plugins\n")
        cmd = self._run(tmp_path)
        assert cmd[-1] == "test"
        assert "coverage" not in cmd

    def test_without_project_dir(self, tmp_path: Path) -> None:
        assert self._run(tmp_path)[-1] == "test"


class TestValidateCoverageAndUnusedKeys:
    def _messages(self, data: dict) -> list[str]:
        return [w.message for w in validate_config(data, source="test.yml")]

    def test_coverage_section_without_enabled_is_not_treated_as_on(self) -> None:
        messages = self._messages(
            {"pipeline": {"coverage": {"threshold": 80}, "testing": {"enabled": False}}}
        )
        assert not any("Coverage requires testing" in m for m in messages)

    def test_enabled_coverage_without_testing_still_warns(self) -> None:
        messages = self._messages(
            {"pipeline": {"coverage": {"enabled": True}, "testing": {"enabled": False}}}
        )
        assert any("Coverage requires testing" in m for m in messages)

    def test_coverage_extra_args_warns(self) -> None:
        messages = self._messages(
            {
                "pipeline": {
                    "testing": {"enabled": True},
                    "coverage": {"enabled": True, "extra_args": ["-DskipITs"]},
                }
            }
        )
        assert any(
            "'pipeline.coverage.extra_args' has no effect" in m for m in messages
        )

    def test_testing_exclude_warns(self) -> None:
        messages = self._messages(
            {"pipeline": {"testing": {"enabled": True, "exclude": ["tests/slow/**"]}}}
        )
        assert any("'pipeline.testing.exclude' has no effect" in m for m in messages)

    def test_no_warning_when_keys_are_absent_or_empty(self) -> None:
        messages = self._messages(
            {
                "pipeline": {
                    "testing": {"enabled": True, "exclude": []},
                    "coverage": {"enabled": True},
                }
            }
        )
        assert not any("has no effect" in m for m in messages)


class TestBiomeRuleDocumentationUrl:
    @pytest.mark.parametrize(
        ("category", "expected"),
        [
            (
                "lint/suspicious/noDoubleEquals",
                "https://biomejs.dev/linter/rules/no-double-equals",
            ),
            (
                "lint/a11y/noSvgWithoutTitle",
                "https://biomejs.dev/linter/rules/no-svg-without-title",
            ),
            (
                "lint/nursery/useJSXKey",
                "https://biomejs.dev/linter/rules/use-jsx-key",
            ),
            ("parse", None),
            ("format", None),
            ("lint/suspicious", None),
            ("", None),
        ],
    )
    def test_url(self, category: str, expected: str | None) -> None:
        assert _rule_documentation_url(category) == expected


class TestOverviewSettings:
    def test_one_default_domain_list_everywhere(self) -> None:
        expected = list(DEFAULT_OVERVIEW_DOMAINS)
        assert OverviewConfig().domains == expected
        assert _parse_overview_config({"file": "Q.md"}).domains == expected
        assert _parse_overview_config({"domains": None}).domains == expected
        assert GeneratorOverviewConfig().domains == expected
        assert "formatting" in expected and "testing" in expected

    def test_explicit_domains_are_kept(self) -> None:
        assert _parse_overview_config({"domains": []}).domains == []
        assert _parse_overview_config({"domains": ["sca"]}).domains == ["sca"]

    def test_update_writes_nothing_when_disabled(self, tmp_path: Path, capsys) -> None:
        from lucidshark.core.models import ScanMetadata

        config = LucidSharkConfig(overview=OverviewConfig(enabled=False))
        scan_result = ScanResult(issues=[])
        scan_result.metadata = ScanMetadata(
            lucidshark_version="1.0.0",
            scan_started_at="",
            scan_finished_at="",
            duration_ms=0,
            project_root=str(tmp_path),
            all_files=True,
        )
        args = Namespace(path=str(tmp_path), preview=False, update=True, show=False)
        cmd = OverviewCommand(version="1.0.0")

        with patch.object(cmd, "_get_scan_results", return_value=scan_result):
            exit_code = cmd.execute(args, config)

        assert exit_code == 0
        assert not (tmp_path / "QUALITY.md").exists()
        assert not (tmp_path / ".lucidshark" / "quality-history.json").exists()
        assert "disabled" in capsys.readouterr().out


class TestPluginTables:
    GROUPS = (
        discovery.LINTER_ENTRY_POINT_GROUP,
        discovery.TYPE_CHECKER_ENTRY_POINT_GROUP,
        discovery.TEST_RUNNER_ENTRY_POINT_GROUP,
        discovery.COVERAGE_ENTRY_POINT_GROUP,
        discovery.DUPLICATION_ENTRY_POINT_GROUP,
        discovery.FORMATTER_ENTRY_POINT_GROUP,
    )

    def test_language_table_matches_every_plugin(self) -> None:
        """A plugin missing from the table is never filtered by language."""
        for group in self.GROUPS:
            plugins: dict[str, Any] = discovery.discover_plugins(group)
            for name, plugin_cls in plugins.items():
                assert name in PLUGIN_LANGUAGES, f"{name} missing from PLUGIN_LANGUAGES"
                assert set(PLUGIN_LANGUAGES[name]) == set(plugin_cls().languages), name

    @pytest.mark.parametrize("tool", ["gosec", "ktlint", "ktlint_format", "detekt"])
    def test_self_downloading_tools_are_listed(self, tool: str) -> None:
        assert tool in AUTO_DOWNLOADABLE_TOOLS


class TestFormatterActions:
    @pytest.mark.parametrize(
        ("domain", "action"),
        [
            (ToolDomain.FORMATTING, "FIX_FORMATTING"),
            (ToolDomain.DUPLICATION, "REDUCE_DUPLICATION"),
        ],
    )
    def test_action(self, domain: ToolDomain, action: str) -> None:
        assert InstructionFormatter()._generate_action(_issue(domain)) == action
