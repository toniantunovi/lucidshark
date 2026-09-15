"""Subprocess runner with streaming support.

Provides utilities for running external tools with real-time output streaming.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional, Union

from lucidshark.core.streaming import (
    NullStreamHandler,
    StreamEvent,
    StreamHandler,
    StreamType,
)


# PyInstaller's onefile bootloader prepends the extraction directory
# (``sys._MEIPASS``) to the dynamic loader search path and stashes the
# pre-launch value in ``<VAR>_ORIG``. Child processes inherit the modified
# path, so a spawned tool can load one of our bundled libraries instead of the
# system copy. When the bundled build is older this breaks the tool outright --
# e.g. ``/bin/sh`` aborting with "symbol lookup error: undefined symbol:
# rl_trim_arg_from_keyseq" because bash resolved our libreadline.so.8 rather
# than the newer one in /usr/lib.
#
# The bundle ships several libraries whose SONAME matches a system one
# (libreadline.so.8, libtinfo.so.6, libz.so.1, libgcc_s.so.1, ...), so this is
# not specific to readline. Restoring the original search path for children
# fixes all of them at once.
_LOADER_PATH_VARS = (
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "DYLD_FRAMEWORK_PATH",
)


def sanitize_loader_env(
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return a copy of ``env`` with PyInstaller's loader paths undone.

    Safe to call when not running from a frozen binary: the environment is
    copied but otherwise left alone.

    Args:
        env: Environment to sanitize. Defaults to ``os.environ``.

    Returns:
        A new mapping suitable for passing as ``subprocess(env=...)``.
    """
    result = dict(os.environ if env is None else env)

    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return result

    for var in _LOADER_PATH_VARS:
        original = result.pop(f"{var}_ORIG", None)
        if original is not None:
            # The bootloader recorded what was there before it ran.
            result[var] = original
        elif var in result:
            # No record to restore from, so drop just our own entry and keep
            # anything the user had set.
            kept = [
                entry
                for entry in result[var].split(os.pathsep)
                if entry and os.path.normpath(entry) != os.path.normpath(meipass)
            ]
            result[var] = os.pathsep.join(kept)

        # An empty value is not the same as unset for some loaders; drop it.
        if not result.get(var):
            result.pop(var, None)

    return result


def restore_loader_env() -> None:
    """Undo PyInstaller's loader-path changes in ``os.environ`` in place.

    Call once at startup so every subprocess spawned later inherits a clean
    search path, including the many call sites that do not pass ``env=``
    explicitly.

    This does not affect libraries the current process loads: glibc reads
    ``LD_LIBRARY_PATH`` once at startup, and our own bundled libraries are
    found via the executable's RUNPATH rather than the environment.
    """
    sanitized = sanitize_loader_env()

    for var in _LOADER_PATH_VARS:
        if var in sanitized:
            os.environ[var] = sanitized[var]
        else:
            os.environ.pop(var, None)
        os.environ.pop(f"{var}_ORIG", None)


def run_with_streaming(
    cmd: List[str],
    cwd: Union[str, Path],
    tool_name: str,
    stream_handler: Optional[StreamHandler] = None,
    timeout: int = 120,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command with optional streaming output.

    This function runs a subprocess and optionally streams its output
    line-by-line to a StreamHandler. When streaming is enabled, output
    is still captured and returned in the CompletedProcess for parsing.

    Args:
        cmd: Command and arguments to run.
        cwd: Working directory for the command.
        tool_name: Name of the tool (used in stream events).
        stream_handler: Handler for streaming output. If None or NullStreamHandler,
            uses regular subprocess.run for efficiency.
        timeout: Timeout in seconds (default: 120).
        capture_output: Whether to capture output (default: True). If False and
            streaming is enabled, output goes only to the stream handler.

    Returns:
        CompletedProcess with stdout/stderr captured (if capture_output=True).

    Raises:
        subprocess.TimeoutExpired: If the command times out.
        subprocess.SubprocessError: If the command fails to start.
    """
    handler = stream_handler or NullStreamHandler()
    cwd_str = str(cwd)
    env = sanitize_loader_env()

    # If no streaming requested, use simple subprocess.run for efficiency
    if isinstance(handler, NullStreamHandler):
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=cwd_str,
            timeout=timeout,
            env=env,
        )

    # Streaming mode with Popen
    handler.start_tool(tool_name)

    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    try:
        with (
            subprocess.Popen(  # nosemgrep: python36-compatibility-Popen1, python36-compatibility-Popen2
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=cwd_str,
                env=env,
            ) as proc
        ):
            # Use a queue to collect output from both streams
            output_queue: queue.Queue = queue.Queue()

            def read_stream(
                stream,
                stream_type: StreamType,
                lines_list: List[str],
            ) -> None:
                """Read lines from a stream and put them in the queue."""
                try:
                    for line_num, line in enumerate(stream, 1):
                        line = line.rstrip("\n\r")
                        lines_list.append(line)
                        output_queue.put((stream_type, line, line_num))
                except Exception:
                    pass
                finally:
                    # Signal EOF for this stream
                    output_queue.put((stream_type, None, None))

            # Start reader threads for stdout and stderr
            stdout_thread = threading.Thread(
                target=read_stream,
                args=(proc.stdout, StreamType.STDOUT, stdout_lines),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=read_stream,
                args=(proc.stderr, StreamType.STDERR, stderr_lines),
                daemon=True,
            )

            stdout_thread.start()
            stderr_thread.start()

            # Process output as it arrives
            streams_closed = 0
            while streams_closed < 2:
                try:
                    stream_type, line, line_num = output_queue.get(timeout=timeout)
                    if line is None:
                        streams_closed += 1
                    else:
                        handler.emit(
                            StreamEvent(
                                tool_name=tool_name,
                                stream_type=stream_type,
                                content=line,
                                line_number=line_num,
                            )
                        )
                except queue.Empty:
                    # Timeout waiting for output
                    proc.kill()
                    handler.end_tool(tool_name, False)
                    raise subprocess.TimeoutExpired(cmd, timeout)

            # Wait for reader threads to finish
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)

            # Wait for process to complete
            proc.wait()

            success = proc.returncode == 0
            handler.end_tool(tool_name, success)

            # Return CompletedProcess with captured output
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=proc.returncode,
                stdout="\n".join(stdout_lines) if capture_output else "",
                stderr="\n".join(stderr_lines) if capture_output else "",
            )

    except subprocess.TimeoutExpired:
        handler.end_tool(tool_name, False)
        raise
    except Exception as e:
        handler.end_tool(tool_name, False)
        raise subprocess.SubprocessError(f"Failed to run {tool_name}: {e}") from e


@contextmanager
def temporary_env(env_vars: Dict[str, str]) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables.

    Saves the current state of the specified environment variables,
    sets the new values, and restores the originals on exit.

    Args:
        env_vars: Dictionary of environment variable names to values.

    Yields:
        None

    Example:
        with temporary_env({"MY_VAR": "value"}):
            # MY_VAR is set to "value" here
            run_subprocess()
        # MY_VAR is restored to original value (or unset if it wasn't set)
    """
    old_env: Dict[str, Optional[str]] = {}

    # Save old values and set new ones
    for key, value in env_vars.items():
        if key not in os.environ or os.environ[key] != value:
            old_env[key] = os.environ.get(key)
            os.environ[key] = value

    try:
        yield
    finally:
        # Restore original environment
        for key, old_value in old_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value
