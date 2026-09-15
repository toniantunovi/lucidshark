"""Unit tests for subprocess environment sanitization."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from lucidshark.core.subprocess_runner import (
    restore_loader_env,
    sanitize_loader_env,
)

MEIPASS = "/tmp/_MEIabc123"


@pytest.fixture
def frozen():
    """Pretend we are running from a PyInstaller onefile binary."""
    with patch("lucidshark.core.subprocess_runner.sys") as mock_sys:
        mock_sys._MEIPASS = MEIPASS
        yield


def test_noop_when_not_frozen():
    """Outside a frozen binary the environment is passed through untouched."""
    env = {"LD_LIBRARY_PATH": f"{MEIPASS}:/usr/lib", "PATH": "/usr/bin"}

    result = sanitize_loader_env(env)

    assert result == env
    assert result is not env, "should return a copy, not the original mapping"


def test_restores_recorded_original(frozen):
    """The bootloader's recorded pre-launch value wins."""
    result = sanitize_loader_env(
        {
            "LD_LIBRARY_PATH": f"{MEIPASS}:/opt/custom/lib",
            "LD_LIBRARY_PATH_ORIG": "/opt/custom/lib",
        }
    )

    assert result["LD_LIBRARY_PATH"] == "/opt/custom/lib"
    assert "LD_LIBRARY_PATH_ORIG" not in result


def test_drops_meipass_when_no_original_recorded(frozen):
    """Without a recorded original, only our own entry is removed."""
    result = sanitize_loader_env({"LD_LIBRARY_PATH": f"{MEIPASS}:/opt/custom/lib"})

    assert result["LD_LIBRARY_PATH"] == "/opt/custom/lib"


def test_unsets_variable_when_only_meipass(frozen):
    """A path containing nothing but our entry is removed, not left empty."""
    result = sanitize_loader_env({"LD_LIBRARY_PATH": MEIPASS})

    assert "LD_LIBRARY_PATH" not in result


def test_unsets_variable_when_original_was_empty(frozen):
    """An empty recorded original means the variable was unset before launch."""
    result = sanitize_loader_env(
        {"LD_LIBRARY_PATH": MEIPASS, "LD_LIBRARY_PATH_ORIG": ""}
    )

    assert "LD_LIBRARY_PATH" not in result


def test_handles_macos_variables(frozen):
    """The Darwin loader variables are sanitized too."""
    result = sanitize_loader_env(
        {
            "DYLD_LIBRARY_PATH": f"{MEIPASS}:/usr/local/lib",
            "DYLD_FRAMEWORK_PATH": MEIPASS,
        }
    )

    assert result["DYLD_LIBRARY_PATH"] == "/usr/local/lib"
    assert "DYLD_FRAMEWORK_PATH" not in result


def test_leaves_unrelated_variables_alone(frozen):
    """Only loader paths are touched."""
    result = sanitize_loader_env(
        {"LD_LIBRARY_PATH": MEIPASS, "PATH": "/usr/bin", "HOME": "/home/u"}
    )

    assert result["PATH"] == "/usr/bin"
    assert result["HOME"] == "/home/u"


def test_defaults_to_os_environ(frozen):
    """Called with no argument, it sanitizes the process environment."""
    with patch.dict(
        os.environ,
        {"LD_LIBRARY_PATH": f"{MEIPASS}:/usr/lib"},
        clear=False,
    ):
        result = sanitize_loader_env()

    assert result["LD_LIBRARY_PATH"] == "/usr/lib"


def test_restore_loader_env_mutates_os_environ(frozen):
    """restore_loader_env fixes the process environment in place."""
    with patch.dict(
        os.environ,
        {
            "LD_LIBRARY_PATH": f"{MEIPASS}:/opt/lib",
            "LD_LIBRARY_PATH_ORIG": "/opt/lib",
        },
        clear=False,
    ):
        restore_loader_env()

        assert os.environ["LD_LIBRARY_PATH"] == "/opt/lib"
        assert "LD_LIBRARY_PATH_ORIG" not in os.environ


def test_restore_loader_env_is_noop_when_not_frozen():
    """Development runs keep whatever the user configured."""
    with patch.dict(os.environ, {"LD_LIBRARY_PATH": "/opt/lib"}, clear=False):
        restore_loader_env()

        assert os.environ["LD_LIBRARY_PATH"] == "/opt/lib"
