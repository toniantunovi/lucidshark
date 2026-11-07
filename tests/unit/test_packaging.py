"""Guards for the PyPI packaging metadata in pyproject.toml."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]


def _pyproject() -> dict:
    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def test_version_is_read_from_package() -> None:
    """The wheel version must track lucidshark.__version__, the release source of truth."""
    data = _pyproject()
    assert "version" not in data["project"]
    assert "version" in data["project"]["dynamic"]
    assert data["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "lucidshark.__version__"
    }


def test_readme_is_long_description() -> None:
    """The MCP Registry validates ownership via the mcp-name marker in README.md."""
    assert _pyproject()["project"]["readme"] == "README.md"


def test_console_script_entry_point() -> None:
    assert _pyproject()["project"]["scripts"] == {"lucidshark": "lucidshark.cli:main"}


def test_runtime_data_is_packaged() -> None:
    package_data = _pyproject()["tool"]["setuptools"]["package-data"]
    assert "*.md" in package_data["lucidshark.data"]
    assert "*.xml" in package_data["lucidshark.data"]
    assert "*.yml" in package_data["lucidshark.data.templates"]
