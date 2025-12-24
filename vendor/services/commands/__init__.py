"""Command service for inter-process communication and command handling."""

import time
from multiprocessing import Queue
from queue import Empty
from typing import Any, Callable, Dict, Optional

from vendor.enums.command import Command
from vendor.interfaces.commands import CommandInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.models.command import CommandModel
from vendor.services.logging import LoggingService

LOG_INTERVAL_SECONDS = 15


class CommandService(CommandInterface):
    """Service that processes commands from the command queue."""

    _commands_queue: Optional["Queue[Any]"]
    _events_queue: Optional["Queue[Any]"]

    _commands: Dict[Command, None]
    _last_log_time: float
    _processed_count: int

    _log: LoggingInterface

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the commands service with queue connections."""
        self._log = LoggingService()
        self._log.info("Commands service started")

        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")
        self._processed_count = 0
        self._last_log_time = 0.0

        self._commands = {
            Command.EXECUTE: None,
        }

        self.start()

    def process_command(self, command: CommandModel) -> bool:
        """Process a single command from the queue."""
        command_type = command.command

        if command_type not in self._commands:
            self._log.error(
                "Command not found",
                command=str(command_type),
            )

            return False

        if command_type.is_execute():
            function: Optional[Callable[..., Any]] = command.function
            args: Optional[Dict[str, Any]] = command.args

            if function is None:
                self._log.error("Function is not set in command")
                return False

            if args is None:
                args = {}

            try:
                response = function(**args)

                if response.get("success") is False:
                    self._log.error(
                        "Failed to execute command",
                        function=str(function),
                        response=str(response),
                        args=str(args),
                    )

                return True

            except Exception as exception:
                self._log.error(
                    "Failed to execute command",
                    error=str(exception),
                )

                return False

        return True

    def start(self) -> None:
        """Start processing commands from the queue."""
        if self._commands_queue is None:
            self._log.error("Commands queue is not set")
            return

        if self._events_queue is None:
            self._log.error("Events queue is not set")
            return

        while True:
            command_data = self._get_next_command()

            if command_data is None:
                continue

            command = CommandModel(**command_data)

            if command.command.is_shutdown():
                self._log.info("Shutdown received, stopping commands service")
                break

            success = self.process_command(command)

            if command.command.is_execute():
                self._processed_count += 1
                self._log_progress()

            if not success:
                self._log.error(
                    "Failed to process command",
                    command=str(command),
                )

                continue

    def _get_next_command(self) -> Optional[Dict[str, Any]]:
        """Get next command from the queue."""
        if self._commands_queue is None:
            return None

        try:
            return self._commands_queue.get(timeout=0.1)
        except Empty:
            return None

    def _log_progress(self) -> None:
        """Log progress every 60 seconds."""
        current_time = time.time()
        elapsed_seconds = current_time - self._last_log_time

        if elapsed_seconds < LOG_INTERVAL_SECONDS:
            return

        self._last_log_time = current_time
        self._log.info(
            "Commands processed",
            count=self._processed_count,
        )
