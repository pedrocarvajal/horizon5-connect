"""Asset service for managing trading strategies on a specific instrument."""

from __future__ import annotations

from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.interfaces.analytic import AnalyticInterface
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.orderbook import OrderbookInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.interfaces.strategy import StrategyInterface
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService
from vendor.services.portfolio.components.gateway import Gateway


class AssetService(AssetInterface):
    """Service managing strategies and gateway for a specific trading asset."""

    _commands_queue: Optional[Queue[Any]]
    _events_queue: Optional[Queue[Any]]

    _analytic: AnalyticInterface
    _log: LoggingInterface

    def __init__(
        self,
        symbol: str,
        gateway_name: str,
        strategies: List[StrategyInterface],
        leverage: int = 1,
    ) -> None:
        """Initialize the asset service with default configuration.

        Args:
            symbol: Trading symbol for this asset.
            gateway_name: Name of the gateway to use.
            strategies: List of strategies for this asset.
            leverage: Leverage multiplier for margin trading.
        """
        self._leverage = leverage
        self._allocation = 0.0
        self._symbol = symbol
        self._gateway_name = gateway_name
        self._backtest_id = None
        self._commands_queue = None
        self._events_queue = None
        self._gateway: Optional[Gateway] = None
        self._is_historical_filling = False
        self._orderbook = None
        self._portfolio = None
        self._strategies = strategies or []
        self._tick = None

        self._log = LoggingService()

    def on_end(self) -> Dict[str, Any]:
        """Notify all strategies that execution has ended.

        Returns:
            Asset report with aggregated performance and strategy reports.
        """
        strategy_reports: List[Dict[str, Any]] = []
        trade_histories: Dict[str, List[Dict[str, Any]]] = {}

        for strategy in self._strategies:
            report = strategy.on_end()
            if report:
                strategy_reports.append(report)

            trade_histories[strategy.id] = [
                {
                    "id": order.id,
                    "strategy_id": order.strategy_id,
                    "symbol": order.symbol,
                    "side": order.side.value if order.side else None,
                    "status": order.status.value,
                    "volume": order.volume,
                    "price": order.price,
                    "close_price": order.close_price,
                    "take_profit_price": order.take_profit_price,
                    "stop_loss_price": order.stop_loss_price,
                    "profit": order.profit,
                    "profit_percentage": order.profit_percentage,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at,
                }
                for order in strategy.trade_history
            ]

        total_profit = sum(r.get("total_profit", 0) for r in strategy_reports)
        total_trades = sum(r.get("total_trades", 0) for r in strategy_reports)

        return {
            "symbol": self._symbol,
            "allocation": self._allocation,
            "balance": self._orderbook.balance if self._orderbook else 0,
            "nav": self._orderbook.nav if self._orderbook else 0,
            "total_profit": round(total_profit, 2),
            "total_trades": total_trades,
            "return_pct": round((total_profit / self._allocation) * 100, 2) if self._allocation > 0 else 0,
            "strategies": strategy_reports,
            "trade_histories": trade_histories,
        }

    def on_new_day(self) -> None:
        """Handle a new day event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_day()

        # self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """Handle a new hour event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_hour()

        # self._analytic.on_new_hour()

    def on_new_minute(self) -> None:
        """Handle a new minute event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_minute()

    def on_new_month(self) -> None:
        """Handle a new month event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_month()

        # self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """Handle a new week event. Cascades to all strategies."""
        for strategy in self._strategies:
            strategy.on_new_week()

        # self._analytic.on_new_week()

    def on_tick(self, tick: TickModel) -> None:
        """Propagate tick data to all enabled strategies."""
        self._tick = tick

        if self._orderbook:
            self._orderbook.refresh(tick)

        for strategy in self._strategies:
            strategy.on_tick(tick)

        # self._analytic.on_tick(tick)

    def on_transaction(self, order: OrderModel) -> None:
        """Route a transaction event to the owning strategy."""
        for strategy in self._strategies:
            if order.strategy_id != strategy.id:
                continue

            strategy.on_transaction(order)

        # self._analytic.on_transaction(order)

    def setup(self, **kwargs: Any) -> None:
        """Configure the asset with runtime parameters and initialize strategies.

        Args:
            **kwargs: Configuration parameters including:
                backtest: Whether running in backtest mode.
                backtest_id: Backtest identifier (required if backtest is True).
                gateway: Gateway instance (required).
                orderbook: Orderbook instance (required).
                portfolio: Portfolio instance (required).
                commands_queue: Queue for commands (required).
                events_queue: Queue for events (required).
        """
        backtest = kwargs.get("backtest", False)
        backtest_id = kwargs.get("backtest_id")
        gateway = kwargs.get("gateway")
        orderbook = kwargs.get("orderbook")
        portfolio = kwargs.get("portfolio")
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")

        if not commands_queue:
            raise ValueError("Commands queue is required")

        if not events_queue:
            raise ValueError("Events queue is required")

        if backtest_id is None and backtest:
            raise ValueError("Backtest ID is required")

        if not gateway:
            raise ValueError("Gateway is required")

        if not orderbook:
            raise ValueError("Orderbook is required")

        if not portfolio:
            raise ValueError("Portfolio is required")

        self._backtest_id = backtest_id
        self._commands_queue = commands_queue
        self._events_queue = events_queue
        self._gateway = gateway
        self._orderbook = orderbook
        self._portfolio = portfolio

        self._setup_strategies()
        self._setup_analytic()

        self._log.setup_prefix(f"[{self._symbol}]")
        self._log.success("Setup finished.", symbol=self._symbol, allocation=self._allocation)

    def start_historical_filling(self) -> None:
        """Mark the asset as currently processing historical data."""
        self._is_historical_filling = True

    def stop_historical_filling(self) -> None:
        """Mark the asset as no longer processing historical data."""
        self._is_historical_filling = False

    def _setup_strategies(self) -> None:
        """Configure strategies."""
        allocation = self._allocation / max(1, len(self._strategies))

        for strategy in self._strategies:
            strategy.setup(
                asset=self,
                allocation=allocation,
                backtest=self.backtest,
                backtest_id=self._backtest_id,
                orderbook=self._orderbook,
                portfolio=self._portfolio,
                commands_queue=self._commands_queue,
                events_queue=self._events_queue,
            )

    def _setup_analytic(self) -> None:
        """Initialize the asset analytics service."""
        # self._analytic = AssetAnalytic(
        #     asset_id=self._symbol,
        #     allocation=self._allocation,
        #     strategies=self._strategies,
        #     backtest_id=self._backtest_id,
        #     commands_queue=self._commands_queue,
        #     portfolio_id=self._portfolio.id if self._portfolio else None,
        # )
        pass

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
        return self._backtest_id is not None

    @property
    def gateway(self) -> Optional[Gateway]:
        """Return the gateway instance for this asset."""
        return self._gateway

    @property
    def gateway_name(self) -> str:
        """Return the gateway name for this asset."""
        return self._gateway_name

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
    def orderbook(self) -> Optional[OrderbookInterface]:
        """Return the orderbook for this asset."""
        return self._orderbook

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
