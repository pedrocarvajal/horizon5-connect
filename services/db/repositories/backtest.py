from typing import Any

from services.db.repositories.base import BaseRepository


class BacktestSessionRepository(BaseRepository):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _collection: str = "backtest"

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
