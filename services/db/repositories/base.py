import datetime
from typing import Any, Dict

from configs.timezone import TIMEZONE
from services.db import DBService


class BaseRepository:
    _collection: str

    def __init__(self, db: DBService) -> None:
        self._db = db

    def store(self, data: Dict[str, Any]) -> None:
        self._db.database[self._collection].insert_one(
            {
                **data,
                "created_at": datetime.datetime.now(tz=TIMEZONE),
                "updated_at": datetime.datetime.now(tz=TIMEZONE),
            }
        )

    def update(
        self,
        update: Dict[str, Any],
        where: Dict[str, Any],
        update_or_insert: bool = False,
    ) -> None:
        update = {
            **update,
            "updated_at": datetime.datetime.now(tz=TIMEZONE),
        }

        self._db.database[self._collection].update_one(
            where, {"$set": update}, upsert=update_or_insert
        )
