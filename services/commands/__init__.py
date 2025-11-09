import datetime
from multiprocessing import Queue
from typing import Any, Dict

from enums.command import Command
from services.logging import LoggingService


class CommandsService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _commands_queue: Queue
    _events_queue: Queue
    _commands: Dict[str, Any]
    _ping_made_at: datetime.datetime

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("commands_service")
        self._log.info("Commands service started")

        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        self._commands = {
            Command.KILL: None,
            Command.EXECUTE: None,
        }

        self._check_commands_queue()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _check_commands_queue(self) -> None:
        if self._commands_queue is None:
            self._log.error("Commands queue is not set")
            return

        if self._events_queue is None:
            self._log.error("Events queue is not set")
            return

        while True:
            command = self._commands_queue.get()
            success, kill = self._process_command(command)

            if not success:
                self._log.error(f"Failed to process command {command}")
                continue

            if kill:
                self._log.info("Shutdown commands handler")
                break

    def _process_command(self, command: Dict[str, Any]) -> tuple[bool, bool]:
        command_type = command.get("command")

        if command_type not in self._commands:
            self._log.error(f"Command {command_type} not found")
            return False, False

        if command_type is Command.KILL:
            self._log.info("Shutting down commands handler")
            return True, True

        if command_type is Command.EXECUTE:
            function = command.get("function")
            args = command.get("args")

            try:
                response = function(**args)

                if response.get("success") is False:
                    self._log.error(f"Failed to execute command {function}: {response}")
                    self._log.error(args)

                return True, False

            except Exception as e:
                self._log.error("Failed to execute command")
                self._log.error(e)
                return False, False

        return True, False
