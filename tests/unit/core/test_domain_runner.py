"""Unit tests for domain runner utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Type
from unittest.mock import patch, MagicMock


from lucidshark.config.models import LucidSharkConfig
from lucidshark.core.domain_runner import (
    DomainRunner,
    EXTENSION_LANGUAGE,
    PLUGIN_LANGUAGES,
    check_severity_threshold,
    detect_language,
    filter_plugins_by_language,
    get_domains_for_language,
)
from lucidshark.core.models import Severity, ToolDomain, UnifiedIssue


class MockPlugin:
    """Mock plugin for testing."""

    pass


class MockPythonPlugin:
    """Mock Python plugin."""

    pass


class MockJsPlugin:
    """Mock JavaScript plugin."""

    pass


class TestFilterPluginsByLanguage:
    """Tests for filter_plugins_by_language function."""

    def test_returns_all_plugins_when_no_languages(self) -> None:
        """Test all plugins returned when no languages specified."""
        plugins: Dict[str, Type[Any]] = {
            "ruff": MockPythonPlugin,
            "eslint": MockJsPlugin,
        }

        result = filter_plugins_by_language(plugins, [])

        assert result == plugins

    def test_filters_plugins_by_language(self) -> None:
        """Test plugins are filtered by supported language."""
        plugins: Dict[str, Type[Any]] = {
            "ruff": MockPythonPlugin,
            "eslint": MockJsPlugin,
        }

        result = filter_plugins_by_language(plugins, ["python"])

        assert "ruff" in result
        assert "eslint" not in result

    def test_includes_plugin_for_any_matching_language(self) -> None:
        """Test plugin included if any language matches."""
        plugins: Dict[str, Type[Any]] = {
            "eslint": MockJsPlugin,
        }

        # eslint supports both javascript and typescript
        result = filter_plugins_by_language(plugins, ["typescript"])

        assert "eslint" in result

    def test_case_insensitive_language_matching(self) -> None:
        """Test language matching is case insensitive."""
        plugins: Dict[str, Type[Any]] = {
            "ruff": MockPythonPlugin,
        }

        result = filter_plugins_by_language(plugins, ["Python"])

        assert "ruff" in result

    def test_includes_plugins_without_language_restrictions(self) -> None:
        """Test plugins with no language restrictions are included."""
        plugins: Dict[str, Type[Any]] = {
            "unknown_plugin": MockPlugin,
        }

        # Unknown plugins not in PLUGIN_LANGUAGES are included
        result = filter_plugins_by_language(plugins, ["python"])

        assert "unknown_plugin" in result

    def test_multiple_languages_filter(self) -> None:
        """Test filtering with multiple languages."""
        plugins: Dict[str, Type[Any]] = {
            "ruff": MockPythonPlugin,
            "mypy": MockPythonPlugin,
            "eslint": MockJsPlugin,
            "typescript": MockJsPlugin,
        }

        result = filter_plugins_by_language(plugins, ["python", "typescript"])

        assert "ruff" in result
        assert "mypy" in result
        assert "eslint" in result
        assert "typescript" in result


class TestDetectLanguage:
    """Tests for detect_language function."""

    def test_detects_python(self) -> None:
        """Test Python detection from .py extension."""
        assert detect_language(Path("test.py")) == "python"

    def test_detects_python_stub(self) -> None:
        """Test Python stub detection from .pyi extension."""
        assert detect_language(Path("types.pyi")) == "python"

    def test_detects_javascript(self) -> None:
        """Test JavaScript detection from .js extension."""
        assert detect_language(Path("index.js")) == "javascript"

    def test_detects_jsx(self) -> None:
        """Test JSX detection as javascript."""
        assert detect_language(Path("component.jsx")) == "javascript"

    def test_detects_typescript(self) -> None:
        """Test TypeScript detection from .ts extension."""
        assert detect_language(Path("app.ts")) == "typescript"

    def test_detects_tsx(self) -> None:
        """Test TSX detection as typescript."""
        assert detect_language(Path("component.tsx")) == "typescript"

    def test_detects_java(self) -> None:
        """Test Java detection from .java extension."""
        assert detect_language(Path("Main.java")) == "java"

    def test_detects_go(self) -> None:
        """Test Go detection from .go extension."""
        assert detect_language(Path("main.go")) == "go"

    def test_detects_rust(self) -> None:
        """Test Rust detection from .rs extension."""
        assert detect_language(Path("lib.rs")) == "rust"

    def test_detects_terraform(self) -> None:
        """Test Terraform detection from .tf extension."""
        assert detect_language(Path("main.tf")) == "terraform"

    def test_detects_yaml(self) -> None:
        """Test YAML detection from .yaml and .yml extensions."""
        assert detect_language(Path("config.yaml")) == "yaml"
        assert detect_language(Path("config.yml")) == "yaml"

    def test_detects_json(self) -> None:
        """Test JSON detection from .json extension."""
        assert detect_language(Path("package.json")) == "json"

    def test_returns_unknown_for_unrecognized(self) -> None:
        """Test unknown returned for unrecognized extensions."""
        assert detect_language(Path("readme.md")) == "unknown"
        assert detect_language(Path("Makefile")) == "unknown"
        assert detect_language(Path("script.sh")) == "unknown"

    def test_case_insensitive_extension(self) -> None:
        """Test extension matching is case insensitive."""
        assert detect_language(Path("Test.PY")) == "python"
        assert detect_language(Path("App.TS")) == "typescript"


class TestGetDomainsForLanguage:
    """Tests for get_domains_for_language function."""

    def test_python_domains(self) -> None:
        """Test Python gets all standard domains."""
        domains = get_domains_for_language("python")

        assert "linting" in domains
        assert "type_checking" in domains
        assert "testing" in domains
        assert "coverage" in domains
        assert "sast" in domains
        assert "sca" in domains

    def test_javascript_domains(self) -> None:
        """Test JavaScript gets all standard domains."""
        domains = get_domains_for_language("javascript")

        assert "linting" in domains
        assert "type_checking" in domains
        assert "testing" in domains
        assert "coverage" in domains

    def test_typescript_domains(self) -> None:
        """Test TypeScript gets all standard domains."""
        domains = get_domains_for_language("typescript")

        assert "linting" in domains
        assert "type_checking" in domains
        assert "testing" in domains
        assert "coverage" in domains

    def test_java_domains(self) -> None:
        """Test Java gets all standard domains."""
        domains = get_domains_for_language("java")

        assert "linting" in domains
        assert "type_checking" in domains
        assert "testing" in domains
        assert "coverage" in domains

    def test_kotlin_domains(self) -> None:
        """Test Kotlin gets all standard domains."""
        domains = get_domains_for_language("kotlin")

        assert "linting" in domains
        assert "type_checking" in domains
        assert "testing" in domains
        assert "coverage" in domains

    def test_terraform_domains(self) -> None:
        """Test Terraform gets IAC domain only."""
        domains = get_domains_for_language("terraform")

        assert domains == ["iac"]

    def test_yaml_domains(self) -> None:
        """Test YAML gets IAC and SAST domains."""
        domains = get_domains_for_language("yaml")

        assert "iac" in domains
        assert "sast" in domains

    def test_json_domains(self) -> None:
        """Test JSON gets IAC and SAST domains."""
        domains = get_domains_for_language("json")

        assert "iac" in domains
        assert "sast" in domains

    def test_unknown_language_domains(self) -> None:
        """Test unknown language gets default domains."""
        domains = get_domains_for_language("unknown")

        assert "linting" in domains
        assert "sast" in domains
        assert "sca" in domains


class TestCheckSeverityThreshold:
    """Tests for check_severity_threshold function."""

    def _create_issue(self, severity: Severity) -> UnifiedIssue:
        """Helper to create a test issue."""
        return UnifiedIssue(
            id="test-001",
            domain=ToolDomain.LINTING,
            source_tool="test",
            severity=severity,
            rule_id="test-rule",
            title="Test issue",
            description="Test description",
        )

    def test_returns_false_when_no_threshold(self) -> None:
        """Test returns False when no threshold specified."""
        issues = [self._create_issue(Severity.CRITICAL)]

        assert check_severity_threshold(issues, None) is False

    def test_returns_false_when_no_issues(self) -> None:
        """Test returns False when no issues."""
        assert check_severity_threshold([], "high") is False

    def test_returns_true_when_critical_meets_critical_threshold(self) -> None:
        """Test critical issue meets critical threshold."""
        issues = [self._create_issue(Severity.CRITICAL)]

        assert check_severity_threshold(issues, "critical") is True

    def test_returns_true_when_critical_exceeds_high_threshold(self) -> None:
        """Test critical issue exceeds high threshold."""
        issues = [self._create_issue(Severity.CRITICAL)]

        assert check_severity_threshold(issues, "high") is True

    def test_returns_false_when_low_below_high_threshold(self) -> None:
        """Test low issue doesn't meet high threshold."""
        issues = [self._create_issue(Severity.LOW)]

        assert check_severity_threshold(issues, "high") is False

    def test_returns_true_when_medium_meets_medium_threshold(self) -> None:
        """Test medium issue meets medium threshold."""
        issues = [self._create_issue(Severity.MEDIUM)]

        assert check_severity_threshold(issues, "medium") is True

    def test_returns_true_when_any_issue_meets_threshold(self) -> None:
        """Test returns True if any issue meets threshold."""
        issues = [
            self._create_issue(Severity.LOW),
            self._create_issue(Severity.MEDIUM),
            self._create_issue(Severity.HIGH),
        ]

        assert check_severity_threshold(issues, "high") is True

    def test_case_insensitive_threshold(self) -> None:
        """Test threshold comparison is case insensitive."""
        issues = [self._create_issue(Severity.HIGH)]

        assert check_severity_threshold(issues, "HIGH") is True
        assert check_severity_threshold(issues, "High") is True

    def test_unknown_threshold_matches_all_issues(self) -> None:
        """Test unknown threshold matches all issues (level 99 is very permissive)."""
        issues = [self._create_issue(Severity.LOW)]

        # Unknown threshold gets level 99, all issue severities (0-3) will be <= 99
        assert check_severity_threshold(issues, "unknown_level") is True


class TestPluginLanguagesMapping:
    """Tests for PLUGIN_LANGUAGES constant."""

    def test_ruff_supports_python(self) -> None:
        """Test ruff is mapped to Python."""
        assert "python" in PLUGIN_LANGUAGES["ruff"]

    def test_eslint_supports_js_and_ts(self) -> None:
        """Test eslint supports JavaScript and TypeScript."""
        assert "javascript" in PLUGIN_LANGUAGES["eslint"]
        assert "typescript" in PLUGIN_LANGUAGES["eslint"]

    def test_mypy_supports_python(self) -> None:
        """Test mypy is mapped to Python."""
        assert "python" in PLUGIN_LANGUAGES["mypy"]

    def test_pytest_supports_python(self) -> None:
        """Test pytest is mapped to Python."""
        assert "python" in PLUGIN_LANGUAGES["pytest"]

    def test_duplo_supports_multiple_languages(self) -> None:
        """Test duplo supports many languages."""
        duplo_langs = PLUGIN_LANGUAGES["duplo"]
        assert "python" in duplo_langs
        assert "java" in duplo_langs
        assert "javascript" in duplo_langs
        assert "go" in duplo_langs


class TestExtensionLanguageMapping:
    """Tests for EXTENSION_LANGUAGE constant."""

    def test_python_extensions(self) -> None:
        """Test Python extensions are mapped correctly."""
        assert EXTENSION_LANGUAGE[".py"] == "python"
        assert EXTENSION_LANGUAGE[".pyi"] == "python"

    def test_javascript_extensions(self) -> None:
        """Test JavaScript extensions are mapped correctly."""
        assert EXTENSION_LANGUAGE[".js"] == "javascript"
        assert EXTENSION_LANGUAGE[".jsx"] == "javascript"

    def test_typescript_extensions(self) -> None:
        """Test TypeScript extensions are mapped correctly."""
        assert EXTENSION_LANGUAGE[".ts"] == "typescript"
        assert EXTENSION_LANGUAGE[".tsx"] == "typescript"

    def test_java_extension(self) -> None:
        """Test Java extension is mapped correctly."""
        assert EXTENSION_LANGUAGE[".java"] == "java"

    def test_infrastructure_extensions(self) -> None:
        """Test infrastructure file extensions are mapped."""
        assert EXTENSION_LANGUAGE[".tf"] == "terraform"
        assert EXTENSION_LANGUAGE[".yaml"] == "yaml"
        assert EXTENSION_LANGUAGE[".yml"] == "yaml"
        assert EXTENSION_LANGUAGE[".json"] == "json"


class TestDomainRunnerTestCommand:
    """Tests for DomainRunner.run_tests with test_command and post_test_command."""

    def _make_runner(self, tmp_path: Path) -> DomainRunner:
        """Create a DomainRunner with default config."""
        config = LucidSharkConfig()
        return DomainRunner(tmp_path, config)

    def _make_context(self, tmp_path: Path) -> Any:
        """Create a minimal ScanContext-like mock."""
        ctx = MagicMock()
        ctx.project_root = tmp_path
        ctx.ignore_patterns = MagicMock()
        return ctx

    def test_test_command_success(self, tmp_path: Path) -> None:
        """Test that a successful test_command returns no issues."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.core.domain_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
            issues = runner.run_tests(context, test_command="echo test")

        assert len(issues) == 0
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "echo test"
        assert call_args[1]["shell"] is True

    def test_test_command_failure(self, tmp_path: Path) -> None:
        """Test that a failed test_command creates a test failure issue."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.core.domain_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="FAILED: test_foo"
            )
            issues = runner.run_tests(context, test_command="make test")

        assert len(issues) == 1
        assert issues[0].id == "custom-test-failure"
        assert issues[0].domain == ToolDomain.TESTING
        assert issues[0].severity == Severity.HIGH
        assert "exited with code 1" in issues[0].description
        assert "FAILED: test_foo" in issues[0].description

    def test_test_command_skips_plugin_discovery(self, tmp_path: Path) -> None:
        """Test that test_command skips plugin-based test runner discovery."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.core.domain_runner.subprocess.run") as mock_run, \
             patch("lucidshark.plugins.test_runners.discover_test_runner_plugins") as mock_discover:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
            runner.run_tests(context, test_command="npm test")

        # Plugin discovery should NOT be called when test_command is set
        mock_discover.assert_not_called()

    def test_no_test_command_uses_plugins(self, tmp_path: Path) -> None:
        """Test that without test_command, plugin-based discovery is used."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.plugins.test_runners.discover_test_runner_plugins") as mock_discover:
            mock_discover.return_value = {}
            runner.run_tests(context, test_command=None)

        mock_discover.assert_called_once()

    def test_post_test_command_runs_after_test_command(self, tmp_path: Path) -> None:
        """Test that post_test_command runs after test_command."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)
        call_order: list[str] = []

        def side_effect(cmd: str, **_kwargs: Any) -> MagicMock:
            call_order.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("lucidshark.core.domain_runner.subprocess.run", side_effect=side_effect):
            runner.run_tests(
                context,
                test_command="make test",
                post_test_command="make clean",
            )

        assert call_order == ["make test", "make clean"]

    def test_post_test_command_runs_after_plugins(self, tmp_path: Path) -> None:
        """Test that post_test_command runs after plugin-based tests (no test_command)."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.plugins.test_runners.discover_test_runner_plugins") as mock_discover, \
             patch("lucidshark.core.domain_runner.subprocess.run") as mock_run:
            mock_discover.return_value = {}
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            runner.run_tests(context, post_test_command="make clean")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "make clean"

    def test_post_test_command_failure_logged_not_raised(self, tmp_path: Path) -> None:
        """Test that post_test_command failure is logged but doesn't raise."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        call_count = 0

        def side_effect(_cmd: str, **_kwargs: Any) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(returncode=0, stdout="OK", stderr="")
            return MagicMock(returncode=1, stdout="", stderr="cleanup error")

        with patch("lucidshark.core.domain_runner.subprocess.run", side_effect=side_effect):
            issues = runner.run_tests(
                context,
                test_command="make test",
                post_test_command="bad-cleanup",
            )

        # Test command succeeded, so no test failure issues
        assert len(issues) == 0


class TestDomainRunnerCoveragePostTestCommand:
    """Tests for DomainRunner.run_coverage with post_test_command."""

    def _make_runner(self, tmp_path: Path) -> DomainRunner:
        """Create a DomainRunner with default config."""
        config = LucidSharkConfig()
        return DomainRunner(tmp_path, config)

    def _make_context(self, tmp_path: Path) -> Any:
        """Create a minimal ScanContext-like mock."""
        ctx = MagicMock()
        ctx.project_root = tmp_path
        ctx.ignore_patterns = MagicMock()
        return ctx

    def test_post_test_command_runs_after_coverage(self, tmp_path: Path) -> None:
        """Test that post_test_command runs after coverage analysis."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.plugins.coverage.discover_coverage_plugins") as mock_discover, \
             patch("lucidshark.core.domain_runner.subprocess.run") as mock_run:
            mock_discover.return_value = {}
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            runner.run_coverage(context, post_test_command="make report")

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == "make report"

    def test_no_post_test_command_skips_subprocess(self, tmp_path: Path) -> None:
        """Test that no post_test_command means no subprocess call."""
        runner = self._make_runner(tmp_path)
        context = self._make_context(tmp_path)

        with patch("lucidshark.plugins.coverage.discover_coverage_plugins") as mock_discover, \
             patch("lucidshark.core.domain_runner.subprocess.run") as mock_run:
            mock_discover.return_value = {}
            runner.run_coverage(context, post_test_command=None)

        mock_run.assert_not_called()
