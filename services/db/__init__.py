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
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("db_service")

        self._connection = None
        self._database = None

    def connect(self) -> None:
        uri = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/"

        self._connection = MongoClient(uri)
        self._database = self._connection[MONGODB_DATABASE]

        self._log.info(f"Connected to MongoDB: {self._connection}")
        self._log.info(f"Database: {self._database}")

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            self._database = None
