"""Asset service for managing trading strategies on a specific instrument."""

from __future__ import annotations

from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.gateway import GatewayInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.strategy import StrategyInterface
from vendor.models.tick import TickModel
from vendor.services.analytic import AssetAnalytic
from vendor.services.gateway import GatewayService
from vendor.services.logging import LoggingService

MAX_LEVERAGE: int = 1000


class AssetService(AssetInterface):
    """Service managing strategies and gateway for a specific trading asset."""

    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]

    _gateway_name: str

    _analytic: AnalyticInterface
    _gateway: GatewayInterface
    _log: LoggingInterface

    def __init__(self, allocation: float = 0.0, leverage: int = 1) -> None:
        """Initialize the asset service with default configuration.

        Args:
            allocation: Total allocation for this asset to distribute among strategies.
            leverage: Leverage multiplier for trading (default: 1).
        """
        if allocation < 0:
            raise ValueError("Allocation must be >= 0")

        if not (1 <= leverage < MAX_LEVERAGE):
            raise ValueError(f"Leverage must be >= 1 and < {MAX_LEVERAGE}")

        self._allocation = allocation
        self._leverage = leverage

        self._backtest = False
        self._backtest_id = None
        self._commands_queue = None
        self._events_queue = None
        self._is_historical_filling = False
        self._portfolio = None
        self._strategies = []
        self._tick = None

        self._log = LoggingService()

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
        """Configure the asset with runtime parameters and initialize strategies.

        Args:
            **kwargs: Configuration parameters including:
                backtest: Whether running in backtest mode.
                backtest_id: Backtest identifier (required if backtest is True).
                portfolio: Portfolio instance (required).
                commands_queue: Queue for commands (required).
                events_queue: Queue for events (required).
        """
        backtest = kwargs.get("backtest", False)
        backtest_id = kwargs.get("backtest_id")
        portfolio = kwargs.get("portfolio")
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")

        if not commands_queue:
            raise ValueError("Commands queue is required")

        if not events_queue:
            raise ValueError("Events queue is required")

        if backtest and not backtest_id:
            raise ValueError("Backtest ID is required")

        if not portfolio:
            raise ValueError("Portfolio is required")

        self._backtest = backtest
        self._backtest_id = backtest_id
        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._portfolio = portfolio

        self._gateway = GatewayService(
            gateway=self._gateway_name,
            backtest=self._backtest,
        )

        self._configure_strategies()
        self._setup_analytic()

        self._log.setup_prefix(f"[{self._symbol}]")
        self._log.success("Setup finished.", symbol=self._symbol, allocation=self._allocation)

    def start_historical_filling(self) -> None:
        """Mark the asset as currently processing historical data."""
        self._is_historical_filling = True

    def stop_historical_filling(self) -> None:
        """Mark the asset as no longer processing historical data."""
        self._is_historical_filling = False

    def _configure_strategies(self) -> None:
        """Configure strategies."""
        strategies_count = len(self._strategies)
        allocation_per_strategy = self._allocation / strategies_count if strategies_count > 0 else 0.0

        for strategy in self._strategies:
            strategy.setup(
                **{
                    "asset": self,
                    "allocation": allocation_per_strategy,
                    "backtest": self._backtest,
                    "backtest_id": self._backtest_id,
                    "portfolio": self._portfolio,
                    "commands_queue": self._commands_queue,
                    "events_queue": self._events_queue,
                }
            )

    def _setup_analytic(self) -> None:
        """Initialize the asset analytics service."""
        self._analytic = AssetAnalytic(
            asset_id=self._symbol,
            allocation=self._allocation,
            strategies=self._strategies,
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
            portfolio_id=self._portfolio.id if self._portfolio else None,
        )

    @property
    def allocation(self) -> float:
        """Return the asset allocation."""
        return self._allocation

    @property
    def analytic(self) -> AnalyticInterface:
        """Return the analytics service for this asset."""
        return self._analytic

    @property
    def backtest(self) -> bool:
        """Return whether running in backtest mode."""
        return self._backtest

    @property
    def gateway(self) -> GatewayInterface:
        """Return the gateway for this asset."""
        return self._gateway

    @property
    def is_historical_filling(self) -> bool:
        """Return whether the asset is currently processing historical data."""
        return self._is_historical_filling

    @property
    def leverage(self) -> int:
        """Return the leverage multiplier for this asset."""
        return self._leverage

    @property
    def name(self) -> str:
        """Return the asset display name."""
        return self._symbol

    @property
    def portfolio(self) -> Optional[PortfolioInterface]:
        """Return the portfolio for this asset."""
        return self._portfolio

    @property
    def strategies(self) -> List[StrategyInterface]:
        """Return the strategies for this asset."""
        return self._strategies

    @property
    def symbol(self) -> str:
        """Return the trading symbol."""
        return self._symbol

    @property
    def tick(self) -> Optional[TickModel]:
        """Return the latest tick data."""
        return self._tick

    @allocation.setter
    def allocation(self, value: float) -> None:
        """Set the asset allocation."""
        self._allocation = value
