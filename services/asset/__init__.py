from multiprocessing import Queue
from typing import Any, List

from interfaces.asset import AssetInterface
from interfaces.strategy import StrategyInterface
from models.tick import TickModel
from models.trade import TradeModel
from services.gateway import GatewayService
from services.logging import LoggingService


class AssetService(AssetInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _strategies: List[StrategyInterface]
    _db_commands_queue: Queue
    _db_events_queue: Queue

    _gateway: GatewayService
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("asset_service")

        self._gateway = GatewayService(self._gateway)

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._backtest = kwargs.get("backtest", False)
        self._db_commands_queue = kwargs.get("db_commands_queue")
        self._db_events_queue = kwargs.get("db_events_queue")

        if self._db_commands_queue is None:
            raise ValueError("DB commands queue is required")

        if self._db_events_queue is None:
            raise ValueError("DB events queue is required")

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")
                self._strategies.remove(strategy)
                continue

            strategy.setup(
                **kwargs,
            )

    def on_tick(self, tick: TickModel) -> None:
        for strategy in self._strategies:
            strategy.on_tick(tick)

    def on_transaction(self, trade: TradeModel) -> None:
        for strategy in self._strategies:
            strategy.on_transaction(trade)

    def on_end(self) -> None:
        for strategy in self._strategies:
            strategy.on_end()

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def name(self) -> str:
        return self._name

    @property
    def gateway(self) -> GatewayService:
        return self._gateway

    @property
    def strategies(self) -> List[StrategyInterface]:
        return self._strategies
