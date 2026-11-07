"""Tests for pinned SHA-256 verification of tool downloads."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from lucidshark.bootstrap import download
from lucidshark.bootstrap.checksums import PINNED_SHA256
from lucidshark.bootstrap.download import (
    DownloadVerificationError,
    download_verified,
    verify_sha256,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
URL = "https://github.com/example/tool/releases/download/v1.0.0/tool.tar.gz"
PAYLOAD = b"tool bytes"
PAYLOAD_SHA = hashlib.sha256(PAYLOAD).hexdigest()


def _response(body: bytes) -> MagicMock:
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestVerifySha256:
    def test_accepts_match(self) -> None:
        verify_sha256(PAYLOAD, PAYLOAD_SHA, URL)

    def test_accepts_uppercase_and_whitespace(self) -> None:
        verify_sha256(PAYLOAD, f" {PAYLOAD_SHA.upper()}\n", URL)

    def test_rejects_mismatch(self) -> None:
        with pytest.raises(DownloadVerificationError, match="SHA-256 mismatch"):
            verify_sha256(b"tampered", PAYLOAD_SHA, URL)


class TestDownloadVerified:
    def test_unpinned_url_refused_before_network(self) -> None:
        with patch.object(download, "secure_urlopen") as urlopen:
            with pytest.raises(DownloadVerificationError, match="No pinned SHA-256"):
                download_verified(URL)
        urlopen.assert_not_called()

    def test_returns_bytes_when_hash_matches(self) -> None:
        with patch.dict(download.PINNED_SHA256, {URL: PAYLOAD_SHA}):
            with patch.object(
                download, "secure_urlopen", return_value=_response(PAYLOAD)
            ):
                assert download_verified(URL) == PAYLOAD

    def test_rejects_tampered_download(self) -> None:
        with patch.dict(download.PINNED_SHA256, {URL: PAYLOAD_SHA}):
            with patch.object(
                download, "secure_urlopen", return_value=_response(b"evil")
            ):
                with pytest.raises(DownloadVerificationError, match="mismatch"):
                    download_verified(URL)


def _load_updater_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "update_tool_checksums.py"
    spec = importlib.util.spec_from_file_location("update_tool_checksums", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestPinnedTable:
    def test_pins_are_well_formed(self) -> None:
        assert PINNED_SHA256
        for url, digest in PINNED_SHA256.items():
            assert url.startswith("https://github.com/"), url
            assert re.fullmatch(r"[0-9a-f]{64}", digest), url

    def test_every_plugin_download_is_pinned_on_every_platform(self) -> None:
        """Fails when a tool version or asset name changes without re-pinning."""
        script = _load_updater_script()
        by_plugin = script.collect_download_urls()
        assert len(by_plugin) == 10
        wanted = set().union(*by_plugin.values())
        missing = sorted(wanted - set(PINNED_SHA256))
        stale = sorted(set(PINNED_SHA256) - wanted)
        hint = "run: python scripts/update_tool_checksums.py"
        assert not missing, f"unpinned downloads {missing}; {hint}"
        assert not stale, f"stale pins {stale}; {hint}"
