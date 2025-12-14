"""Logging interface definition."""

from abc import ABC, abstractmethod
from typing import Any


class LoggingInterface(ABC):
    """Interface for logging services."""

    @abstractmethod
    def critical(self, message: str) -> None:
        """Log a critical message."""
        pass

    @abstractmethod
    def debug(self, message: Any) -> None:
        """Log a debug message, formatting dicts/lists as JSON."""
        pass

    @abstractmethod
    def error(self, message: str) -> None:
        """Log an error message."""
        pass

    @abstractmethod
    def info(self, message: str) -> None:
        """Log an info message."""
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
    def success(self, message: str) -> None:
        """Log a success message."""
        pass

    @abstractmethod
    def title(self, message: str) -> None:
        """Log a title message with separator lines."""
        pass

    @abstractmethod
    def warning(self, message: str) -> None:
        """Log a warning message."""
        pass
