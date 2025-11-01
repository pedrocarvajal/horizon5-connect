from multiprocessing import Queue
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

from configs.db import (
    MONGODB_DATABASE,
    MONGODB_HOST,
    MONGODB_PASSWORD,
    MONGODB_PORT,
    MONGODB_USERNAME,
)
from services.logging import LoggingService


class DBService:
    _db_commands_queue: Queue
    _db_events_queue: Queue

    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("db_service")
        self._log.info("DB service started")

        self._db_commands_queue: Queue = kwargs.get("db_commands_queue")
        self._db_events_queue: Queue = kwargs.get("db_events_queue")

        self._database = None
        self._connection = self._connect()

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

            self._log.info(f"Command: {command_name}")

    def _connect(self) -> None:
        uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"

        self._connection = MongoClient(uri)
        self._database = self._connection[MONGODB_DATABASE]

        self._log.info(f"Connected to MongoDB: {self._connection}")
        self._log.info(f"Database: {self._database}")
