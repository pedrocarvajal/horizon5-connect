"""Command types for inter-process communication."""

from enum import Enum, unique


@unique
class Command(str, Enum):
    """
    Represents system commands used for inter-process communication.

    This enum is used throughout the system to send commands between processes
    via queues. Commands are used to control execution flow.
    Values are lowercase strings for API compatibility and JSON serialization.

    Inherits from str to allow direct string operations and JSON serialization.

    Members:
        EXECUTE: Command to execute a function with provided arguments.
        SHUTDOWN: Command to stop the command service gracefully.
    """

    EXECUTE = "execute"
    SHUTDOWN = "shutdown"

    def is_execute(self) -> bool:
        """
        Check if the command is execute.

        Returns:
            bool: True if command is EXECUTE, False otherwise.
        """
        return self == Command.EXECUTE

    def is_shutdown(self) -> bool:
        """
        Check if the command is shutdown.

        Returns:
            bool: True if command is SHUTDOWN, False otherwise.
        """
        return self == Command.SHUTDOWN
