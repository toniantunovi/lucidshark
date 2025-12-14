from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ScanDomain(str, Enum):
    """Scanning domains supported by lucidscan."""

    SCA = "sca"
    CONTAINER = "container"
    IAC = "iac"
    SAST = "sast"


class Severity(str, Enum):
    """Unified severity levels used across all scanners."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class UnifiedIssue:
    """Normalized issue representation shared by all scanners.

    This is a preliminary skeleton aligned with the main specification's
    unified issue schema. Additional fields may be added in later phases.
    """

    id: str
    scanner: ScanDomain
    source_tool: str
    severity: Severity
    title: str
    description: str

    file_path: Optional[Path] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    dependency: Optional[str] = None
    iac_resource: Optional[str] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None

    scanner_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanContext:
    """Context provided to scanner plugins during scan execution.

    Contains target paths, configuration, and scan settings needed
    by plugins to execute their scans.
    """

    project_root: Path
    paths: List[Path]
    enabled_domains: List[ScanDomain]
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScanResult:
    """Aggregated result for a scan over one project or path set."""

    issues: List[UnifiedIssue] = field(default_factory=list)
    schema_version: str = "0.1.0"


