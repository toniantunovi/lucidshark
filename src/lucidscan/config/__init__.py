"""Configuration module for lucidscan.

Provides configuration file loading, parsing, and validation with support for:
- Project-level config (.lucidscan.yml)
- Global config (~/.lucidscan/config/config.yml)
- Environment variable expansion
- Plugin-specific configuration passthrough
"""

from lucidscan.config.models import (
    LucidScanConfig,
    OutputConfig,
    ScannerDomainConfig,
    DEFAULT_PLUGINS,
)
from lucidscan.config.loader import load_config, find_project_config, find_global_config
from lucidscan.config.validation import validate_config, ConfigValidationWarning

__all__ = [
    "LucidScanConfig",
    "OutputConfig",
    "ScannerDomainConfig",
    "DEFAULT_PLUGINS",
    "load_config",
    "find_project_config",
    "find_global_config",
    "validate_config",
    "ConfigValidationWarning",
]
