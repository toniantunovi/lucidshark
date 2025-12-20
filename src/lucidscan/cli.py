from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from importlib.metadata import version, PackageNotFoundError

from lucidscan.core.logging import configure_logging, get_logger
from lucidscan.core.models import (
    ScanContext,
    ScanDomain,
    ScanMetadata,
    ScanResult,
    UnifiedIssue,
)
from lucidscan.config import (
    LucidScanConfig,
    load_config,
    DEFAULT_PLUGINS,
)
from lucidscan.config.loader import ConfigError
from lucidscan.bootstrap.paths import get_lucidscan_home, LucidscanPaths
from lucidscan.bootstrap.platform import get_platform_info
from lucidscan.bootstrap.validation import validate_binary, ToolStatus
from lucidscan.scanners import discover_scanner_plugins, get_scanner_plugin
from lucidscan.reporters import get_reporter_plugin


LOGGER = get_logger(__name__)

# Exit codes per Section 14 of the spec
EXIT_SUCCESS = 0
EXIT_ISSUES_FOUND = 1
EXIT_SCANNER_ERROR = 2
EXIT_INVALID_USAGE = 3
EXIT_BOOTSTRAP_FAILURE = 4


def _get_version() -> str:
    try:
        return version("lucidscan")
    except PackageNotFoundError:
        # Fallback for editable installs that have not yet built metadata.
        from lucidscan import __version__

        return __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lucidscan",
        description="lucidscan - Plugin-based security scanning framework.",
    )

    # Global options
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show lucidscan version and exit.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (info-level) logging.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce logging output to errors only.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "table", "sarif", "summary"],
        default=None,
        help="Output format (default: json, or as specified in config file).",
    )

    # Status flag
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show scanner plugin status and installed versions.",
    )

    # Scanner domain flags
    parser.add_argument(
        "--sca",
        action="store_true",
        help="Enable Software Composition Analysis (Trivy plugin).",
    )
    parser.add_argument(
        "--container",
        action="store_true",
        help="Enable container image scanning (Trivy plugin).",
    )
    parser.add_argument(
        "--iac",
        action="store_true",
        help="Enable Infrastructure-as-Code scanning (Checkov plugin).",
    )
    parser.add_argument(
        "--sast",
        action="store_true",
        help="Enable static application security testing (OpenGrep plugin).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Enable all scanner plugins.",
    )

    # Target path
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory).",
    )

    # Container image targets
    parser.add_argument(
        "--image",
        action="append",
        dest="images",
        metavar="IMAGE",
        help="Container image to scan (can be specified multiple times).",
    )

    # Severity threshold for exit code
    parser.add_argument(
        "--fail-on",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help="Exit with code 1 if issues at or above this severity are found.",
    )

    # Configuration
    parser.add_argument(
        "--config",
        metavar="PATH",
        type=Path,
        help="Path to config file (default: .lucidscan.yml in project root).",
    )

    # List scanners command
    parser.add_argument(
        "--list-scanners",
        action="store_true",
        help="List all available scanner plugins and exit.",
    )

    return parser


def _handle_status() -> int:
    """Handle --status command.

    Shows scanner plugin status and environment information.

    Returns:
        Exit code (0 for success).
    """
    home = get_lucidscan_home()
    paths = LucidscanPaths(home)
    platform_info = get_platform_info()

    print(f"lucidscan version: {_get_version()}")
    print(f"Platform: {platform_info.os}-{platform_info.arch}")
    print(f"Binary cache: {home}/bin/")
    print()

    # Discover plugins via entry points
    print("Scanner plugins:")
    plugins = discover_scanner_plugins()

    if plugins:
        for name, plugin_class in sorted(plugins.items()):
            try:
                plugin = plugin_class()
                domains = ", ".join(d.value.upper() for d in plugin.domains)
                binary_dir = paths.plugin_bin_dir(name, plugin.get_version())
                binary_path = binary_dir / name

                status = validate_binary(binary_path)
                if status == ToolStatus.PRESENT:
                    status_str = f"v{plugin.get_version()} installed"
                else:
                    status_str = f"v{plugin.get_version()} (not downloaded)"

                print(f"  {name}: {status_str} [{domains}]")
            except Exception as e:
                print(f"  {name}: error loading plugin ({e})")
    else:
        print("  No plugins discovered.")

    print()
    print("Scanner binaries are downloaded automatically on first use.")

    return EXIT_SUCCESS


def _handle_list_scanners() -> int:
    """Handle --list-scanners command.

    Lists all available scanner plugins with their domains.

    Returns:
        Exit code (0 for success).
    """
    plugins = discover_scanner_plugins()

    print("Available scanner plugins:")
    print()

    if plugins:
        for name, plugin_class in sorted(plugins.items()):
            try:
                plugin = plugin_class()
                domains = ", ".join(d.value.upper() for d in plugin.domains)
                version_str = plugin.get_version()
                print(f"  {name}")
                print(f"    Domains: {domains}")
                print(f"    Version: {version_str}")
                print()
            except Exception as e:
                print(f"  {name}: error loading plugin ({e})")
                print()
    else:
        print("  No plugins discovered.")
        print()
        print("Install plugins via pip, e.g.: pip install lucidscan-snyk")

    return EXIT_SUCCESS


def cli_args_to_config_overrides(args: argparse.Namespace) -> Dict[str, Any]:
    """Convert CLI arguments to config override dict.

    CLI arguments take precedence over config file values.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Dictionary of config overrides.
    """
    overrides: Dict[str, Any] = {}

    # Domain toggles - only set if explicitly provided on CLI
    scanners: Dict[str, Dict[str, Any]] = {}

    if args.all:
        # Enable all domains
        for domain in ["sca", "sast", "iac", "container"]:
            scanners[domain] = {"enabled": True}
    else:
        if args.sca:
            scanners["sca"] = {"enabled": True}
        if args.sast:
            scanners["sast"] = {"enabled": True}
        if args.iac:
            scanners["iac"] = {"enabled": True}
        if args.container:
            scanners["container"] = {"enabled": True}

    # Container images go into container scanner options
    if args.images:
        if "container" not in scanners:
            scanners["container"] = {}
        scanners["container"]["enabled"] = True
        scanners["container"]["images"] = args.images

    if scanners:
        overrides["scanners"] = scanners

    # Fail-on threshold
    if args.fail_on:
        overrides["fail_on"] = args.fail_on

    # Note: output.format is handled in main() to allow config file to set default
    # We don't add it here because args.format always has a default value

    return overrides


def _get_enabled_domains_from_config(
    config: LucidScanConfig,
    cli_args: argparse.Namespace,
) -> List[ScanDomain]:
    """Determine which scan domains are enabled.

    If CLI flags (--sca, --sast, etc.) are provided, use those.
    Otherwise, use domains enabled in config file.

    Args:
        config: Loaded configuration.
        cli_args: Parsed CLI arguments.

    Returns:
        List of enabled ScanDomain values.
    """
    # Check if any domain flags were explicitly set on CLI
    cli_domains_set = any([
        cli_args.sca,
        cli_args.sast,
        cli_args.iac,
        cli_args.container,
        cli_args.all,
    ])

    if cli_domains_set:
        # CLI flags take precedence - use what was explicitly requested
        domains: List[ScanDomain] = []
        if cli_args.all:
            domains = [ScanDomain.SCA, ScanDomain.SAST, ScanDomain.IAC, ScanDomain.CONTAINER]
        else:
            if cli_args.sca:
                domains.append(ScanDomain.SCA)
            if cli_args.sast:
                domains.append(ScanDomain.SAST)
            if cli_args.iac:
                domains.append(ScanDomain.IAC)
            if cli_args.container:
                domains.append(ScanDomain.CONTAINER)
        return domains

    # Use config file settings
    enabled_domains: List[ScanDomain] = []
    for domain_name in config.get_enabled_domains():
        try:
            enabled_domains.append(ScanDomain(domain_name))
        except ValueError:
            LOGGER.warning(f"Unknown domain in config: {domain_name}")

    return enabled_domains


def _filter_ignored_paths(
    paths: List[Path],
    ignore_patterns: List[str],
    root: Path,
) -> List[Path]:
    """Filter paths that match any ignore pattern.

    Args:
        paths: List of paths to filter.
        ignore_patterns: Glob patterns for files/directories to ignore.
        root: Project root for relative path calculation.

    Returns:
        Filtered list of paths.
    """
    if not ignore_patterns:
        return paths

    result: List[Path] = []
    for path in paths:
        try:
            rel_path = path.relative_to(root)
        except ValueError:
            rel_path = path

        rel_str = str(rel_path)
        if not any(fnmatch(rel_str, pattern) for pattern in ignore_patterns):
            result.append(path)
        else:
            LOGGER.debug(f"Ignoring path: {rel_path}")

    return result


def _run_scan(args: argparse.Namespace, config: LucidScanConfig) -> ScanResult:
    """Execute the scan based on CLI arguments and config.

    Args:
        args: Parsed CLI arguments.
        config: Loaded configuration.

    Returns:
        ScanResult containing all issues found.
    """
    start_time = datetime.now(timezone.utc)
    project_root = Path(args.path).resolve()

    if not project_root.exists():
        raise FileNotFoundError(f"Path does not exist: {project_root}")

    enabled_domains = _get_enabled_domains_from_config(config, args)
    if not enabled_domains:
        LOGGER.warning("No scan domains enabled")
        return ScanResult()

    # Apply ignore patterns to paths
    paths = [project_root]
    if config.ignore:
        paths = _filter_ignored_paths(paths, config.ignore, project_root)

    # Build scan context with typed config
    context = ScanContext(
        project_root=project_root,
        paths=paths,
        enabled_domains=enabled_domains,
        config=config,
    )

    all_issues: List[UnifiedIssue] = []
    scanners_used: List[Dict[str, Any]] = []

    # Collect unique scanners needed based on config
    needed_scanners: set[str] = set()
    for domain in enabled_domains:
        # Get plugin from config, falling back to defaults
        scanner_name = config.get_plugin_for_domain(domain.value)
        if scanner_name:
            needed_scanners.add(scanner_name)
        else:
            LOGGER.warning(f"No scanner plugin configured for domain: {domain.value}")

    # Run each scanner
    for scanner_name in needed_scanners:
        scanner = get_scanner_plugin(scanner_name)
        if not scanner:
            LOGGER.error(f"Scanner plugin '{scanner_name}' not found")
            continue

        LOGGER.info(f"Running {scanner_name} scanner...")

        try:
            issues = scanner.scan(context)
            all_issues.extend(issues)

            scanners_used.append({
                "name": scanner_name,
                "version": scanner.get_version(),
                "domains": [d.value for d in scanner.domains],
            })

            LOGGER.info(f"{scanner_name}: found {len(issues)} issues")

        except Exception as e:
            LOGGER.error(f"Scanner {scanner_name} failed: {e}")

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # Build result
    result = ScanResult(issues=all_issues)
    result.metadata = ScanMetadata(
        lucidscan_version=_get_version(),
        scan_started_at=start_time.isoformat(),
        scan_finished_at=end_time.isoformat(),
        duration_ms=duration_ms,
        project_root=str(project_root),
        scanners_used=scanners_used,
    )
    result.summary = result.compute_summary()

    return result


def _check_severity_threshold(
    result: ScanResult, threshold: Optional[str]
) -> bool:
    """Check if any issues meet or exceed the severity threshold.

    Args:
        result: Scan result to check.
        threshold: Severity threshold ('critical', 'high', 'medium', 'low').

    Returns:
        True if issues at or above threshold exist, False otherwise.
    """
    if not threshold or not result.issues:
        return False

    threshold_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    threshold_level = threshold_order.get(threshold.lower(), 99)

    for issue in result.issues:
        issue_level = threshold_order.get(issue.severity.value, 99)
        if issue_level <= threshold_level:
            return True

    return False


def main(argv: Optional[Iterable[str]] = None) -> int:
    """CLI entrypoint.

    Returns an exit code suitable for use as a console script.
    """

    parser = build_parser()

    # Handle --help specially to return 0
    if argv is not None:
        argv_list = list(argv)
        if "--help" in argv_list or "-h" in argv_list:
            parser.print_help()
            return EXIT_SUCCESS
    else:
        argv_list = None

    args = parser.parse_args(argv_list)

    # Configure logging as early as possible.
    configure_logging(debug=args.debug, verbose=args.verbose, quiet=args.quiet)

    if args.version:
        print(_get_version())
        return EXIT_SUCCESS

    if args.status:
        return _handle_status()

    if args.list_scanners:
        return _handle_list_scanners()

    # Load configuration
    project_root = Path(args.path).resolve()
    cli_overrides = cli_args_to_config_overrides(args)

    try:
        config = load_config(
            project_root=project_root,
            cli_config_path=args.config,
            cli_overrides=cli_overrides,
        )
    except ConfigError as e:
        LOGGER.error(str(e))
        return EXIT_INVALID_USAGE

    # Check if we should run a scan (CLI flags or config file enables domains)
    cli_scan_requested = any([args.sca, args.container, args.iac, args.sast, args.all])
    config_has_enabled_domains = bool(config.get_enabled_domains())

    if cli_scan_requested or config_has_enabled_domains:
        try:
            result = _run_scan(args, config)

            # Determine output format: CLI > config > default (json)
            if args.format:
                # CLI explicitly specified format
                output_format = args.format
            elif config.output.format:
                # Use config file format
                output_format = config.output.format
            else:
                # Default to json
                output_format = "json"
            reporter = get_reporter_plugin(output_format)
            if not reporter:
                LOGGER.error(f"Reporter plugin '{output_format}' not found")
                return EXIT_SCANNER_ERROR

            # Write output to stdout
            reporter.report(result, sys.stdout)

            # Check severity threshold - CLI overrides config
            threshold = args.fail_on if args.fail_on else config.fail_on
            if _check_severity_threshold(result, threshold):
                return EXIT_ISSUES_FOUND

            return EXIT_SUCCESS

        except FileNotFoundError as e:
            LOGGER.error(str(e))
            return EXIT_INVALID_USAGE
        except Exception as e:
            LOGGER.error(f"Scan failed: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()
            return EXIT_SCANNER_ERROR

    # If no scanners are selected, show help to guide users.
    parser.print_help()
    return EXIT_SUCCESS


if __name__ == "__main__":  # pragma: no cover - exercised via console script
    raise SystemExit(main())
