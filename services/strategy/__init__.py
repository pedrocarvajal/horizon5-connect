from typing import Any

from interfaces.strategy import StrategyInterface
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

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
