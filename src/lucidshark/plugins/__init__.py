"""Plugin infrastructure for lucidshark.

This package provides the plugin discovery and management infrastructure
for all plugin types:
- Scanner plugins (lucidshark.scanners) - Security scanners
- Linter plugins (lucidshark.linters) - Code linting
- Type checker plugins (lucidshark.type_checkers) - Type checking
- Test runner plugins (lucidshark.test_runners) - Test execution
- Coverage plugins (lucidshark.coverage) - Coverage analysis
- Enricher plugins (lucidshark.enrichers) - Post-processing
- Reporter plugins (lucidshark.reporters) - Output formatting

Plugins are discovered via Python entry points.
"""

from lucidshark.plugins.discovery import (
    discover_plugins,
    get_plugin,
    list_available_plugins,
    SCANNER_ENTRY_POINT_GROUP,
    ENRICHER_ENTRY_POINT_GROUP,
    REPORTER_ENTRY_POINT_GROUP,
    LINTER_ENTRY_POINT_GROUP,
    TYPE_CHECKER_ENTRY_POINT_GROUP,
    TEST_RUNNER_ENTRY_POINT_GROUP,
    COVERAGE_ENTRY_POINT_GROUP,
)

__all__ = [
    "discover_plugins",
    "get_plugin",
    "list_available_plugins",
    "SCANNER_ENTRY_POINT_GROUP",
    "ENRICHER_ENTRY_POINT_GROUP",
    "REPORTER_ENTRY_POINT_GROUP",
    "LINTER_ENTRY_POINT_GROUP",
    "TYPE_CHECKER_ENTRY_POINT_GROUP",
    "TEST_RUNNER_ENTRY_POINT_GROUP",
    "COVERAGE_ENTRY_POINT_GROUP",
]
