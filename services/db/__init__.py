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
from services.db.handlers.command_delete import CommandDeleteHandler
from services.db.handlers.command_kill import CommandKillHandler
from services.db.handlers.command_store import CommandStoreHandler
from services.db.handlers.command_update import CommandUpdateHandler
from services.db.repositories.backtest import BacktestSessionRepository
from services.db.repositories.order import OrderRepository
from services.db.repositories.snapshot import SnapshotRepository
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
    _handlers: Dict[str, Any]

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
            "SnapshotRepository": SnapshotRepository(
                connection=self._database,
            ),
            "OrderRepository": OrderRepository(
                connection=self._database,
            ),
        }

        self._handlers = {
            DBCommand.KILL: CommandKillHandler(
                connection=self._connection,
                log=self._log,
            ),
            DBCommand.STORE: CommandStoreHandler(
                repositories=self._repositories,
                log=self._log,
            ),
            DBCommand.UPDATE: CommandUpdateHandler(
                repositories=self._repositories,
                log=self._log,
            ),
            DBCommand.DELETE: CommandDeleteHandler(
                repositories=self._repositories,
                log=self._log,
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
            success, kill = self._process_command(command)

            if not success:
                self._log.error(f"Failed to process command {command}")
                break

            if kill:
                self._log.info("Shutdown DB service")
                break

    def _process_command(self, command: Dict[str, Any]) -> tuple[bool, bool]:
        command_type = command.get("command")

        if not command_type:
            self._log.error("Command type is not set")
            return False, False

        handler = self._handlers.get(command_type)

        if not handler:
            self._log.error(f"Handler for command {command_type} not found")
            return False, False

        return handler.execute(command)

    def _connect(self) -> MongoClient:
        uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"

        connection = MongoClient(uri)
        self._database = connection[MONGODB_DATABASE]

        self._log.info(f"Connected to MongoDB: {connection}")
        self._log.info(f"Database: {self._database}")

        return connection
