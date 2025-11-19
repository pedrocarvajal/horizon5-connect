# Code reviewed on 2025-01-27 by pedrocarvajal

from enum import Enum, unique


@unique
class Command(str, Enum):
    """
    Represents system commands used for inter-process communication.

    This enum is used throughout the system to send commands between processes
    via queues. Commands are used to control execution flow and system shutdown.
    Values are lowercase strings for API compatibility and JSON serialization.

    Inherits from str to allow direct string operations and JSON serialization.

    Members:
        EXECUTE: Command to execute a function with provided arguments.
        KILL: Command to shutdown the command handler and terminate execution.
    """

    EXECUTE = "execute"
    KILL = "kill"

    def is_execute(self) -> bool:
        """
        Check if the command is execute.

        Returns:
            bool: True if command is EXECUTE, False otherwise.
        """
        return self == Command.EXECUTE

    def is_kill(self) -> bool:
        """
        Check if the command is kill.

        Returns:
            bool: True if command is KILL, False otherwise.
        """
        return self == Command.KILL
