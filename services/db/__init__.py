from multiprocessing import Queue
from typing import Any, Dict, Optional

from pymongo import MongoClient

from configs.db import (
    MONGODB_DATABASE,
    MONGODB_HOST,
    MONGODB_PASSWORD,
    MONGODB_PORT,
    MONGODB_USERNAME,
)
from enums.db_command import DBCommand
from services.db.repositories.backtest import BacktestSessionRepository
from services.logging import LoggingService


class DBService:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _db_commands_queue: Queue
    _db_events_queue: Queue
    _database: Optional[Any]
    _connection: MongoClient
    _repositories: Dict[str, Any]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("db_service")
        self._log.info("DB service started")

        self._db_commands_queue = kwargs.get("db_commands_queue")
        self._db_events_queue = kwargs.get("db_events_queue")

        self._database = None
        self._connection = self._connect()

        self._repositories = {
            "BacktestRepository": BacktestSessionRepository(
                connection=self._database,
            ),
        }

        self._check_db_commands_queue()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _check_db_commands_queue(self) -> None:
        if self._db_commands_queue is None:
            self._log.error("DB commands queue is not set")
            return

        if self._db_events_queue is None:
            self._log.error("DB events queue is not set")
            return

        while True:
            command = self._db_commands_queue.get()
            command_name = command.get("command")
            command_repository = command.get("repository")

            self._log.debug(command)

            if not command_repository:
                self._log.error("Repository is not set")
                continue

            if not command_name:
                self._log.error("Command name is not set")
                continue

            command_method = command.get("method")
            command_method_name = command_method.get("name")
            command_method_arguments = command_method.get("arguments")

            if not command_method:
                self._log.error("Method is not set")
                continue

            if not command_method_name:
                self._log.error("Method name is not set")
                continue

            if not command_method_arguments:
                self._log.error("Method arguments are not set")
                continue

            repository = self._repositories.get(command_repository)

            if not repository:
                self._log.error(f"Repository {command_repository} not found")
                continue

            try:
                method = getattr(repository, command_method_name)
                method(**command_method_arguments)
            except Exception as e:
                self._log.error(f"Error executing {command_method_name}: {e}")
                continue

    def _connect(self) -> MongoClient:
        uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"

        connection = MongoClient(uri)
        self._database = connection[MONGODB_DATABASE]

        self._log.info(f"Connected to MongoDB: {connection}")
        self._log.info(f"Database: {self._database}")

        return connection
