from typing import Any, Dict

from pymongo import MongoClient

from services.logging import LoggingService


class CommandKillHandler:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _connection: MongoClient
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, connection: MongoClient, log: LoggingService) -> None:
        self._connection = connection
        self._log = log

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def execute(self, _: Dict[str, Any]) -> bool:
        self._log.info("Shutting down DB service")

        if self._connection:
            self._connection.close()
            self._log.info("MongoDB connection closed")

        return True
