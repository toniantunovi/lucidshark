"""Stream handler abstraction for live output during scans.

Provides a unified interface for streaming tool output to different targets:
- CLI: Print to console with optional Rich formatting
- MCP: Send notifications to AI agents
- Null: No-op for backward compatibility
"""

from __future__ import annotations

import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, TextIO


class StreamType(str, Enum):
    """Type of stream output."""

    STDOUT = "stdout"
    STDERR = "stderr"
    STATUS = "status"


@dataclass
class StreamEvent:
    """A streaming event from a tool execution."""

    tool_name: str
    stream_type: StreamType
    content: str
    line_number: Optional[int] = None


class StreamHandler(ABC):
    """Abstract base class for stream handlers.

    Implementations must be thread-safe as multiple tools may emit
    events concurrently from different threads.
    """

    @abstractmethod
    def emit(self, event: StreamEvent) -> None:
        """Emit a stream event.

        Args:
            event: The stream event to emit.
        """

    @abstractmethod
    def start_tool(self, tool_name: str) -> None:
        """Signal that a tool has started execution.

        Args:
            tool_name: Name of the tool that started.
        """

    @abstractmethod
    def end_tool(self, tool_name: str, success: bool) -> None:
        """Signal that a tool has finished execution.

        Args:
            tool_name: Name of the tool that finished.
            success: Whether the tool completed successfully.
        """


class NullStreamHandler(StreamHandler):
    """No-op handler for backward compatibility.

    Use this when streaming is not needed - all methods are no-ops.
    """

    def emit(self, event: StreamEvent) -> None:
        """No-op emit."""
        pass

    def start_tool(self, tool_name: str) -> None:
        """No-op start."""
        pass

    def end_tool(self, tool_name: str, success: bool) -> None:
        """No-op end."""
        pass


class CLIStreamHandler(StreamHandler):
    """Thread-safe CLI stream handler.

    Streams tool output to the console with optional Rich formatting.
    Shows both raw tool output and formatted status messages.
    """

    def __init__(
        self,
        output: TextIO = sys.stderr,
        show_output: bool = True,
        use_rich: bool = False,
    ):
        """Initialize CLIStreamHandler.

        Args:
            output: Output stream to write to (default: stderr).
            show_output: Whether to show raw tool output lines.
            use_rich: Whether to use Rich for formatted output.
        """
        self._output = output
        self._show_output = show_output
        self._use_rich = use_rich
        self._lock = threading.Lock()
        self._console = None

        if use_rich:
            try:
                from rich.console import Console

                self._console = Console(file=output, force_terminal=True)
            except ImportError:
                self._use_rich = False

    def emit(self, event: StreamEvent) -> None:
        """Emit a stream event to the console.

        Args:
            event: The stream event to emit.
        """
        if not self._show_output:
            return

        with self._lock:
            if event.stream_type == StreamType.STATUS:
                self._print_status(f"[{event.tool_name}] {event.content}")
            else:
                # Show raw output with tool prefix
                prefix = f"  {event.tool_name}: "
                self._print_line(prefix, event.content)

    def start_tool(self, tool_name: str) -> None:
        """Signal that a tool has started.

        Args:
            tool_name: Name of the tool that started.
        """
        with self._lock:
            self._print_status(f"[{tool_name}] Starting...")

    def end_tool(self, tool_name: str, success: bool) -> None:
        """Signal that a tool has finished.

        Args:
            tool_name: Name of the tool that finished.
            success: Whether the tool completed successfully.
        """
        with self._lock:
            if success:
                self._print_status(f"[{tool_name}] Done")
            else:
                self._print_status(f"[{tool_name}] Failed")

    def _print_status(self, message: str) -> None:
        """Print a status message.

        Args:
            message: The status message to print.
        """
        if self._console:
            self._console.print(f"[bold cyan]{message}[/bold cyan]")
        else:
            print(message, file=self._output, flush=True)

    def _print_line(self, prefix: str, content: str) -> None:
        """Print a line of tool output.

        Args:
            prefix: Prefix to add before the content.
            content: The content to print.
        """
        if self._console:
            self._console.print(f"[dim]{prefix}[/dim]{content}")
        else:
            print(f"{prefix}{content}", file=self._output, flush=True)


class CallbackStreamHandler(StreamHandler):
    """Handler that invokes callbacks for stream events.

    Useful for MCP or async contexts where events need to be
    forwarded to another system.
    """

    def __init__(
        self,
        on_event: Optional[Callable[[StreamEvent], None]] = None,
        on_start: Optional[Callable[[str], None]] = None,
        on_end: Optional[Callable[[str, bool], None]] = None,
    ):
        """Initialize CallbackStreamHandler.

        Args:
            on_event: Callback for stream events.
            on_start: Callback when a tool starts.
            on_end: Callback when a tool ends.
        """
        self._on_event = on_event
        self._on_start = on_start
        self._on_end = on_end
        self._lock = threading.Lock()

    def emit(self, event: StreamEvent) -> None:
        """Emit a stream event via callback.

        Args:
            event: The stream event to emit.
        """
        if self._on_event:
            with self._lock:
                self._on_event(event)

    def start_tool(self, tool_name: str) -> None:
        """Signal that a tool has started via callback.

        Args:
            tool_name: Name of the tool that started.
        """
        if self._on_start:
            with self._lock:
                self._on_start(tool_name)
        # Also emit as event if callback registered
        if self._on_event:
            self.emit(
                StreamEvent(
                    tool_name=tool_name,
                    stream_type=StreamType.STATUS,
                    content="started",
                )
            )

    def end_tool(self, tool_name: str, success: bool) -> None:
        """Signal that a tool has finished via callback.

        Args:
            tool_name: Name of the tool that finished.
            success: Whether the tool completed successfully.
        """
        if self._on_end:
            with self._lock:
                self._on_end(tool_name, success)
        # Also emit as event if callback registered
        if self._on_event:
            status = "completed" if success else "failed"
            self.emit(
                StreamEvent(
                    tool_name=tool_name,
                    stream_type=StreamType.STATUS,
                    content=status,
                )
            )
