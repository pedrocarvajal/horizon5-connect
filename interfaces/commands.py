"""Command interface for inter-process communication and command handling."""

from abc import ABC, abstractmethod
from multiprocessing import Queue
from typing import Any, Optional

from models.command import CommandModel


class CommandInterface(ABC):
    """Abstract interface for command processing service."""

    _commands_queue: Optional["Queue[Any]"]
    _events_queue: Optional["Queue[Any]"]

    @abstractmethod
    def start(self) -> None:
        """Start processing commands from the queue."""
        pass

    @abstractmethod
    def process_command(self, command: CommandModel) -> bool:
        """Process a single command.

        Args:
            command: The command to process.

        Returns:
            True if command was processed successfully, False otherwise.
        """
        pass
