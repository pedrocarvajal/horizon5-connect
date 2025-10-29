from typing import Any

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from services.backtest.handlers.session import SessionHandler
from services.db import DBService
from services.logging import LoggingService


class StrategyService(StrategyInterface):
    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("strategy_service")

    def setup(self, **kwargs: Any) -> None:
        self._asset = kwargs.get("asset")
        self._db = kwargs.get("db")
        self._session = kwargs.get("session")

        if self._asset is None:
            raise ValueError("Asset is required")

        if self._db is None:
            raise ValueError("DB is required")

        if self._session is None:
            raise ValueError("Session is required")

        self._log.info(f"Setting up {self.name}")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def name(self) -> str:
        return self._name

    @property
    def asset(self) -> AssetService:
        return self._asset

    @property
    def db(self) -> DBService:
        return self._db

    @property
    def session(self) -> SessionHandler:
        return self._session
