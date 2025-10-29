import datetime
from typing import Any

from configs.timezone import TIMEZONE
from services.db import DBService


class BacktestSessionRepository:
    _collection: str = "backtest_sessions"

    def __init__(self, db: DBService) -> None:
        self._db = db

    def store(self, data: dict[str, Any]) -> None:
        self._db.database[self._collection].insert_one(
            {
                **data,
                "created_at": datetime.datetime.now(tz=TIMEZONE),
                "updated_at": datetime.datetime.now(tz=TIMEZONE),
            }
        )
