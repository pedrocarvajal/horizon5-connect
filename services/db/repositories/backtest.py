from services.db import DBService
from services.db.repositories.base import BaseRepository


class BacktestRepository(BaseRepository):
    _collection: str = "backtests"

    def __init__(self, db: DBService) -> None:
        super().__init__(db)
