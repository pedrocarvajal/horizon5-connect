"""Logging interface definition."""

from abc import ABC, abstractmethod
from typing import Any


class LoggingInterface(ABC):
    """Interface for logging services."""

    @abstractmethod
    def critical(self, message: str, **context: Any) -> None:
        """Log a critical message with optional context."""
        pass

    @abstractmethod
    def debug(self, message: Any, **context: Any) -> None:
        """Log a debug message with optional context, formatting dicts/lists as JSON."""
        pass

    @abstractmethod
    def error(self, message: str, **context: Any) -> None:
        """Log an error message with optional context."""
        pass

    @abstractmethod
    def info(self, message: str, **context: Any) -> None:
        """Log an info message with optional context."""
        pass

    @abstractmethod
    def prompt(self, label: str) -> str:
        """Generate a formatted prompt string with timestamp."""
        pass

    @abstractmethod
    def separator(self) -> None:
        """Log a separator line."""
        pass

    @abstractmethod
    def setup_prefix(self, prefix: str) -> None:
        """Set a prefix to prepend to all log messages."""
        pass

    @abstractmethod
    def success(self, message: str, **context: Any) -> None:
        """Log a success message with optional context."""
        pass

    @abstractmethod
    def title(self, message: str) -> None:
        """Log a title message with separator lines."""
        pass

    @abstractmethod
    def warning(self, message: str, **context: Any) -> None:
        """Log a warning message with optional context."""
        pass
