from multiprocessing import Queue
from typing import Any, List, Optional

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
    _backtest_id: Optional[str]
    _strategies: List[StrategyInterface]
    _commands_queue: Optional[Queue]
    _events_queue: Optional[Queue]
    _gateway: GatewayService
    _gateway_name: str
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, futures: bool = True) -> None:
        self._log = LoggingService()
        self._log.setup("asset_service")

        self._strategies = []
        self._commands_queue = None
        self._events_queue = None
        self._backtest = False
        self._backtest_id = None
        self._gateway = GatewayService(
            gateway=self._gateway_name,
            sandbox=self._backtest,
            futures=futures,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setup(self, **kwargs: Any) -> None:
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        if self._commands_queue is None:
            raise ValueError("Commands queue is required")

        if self._events_queue is None:
            raise ValueError("Events queue is required")

        if self._backtest_id is None:
            raise ValueError("Backtest ID is required")

        enabled_strategies = [s for s in self._strategies if s.enabled]

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")

        self._strategies = enabled_strategies

        for strategy in self._strategies:
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
