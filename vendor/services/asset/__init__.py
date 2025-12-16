"""Asset service for managing trading strategies on a specific instrument."""

from __future__ import annotations

from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.gateway import GatewayInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.strategy import StrategyInterface
from vendor.models.tick import TickModel
from vendor.services.analytic import AssetAnalytic
from vendor.services.gateway import GatewayService
from vendor.services.logging import LoggingService

MAX_LEVERAGE: int = 1000


class AssetService(AssetInterface):
    """Service managing strategies and gateway for a specific trading asset."""

    _allocation: float
    _backtest: bool
    _backtest_id: Optional[str]
    _commands_queue: Optional[Queue[Any]]
    _enabled: bool
    _events_queue: Optional[Queue[Any]]
    _gateway: GatewayInterface
    _gateway_name: str
    _is_historical_filling: bool
    _leverage: int
    _name: str
    _portfolio: Optional[PortfolioInterface]
    _strategies: List[StrategyInterface]
    _symbol: str
    _tick: Optional[TickModel]

    _analytic: AnalyticInterface
    _log: LoggingService

    def __init__(self, allocation: float = 0.0, enabled: bool = True, leverage: int = 1) -> None:
        """Initialize the asset service with default configuration.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            enabled: Whether this asset is enabled for execution.
            leverage: Leverage multiplier for trading (default: 1).
        """
        self._log = LoggingService()

        if allocation < 0:
            raise ValueError("Allocation must be >= 0")

        if not (1 <= leverage < MAX_LEVERAGE):
            raise ValueError(f"Leverage must be >= 1 and < {MAX_LEVERAGE}")

        self._allocation = allocation
        self._enabled = enabled
        self._leverage = leverage
        self._strategies = []
        self._commands_queue = None
        self._events_queue = None
        self._backtest = False
        self._backtest_id = None
        self._portfolio = None
        self._is_historical_filling = False
        self._tick = None

        self._gateway = GatewayService(
            gateway=self._gateway_name,
            sandbox=False,
        )

    def on_end(self) -> Dict[str, Any]:
        """Notify all strategies that execution has ended.

        Returns:
            Asset report with aggregated performance and strategy reports.
        """
        report = self._analytic.on_end()
        return report if report else {}

    def on_new_day(self) -> None:
        """Handle a new day event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_day()

        self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """Handle a new hour event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_hour()

        self._analytic.on_new_hour()

    def on_new_minute(self) -> None:
        """Handle a new minute event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_minute()

    def on_new_month(self) -> None:
        """Handle a new month event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_month()

        self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """Handle a new week event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_week()

        self._analytic.on_new_week()

    def on_tick(self, tick: TickModel) -> None:
        """Propagate tick data to all enabled strategies."""
        self._tick = tick

        for strategy in self._strategies:
            strategy.on_tick(tick)

        self._analytic.on_tick(tick)

    def setup(self, **kwargs: Any) -> None:
        """Configure the asset with runtime parameters and initialize strategies."""
        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._portfolio = kwargs.get("portfolio")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        if not self._commands_queue:
            raise ValueError("Commands queue is required")

        if not self._events_queue:
            raise ValueError("Events queue is required")

        if self._backtest and not self._backtest_id:
            raise ValueError("Backtest ID is required")

        if not self._backtest:
            sandbox = None

            self._gateway = GatewayService(
                gateway=self._gateway_name,
                backtest=self._backtest,
                sandbox=sandbox,
            )
        else:
            self._gateway = GatewayService(
                gateway=self._gateway_name,
                sandbox=False,
            )

        enabled_strategies = [s for s in self._strategies if s.enabled]

        for strategy in self._strategies:
            if not strategy.enabled:
                self._log.warning(f"Strategy {strategy.name} is not enabled")

        self._strategies = enabled_strategies

        for strategy in self._strategies:
            strategy.setup(
                **kwargs,
            )

        self._analytic = AssetAnalytic(
            asset_id=self._symbol,
            allocation=self._allocation,
            strategies=self._strategies,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
            portfolio_id=self._portfolio.id if self._portfolio else None,
        )

    def start_historical_filling(self) -> None:
        """Mark the asset as currently processing historical data."""
        self._is_historical_filling = True

    def stop_historical_filling(self) -> None:
        """Mark the asset as no longer processing historical data."""
        self._is_historical_filling = False

    @property
    def allocation(self) -> float:
        """Return the asset allocation."""
        return self._allocation

    @property
    def analytic(self) -> AnalyticInterface:
        """Return the analytics service for this asset."""
        return self._analytic

    @property
    def enabled(self) -> bool:
        """Return whether asset is enabled."""
        return self._enabled

    @property
    def gateway(self) -> GatewayInterface:
        """Return the gateway for this asset."""
        return self._gateway

    @property
    def is_historical_filling(self) -> bool:
        """Return whether the asset is currently processing historical data."""
        return self._is_historical_filling

    @property
    def name(self) -> str:
        """Return the asset display name."""
        return self._name

    @property
    def strategies(self) -> List[StrategyInterface]:
        """Return the strategies for this asset."""
        return self._strategies

    @property
    def symbol(self) -> str:
        """Return the trading symbol."""
        return self._symbol

    @property
    def leverage(self) -> int:
        """Return the leverage multiplier for this asset."""
        return self._leverage
