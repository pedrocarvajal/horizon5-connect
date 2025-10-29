from typing import Any

from enums.timeframe import Timeframe
from interfaces.asset import AssetInterface
from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.analytic import AnalyticService
from services.gateway import GatewayService
from services.logging import LoggingService


class AssetService(AssetInterface):
    _strategies: list[StrategyInterface]
    _timeframes: list[Timeframe]
    _gateway: GatewayService
    _analytic: AnalyticService
    _log: LoggingService

    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("asset_service")

        self._analytic = AnalyticService()
        self._gateway = GatewayService(self._gateway)

    def setup(self, **kwargs: Any) -> None:
        self._analytic.setup()
        self._db = kwargs.get("db")
        self._session = kwargs.get("session")

        if self._db is None:
            raise ValueError("DB is required")

        if self._session is None:
            raise ValueError("Session is required")

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")
                self._strategies.remove(strategy)
                continue

            strategy.setup(**kwargs)

    def on_tick(self, tick: TickModel) -> None:
        self._analytic.on_tick(tick)

        for strategy in self._strategies:
            strategy.on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        self._analytic.on_transaction(trade)

        for strategy in self._strategies:
            strategy.on_transaction(trade)

    def on_end(self) -> None:
        self._analytic.on_end()

        for strategy in self._strategies:
            strategy.on_end()

    @property
    def gateway(self) -> GatewayService:
        return self._gateway

    @property
    def analytic(self) -> AnalyticService:
        return self._analytic

    @property
    def strategies(self) -> list[StrategyInterface]:
        return self._strategies
