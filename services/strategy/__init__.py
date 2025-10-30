from typing import Any

from enums.timeframe import Timeframe
from interfaces.candle import CandleInterface
from interfaces.indicator import IndicatorInterface
from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from services.asset import AssetService
from services.backtest.handlers.session import SessionHandler
from services.db import DBService
from services.logging import LoggingService


class StrategyService(StrategyInterface):
    _indicators: dict[str, IndicatorInterface]
    _candles: dict[Timeframe, CandleInterface]

    def __init__(self) -> None:
        super().__init__()

        self._log = LoggingService()
        self._log.setup("strategy_service")

        self._indicators = {}
        self._candles = {}

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

    def on_tick(self, tick: TickModel) -> None:
        for indicator in self._indicators.values():
            indicator.on_tick(tick)

        for candle in self._candles.values():
            candle.on_tick(tick)

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
