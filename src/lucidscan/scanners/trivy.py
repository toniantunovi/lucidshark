"""Trivy scanner plugin for SCA and container scanning."""

from __future__ import annotations

import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import List
from urllib.request import urlopen

from lucidscan.scanners.base import ScannerPlugin
from lucidscan.core.models import ScanContext, ScanDomain, UnifiedIssue
from lucidscan.bootstrap.paths import LucidscanPaths
from lucidscan.bootstrap.platform import get_platform_info
from lucidscan.core.logging import get_logger

LOGGER = get_logger(__name__)

# Default version from pyproject.toml [tool.lucidscan.scanners]
DEFAULT_VERSION = "0.68.1"


class TrivyScanner(ScannerPlugin):
    """Scanner plugin for Trivy (SCA and container scanning).

    Handles:
    - SCA scans via `trivy fs`
    - Container scans via `trivy image`

    Binary management:
    - Downloads from https://github.com/aquasecurity/trivy/releases/
    - Caches at ~/.lucidscan/bin/trivy/{version}/trivy
    - Uses cache directory at ~/.lucidscan/cache/trivy/
    """

    def __init__(self, version: str = DEFAULT_VERSION) -> None:
        self._version = version
        self._paths = LucidscanPaths.default()

    @property
    def name(self) -> str:
        return "trivy"

    @property
    def domains(self) -> List[ScanDomain]:
        return [ScanDomain.SCA, ScanDomain.CONTAINER]

    def get_version(self) -> str:
        return self._version

    def ensure_binary(self) -> Path:
        """Ensure the Trivy binary is available, downloading if needed."""
        binary_dir = self._paths.plugin_bin_dir(self.name, self._version)
        binary_path = binary_dir / "trivy"

        if binary_path.exists():
            LOGGER.debug(f"Trivy binary found at {binary_path}")
            return binary_path

        LOGGER.info(f"Downloading Trivy v{self._version}...")
        self._download_binary(binary_dir)

        if not binary_path.exists():
            raise RuntimeError(f"Failed to download Trivy binary to {binary_path}")

        return binary_path

    def _download_binary(self, dest_dir: Path) -> None:
        """Download and extract Trivy binary for current platform."""
        platform_info = get_platform_info()

        # Map platform to Trivy release naming
        os_name = {
            "darwin": "macOS",
            "linux": "Linux",
            "windows": "Windows",
        }.get(platform_info.os)

        arch_name = {
            "amd64": "64bit",
            "arm64": "ARM64",
        }.get(platform_info.arch)

        if not os_name or not arch_name:
            raise RuntimeError(
                f"Unsupported platform: {platform_info.os}-{platform_info.arch}"
            )

        # Construct download URL
        # Example: trivy_0.68.1_Linux-64bit.tar.gz
        filename = f"trivy_{self._version}_{os_name}-{arch_name}.tar.gz"
        url = f"https://github.com/aquasecurity/trivy/releases/download/v{self._version}/{filename}"

        LOGGER.debug(f"Downloading from {url}")

        # Create destination directory
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Download and extract
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            try:
                with urlopen(url) as response:
                    tmp_file.write(response.read())

                # Extract tarball
                with tarfile.open(tmp_path, "r:gz") as tar:
                    tar.extractall(path=dest_dir)

                # Make binary executable
                binary_path = dest_dir / "trivy"
                if binary_path.exists():
                    binary_path.chmod(0o755)
                    LOGGER.info(f"Trivy v{self._version} installed to {binary_path}")

            finally:
                tmp_path.unlink(missing_ok=True)

    def scan(self, context: ScanContext) -> List[UnifiedIssue]:
        """Execute Trivy scan and return normalized issues.

        Args:
            context: Scan context containing target paths and configuration.

        Returns:
            List of unified issues found during the scan.
        """
        binary = self.ensure_binary()
        cache_dir = self._paths.plugin_cache_dir(self.name)
        cache_dir.mkdir(parents=True, exist_ok=True)

        issues: List[UnifiedIssue] = []

        # Determine which scan types to run based on enabled domains
        if ScanDomain.SCA in context.enabled_domains:
            issues.extend(self._run_fs_scan(binary, context, cache_dir))

        if ScanDomain.CONTAINER in context.enabled_domains:
            # Container scanning requires image targets, not implemented yet
            LOGGER.debug("Container scanning not yet implemented")

        return issues

    def _run_fs_scan(
        self, binary: Path, context: ScanContext, cache_dir: Path
    ) -> List[UnifiedIssue]:
        """Run trivy fs scan for SCA."""
        cmd = [
            str(binary),
            "fs",
            "--cache-dir", str(cache_dir),
            "--format", "json",
            "--quiet",
            str(context.project_root),
        ]

        LOGGER.debug(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0 and result.stderr:
                LOGGER.warning(f"Trivy stderr: {result.stderr}")

            # TODO: Parse JSON output and convert to UnifiedIssue
            # For now, return empty list - parsing will be implemented next
            return []

        except Exception as e:
            LOGGER.error(f"Trivy scan failed: {e}")
            return []
