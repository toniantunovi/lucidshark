"""Consistency checks for the MCP Registry metadata (server.json)."""

from __future__ import annotations

import json
from pathlib import Path

from lucidshark import __version__
from lucidshark.cli.commands.init import LUCIDSHARK_MCP_ARGS

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_NAME = "io.github.toniantunovi/lucidshark"


def _server_json() -> dict:
    return json.loads((REPO_ROOT / "server.json").read_text(encoding="utf-8"))


def test_versions_match_package_version() -> None:
    """A release bumps __version__; server.json must be bumped with it."""
    server = _server_json()
    assert server["version"] == __version__
    assert [p["version"] for p in server["packages"]] == [__version__]


def test_package_runs_mcp_server_over_stdio() -> None:
    package = _server_json()["packages"][0]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == "lucidshark"
    assert package["transport"] == {"type": "stdio"}
    assert [a["value"] for a in package["packageArguments"]] == LUCIDSHARK_MCP_ARGS


def test_readme_has_pypi_ownership_marker() -> None:
    assert _server_json()["name"] == SERVER_NAME
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"<!-- mcp-name: {SERVER_NAME} -->" in readme
