"""Type definitions for console logging.

This module provides type hints for the dynamically added Console.logging attribute.
"""

from rich.console import Console


class ConsoleLogger:
    """Logger interface added to Rich Console."""

    def __init__(self, console: Console):
        self.console = console

    def info(self, message: str) -> None:
        """Log info message."""
        self.console.print(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.console.print(f"[red]{message}[/red]")

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.console.print(f"[yellow]{message}[/yellow]")

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.console.print(f"[dim]{message}[/dim]")


class ConsoleWithLogging(Console):
    """Console with logging attribute for type checking."""

    logging: ConsoleLogger
