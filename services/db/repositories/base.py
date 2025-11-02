import datetime
from typing import Any, Dict

from configs.timezone import TIMEZONE


class BaseRepository:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _collection: str

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def store(self, data: Dict[str, Any]) -> None:
        self._connection[self._collection].insert_one(
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
        update_query = {
            "$set": {
                **update,
                "updated_at": datetime.datetime.now(tz=TIMEZONE),
            }
        }

        if update_or_insert:
            update_query["$setOnInsert"] = {
                "created_at": datetime.datetime.now(tz=TIMEZONE)
            }

        self._connection[self._collection].update_one(
            where, update_query, upsert=update_or_insert
        )

    def delete(self, where: Dict[str, Any]) -> None:
        self._connection[self._collection].delete_many(where)
