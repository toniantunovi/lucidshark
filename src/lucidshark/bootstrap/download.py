"""Secure download utilities with SSL certificate handling.

This module provides SSL-aware download functions that work correctly
on macOS standalone binaries where the system certificate store is not
accessible by default.
"""

from __future__ import annotations

import hashlib
import hmac
import ssl
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

import certifi

from lucidshark.bootstrap.checksums import PINNED_SHA256


class DownloadVerificationError(RuntimeError):
    """A downloaded file could not be verified against a known SHA-256."""


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def verify_sha256(data: bytes, expected: str, source: str) -> None:
    """Raise DownloadVerificationError unless ``data`` hashes to ``expected``.

    Args:
        data: The downloaded bytes.
        expected: Expected lowercase hex SHA-256 digest.
        source: URL or name of the download, used in the error message.
    """
    actual = sha256_hex(data)
    if not hmac.compare_digest(actual, expected.strip().lower()):
        raise DownloadVerificationError(
            f"SHA-256 mismatch for {source}: expected {expected}, got {actual}. "
            "The download was rejected and nothing was installed."
        )


def get_ssl_context() -> ssl.SSLContext:
    """Get an SSL context that uses certifi's CA bundle.

    This is necessary for standalone binaries on macOS where Python
    cannot access the system's certificate store.

    Returns:
        An SSL context configured with certifi's CA certificates.
    """
    return ssl.create_default_context(cafile=certifi.where())


def secure_urlopen(url: str, timeout: Optional[float] = 30.0):
    """Open a URL with proper SSL certificate verification.

    Args:
        url: The URL to open.
        timeout: Connection timeout in seconds.

    Returns:
        A file-like object for reading the response.

    Raises:
        URLError: If the URL cannot be opened.
        ValueError: If the URL is not HTTPS.
    """
    if not url.startswith("https://"):
        raise ValueError(f"Only HTTPS URLs are supported: {url}")

    ssl_context = get_ssl_context()
    # Security: URL is validated above to only allow https:// scheme,
    # preventing file:// and other dangerous schemes
    return urlopen(url, timeout=timeout, context=ssl_context)  # nosec B310  # nosemgrep: dynamic-urllib-use-detected


def download_file(url: str, dest_path: Path, timeout: Optional[float] = 60.0) -> None:
    """Download a file from a URL with proper SSL certificate verification.

    Args:
        url: The URL to download from.
        dest_path: Path to save the downloaded file.
        timeout: Connection timeout in seconds.

    Raises:
        URLError: If the URL cannot be opened.
        ValueError: If the URL is not HTTPS.
        IOError: If the file cannot be written.
    """
    with secure_urlopen(url, timeout=timeout) as response:
        dest_path.write_bytes(response.read())


def download_verified(url: str, timeout: Optional[float] = 60.0) -> bytes:
    """Download a pinned tool asset and verify it against its SHA-256 pin.

    Every URL LucidShark downloads a tool from must have an entry in
    ``lucidshark.bootstrap.checksums.PINNED_SHA256``. Unpinned URLs are
    refused before any network access, so a tool can never be installed
    without an integrity check.

    Args:
        url: The HTTPS URL of the release asset.
        timeout: Connection timeout in seconds.

    Returns:
        The verified file contents.

    Raises:
        DownloadVerificationError: If the URL has no pin or the hash differs.
        URLError: If the URL cannot be opened.
        ValueError: If the URL is not HTTPS.
    """
    expected = PINNED_SHA256.get(url)
    if expected is None:
        raise DownloadVerificationError(
            f"No pinned SHA-256 for {url}. LucidShark only installs tool "
            "binaries whose checksum ships with it; run "
            "scripts/update_tool_checksums.py after changing a tool version."
        )
    with secure_urlopen(url, timeout=timeout) as response:
        data = response.read()
    verify_sha256(data, expected, url)
    return data
