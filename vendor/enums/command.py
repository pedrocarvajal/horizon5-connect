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
    """

    EXECUTE = "execute"

    def is_execute(self) -> bool:
        """
        Check if the command is execute.

        Returns:
            bool: True if command is EXECUTE, False otherwise.
        """
        return self == Command.EXECUTE
