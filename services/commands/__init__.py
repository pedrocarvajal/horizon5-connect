"""Command service for inter-process communication and command handling."""

from multiprocessing import Queue
from typing import Any, Callable, Dict, Optional, Tuple

from enums.command import Command
from interfaces.commands import CommandInterface
from models.command import CommandModel
from services.logging import LoggingService


class CommandService(CommandInterface):
    """Service that processes commands from the command queue."""

    _commands_queue: Optional["Queue[Any]"]
    _events_queue: Optional["Queue[Any]"]
    _commands: Dict[Command, None]

    _log: LoggingService

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the commands service with queue connections."""
        self._log = LoggingService()
        self._log.info("Commands service started")

        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        self._commands = {
            Command.KILL: None,
            Command.EXECUTE: None,
        }

        self.start()

    def process_command(self, command: CommandModel) -> Tuple[bool, bool]:
        """Process a single command from the queue."""
        command_type = command.command

        if command_type not in self._commands:
            self._log.error(f"Command {command_type} not found")
            return False, False

        if command_type.is_kill():
            self._log.info("Shutting down commands handler")
            return True, True

        if command_type.is_execute():
            function: Optional[Callable[..., Any]] = command.function
            args: Optional[Dict[str, Any]] = command.args

            if function is None:
                self._log.error("Function is not set in command")
                return False, False

            if args is None:
                args = {}

            try:
                response = function(**args)

                if response.get("success") is False:
                    self._log.error(f"Failed to execute command {function}: {response}")
                    self._log.error(str(args))

                return True, False

            except Exception as exception:
                self._log.error("Failed to execute command")
                self._log.error(str(exception))
                return False, False

        return True, False

    def start(self) -> None:
        """Start processing commands from the queue."""
        if self._commands_queue is None:
            self._log.error("Commands queue is not set")
            return

        if self._events_queue is None:
            self._log.error("Events queue is not set")
            return

        while True:
            command_data = self._commands_queue.get()
            command = CommandModel(**command_data)
            success, kill = self.process_command(command)

            if not success:
                self._log.error(f"Failed to process command {command}")
                continue

            if kill:
                self._log.info("Shutdown commands handler")
                break
