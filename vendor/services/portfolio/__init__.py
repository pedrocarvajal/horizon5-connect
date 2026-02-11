"""Portfolio service for managing collections of trading assets."""

from __future__ import annotations

import datetime
from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from vendor.enums.timeframe import Timeframe
from vendor.helpers.get_asset_by_path import get_asset_by_path
from vendor.helpers.get_slug import get_slug
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.portfolio import PortfolioInterface
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.logging import LoggingService
from vendor.services.portfolio.components.analytic import AnalyticComponent
from vendor.services.portfolio.components.gateway import GatewayComponent
from vendor.services.portfolio.components.orderbook import OrderbookComponent
from vendor.services.strategy.helpers.get_truncated_timeframe import get_truncated_timeframe


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _commands_queue: Queue[Any]
    _events_queue: Queue[Any]

    _id: str
    _name: str
    _allocation: float
    _assets: List[AssetInterface]
    _backtest_id: Optional[str]
    _last_timestamps: Dict[Timeframe, datetime.datetime]

    _analytic: AnalyticComponent
    _gateway: GatewayComponent
    _orderbooks: OrderbookComponent
    _log: LoggingInterface

    def __init__(self, name: str, allocation: float, assets: List[str]) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._name = name
        self._allocation = allocation
        self._assets = [get_asset_by_path(path)() for path in assets]

        self._id = get_slug(self._name)
        self._backtest_id = None
        self._last_timestamps = {}

        self._log = LoggingService()

    def on_end(self) -> Dict[str, Any]:
        """Finalize portfolio and return aggregated report."""
        asset_reports = []
        trade_histories: Dict[str, Any] = {}

        for asset in self._assets:
            report = asset.on_end()
            if report:
                asset_reports.append(report)
                for strategy_id, trades in report.get("trade_histories", {}).items():
                    trade_histories[strategy_id] = trades

        total_profit = sum(r.get("total_profit", 0) for r in asset_reports)
        total_trades = sum(r.get("total_trades", 0) for r in asset_reports)

        return {
            "portfolio": self._name,
            "allocation": self._allocation,
            "total_profit": round(total_profit, 2),
            "total_trades": total_trades,
            "return_pct": round((total_profit / self._allocation) * 100, 2) if self._allocation > 0 else 0,
            "assets": asset_reports,
            "trade_histories": trade_histories,
        }

    def on_new_day(self) -> None:
        """Handle a new day event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_day()

        # self._analytic.on_new_day()

    def on_new_hour(self) -> None:
        """Handle a new hour event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_hour()

        # self._analytic.on_new_hour()

    def on_new_minute(self) -> None:
        """Handle a new minute event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_minute()

    def on_new_month(self) -> None:
        """Handle a new month event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_month()

        # self._analytic.on_new_month()

    def on_new_week(self) -> None:
        """Handle a new week event. Cascades to all assets."""
        for asset in self._assets:
            asset.on_new_week()

        # self._analytic.on_new_week()

    def on_tick(self, ticks: Dict[str, TickModel]) -> None:
        """Process tick data for all assets.

        Args:
            ticks: Dictionary mapping symbol to tick data.
        """
        last_tick: Optional[TickModel] = None

        for asset in self._assets:
            tick = ticks.get(asset.symbol)

            if tick:
                last_tick = tick
                asset.on_tick(tick)

        if last_tick:
            self._check_timeframe_transitions(last_tick)

    def on_transaction(self, order: OrderModel) -> None:
        """Handle a transaction event. Cascades to the matching asset and analytics."""
        for asset in self._assets:
            if order.asset != asset:
                continue

            asset.on_transaction(order)

        # self._analytic.on_transaction(order)

    def setup(self, **kwargs: Any) -> None:
        """Configure the portfolio name and/or runtime parameters.

        Args:
            **kwargs: Configuration parameters including:
                name: Display name for the portfolio (generates ID via slug).
                backtest: Whether running in backtest mode.
                backtest_id: Backtest identifier.
                commands_queue: Queue for commands.
                events_queue: Queue for events.
        """
        commands_queue = kwargs.get("commands_queue")
        events_queue = kwargs.get("events_queue")

        if commands_queue is None and events_queue is None:
            return

        if commands_queue is None:
            raise ValueError("Commands queue is required")

        if events_queue is None:
            raise ValueError("Events queue is required")

        if not self._allocation or self._allocation <= 0:
            raise ValueError("Allocation is required")

        if len(self._assets) == 0:
            raise ValueError("Assets is required")

        if len(self._name) == 0:
            raise ValueError("Name is required")

        self._backtest_id = kwargs.get("backtest_id")
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        for asset in self._assets:
            asset.allocation = self._allocation / len(self._assets)

        self._gateway = GatewayComponent(
            portfolio_id=self._id,
            assets=self._assets,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
        )

        self._orderbooks = OrderbookComponent(
            portfolio_id=self._id,
            assets=self._assets,
            gateways=self._gateway.gateways,
            on_transaction=self.on_transaction,
            backtest_id=self._backtest_id,
            commands_queue=self._commands_queue,
        )

        for asset in self._assets:
            orderbook = self._orderbooks.get(asset.symbol)
            gateway = self._gateway.get(asset.gateway_name)

            asset.setup(
                portfolio=self,
                orderbook=orderbook,
                gateway=gateway,
                **kwargs,
            )

        # self._analytic = AnalyticComponent(
        #     portfolio_id=self._id,
        #     assets=self._assets,
        #     backtest_id=self._backtest_id,
        #     commands_queue=self._commands_queue,
        # )

    def _check_timeframe_transitions(self, tick: TickModel) -> None:
        """Check for timeframe transitions and trigger appropriate events."""
        current_time = tick.date

        for timeframe in Timeframe:
            last_timestamp = self._last_timestamps.get(timeframe)

            if not last_timestamp:
                self._last_timestamps[timeframe] = get_truncated_timeframe(current_time, timeframe)
                continue

            current_period = get_truncated_timeframe(current_time, timeframe)

            if current_period > last_timestamp:
                self._last_timestamps[timeframe] = current_period
                self._trigger_timeframe_event(timeframe)

    def _trigger_timeframe_event(self, timeframe: Timeframe) -> None:
        """Trigger the appropriate event handler for a timeframe transition."""
        if timeframe == Timeframe.ONE_MINUTE:
            self.on_new_minute()

        elif timeframe == Timeframe.ONE_HOUR:
            self.on_new_hour()

        elif timeframe == Timeframe.ONE_DAY:
            self.on_new_day()

        elif timeframe == Timeframe.ONE_WEEK:
            self.on_new_week()

        elif timeframe == Timeframe.ONE_MONTH:
            self.on_new_month()
