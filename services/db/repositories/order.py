from typing import Any

from services.db.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _collection: str = "orders"

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
