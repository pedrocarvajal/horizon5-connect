# Code reviewed on 2025-11-19 by pedrocarvajal

import datetime
import json
from multiprocessing import Queue
from typing import Optional

from enums.backtest_status import BacktestStatus
from enums.command import Command
from enums.snapshot_event import SnapshotEvent
from interfaces.analytic import AnalyticInterface
from models.order import OrderModel
from models.snapshot import SnapshotModel
from models.tick import TickModel
from providers.horizon_router import HorizonRouterProvider
from services.analytic.helpers.get_cagr import get_cagr
from services.analytic.helpers.get_calmar_ratio import get_calmar_ratio
from services.analytic.helpers.get_expected_shortfall import get_expected_shortfall
from services.analytic.helpers.get_profit_factor import get_profit_factor
from services.analytic.helpers.get_r2 import get_r2
from services.analytic.helpers.get_recovery_factor import get_recovery_factor
from services.analytic.helpers.get_sharpe_ratio import get_sharpe_ratio
from services.analytic.helpers.get_sortino_ratio import get_sortino_ratio
from services.analytic.helpers.get_ulcer_index import get_ulcer_index
from services.logging import LoggingService
from services.strategy.handlers.orderbook import OrderbookHandler


class AnalyticService(AnalyticInterface):
    """
    Service for calculating and tracking financial analytics during backtests.

    This service monitors trading performance, calculates various financial
    metrics (Sharpe ratio, Sortino ratio, CAGR, etc.), and stores snapshots
    of analytics data at different events (start, daily, end). It integrates
    with the Horizon Router API to persist analytics data.

    Attributes:
        _backtest: Whether the service is running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _strategy_id: Identifier of the strategy being analyzed.
        _orderbook: Handler for managing orders and portfolio state.
        _commands_queue: Queue for sending commands to external services.
        _events_queue: Queue for receiving events from external services.
        _horizon_router: Provider for Horizon Router API interactions.
        _log: Logging service instance for logging operations.
        _started: Whether analytics tracking has started.
        _started_at: Timestamp when analytics tracking started.
        _ended_at: Timestamp when analytics tracking ended.
        _tick: Current market tick data.
        _snapshot: Current analytics snapshot model.
        _executed_orders: Count of executed orders.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _backtest_id: Optional[str]
    _strategy_id: str
    _orderbook: OrderbookHandler
    _commands_queue: Queue
    _events_queue: Queue
    _horizon_router: HorizonRouterProvider
    _log: LoggingService

    _started: bool
    _started_at: datetime.datetime
    _ended_at: datetime.datetime

    _tick: Optional[TickModel]
    _snapshot: SnapshotModel
    _executed_orders: int

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        strategy_id: str,
        backtest: bool,
        backtest_id: Optional[str],
        orderbook: OrderbookHandler,
        commands_queue: Queue,
        events_queue: Queue,
    ) -> None:
        """
        Initialize the analytics service.

        Args:
            strategy_id: Identifier of the strategy being analyzed.
            backtest: Whether the service is running in backtest mode.
            backtest_id: Optional backtest identifier. Required if backtest is True.
            orderbook: Handler for managing orders and portfolio state.
            commands_queue: Queue for sending commands to external services.
            events_queue: Queue for receiving events from external services.

        Raises:
            ValueError: If backtest is True but backtest_id is None.
            ValueError: If strategy_id is None or empty.
        """
        self._log = LoggingService()
        self._log.setup("analytic_service")

        self._horizon_router = HorizonRouterProvider()

        self._backtest = backtest
        self._backtest_id = backtest_id
        self._strategy_id = strategy_id
        self._orderbook = orderbook
        self._commands_queue = commands_queue
        self._events_queue = events_queue

        if self._backtest and self._backtest_id is None:
            raise ValueError("Backtest ID is required when backtest is True")

        if self._strategy_id is None:
            raise ValueError("Strategy ID is required")

        self._started = False
        self._tick = None
        self._executed_orders = 0

        self._snapshot = SnapshotModel(
            backtest=self._backtest,
            backtest_id=self._backtest_id,
            strategy_id=self._strategy_id,
            nav=self._orderbook.nav,
            allocation=self._orderbook.allocation,
            nav_peak=self._orderbook.nav,
            r2=0,
            cagr=0,
            calmar_ratio=0,
            expected_shortfall=0,
            max_drawdown=0,
            profit_factor=0,
            recovery_factor=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            ulcer_index=0,
        )

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_transaction(self, order: OrderModel) -> None:
        """
        Handle a transaction event (order status change).

        When an order is closed, this method updates the executed orders count,
        records the profit in the snapshot's profit history, and stores the order
        via the commands queue.

        Args:
            order: The order model representing the transaction.
        """
        if order.status.is_closed():
            self._executed_orders += 1
            self._snapshot.profit_history.append(order.profit)
            self._store_order(order)

    def on_tick(self, tick: TickModel) -> None:
        """
        Handle a new market tick event.

        Updates the current tick, refreshes snapshot data, and if this is the
        first tick, initializes the analytics tracking and stores the start snapshot.

        Args:
            tick: The current market tick data.
        """
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date
            self._store_snapshot(SnapshotEvent.START_SNAPSHOT)

    def on_new_day(self) -> None:
        """
        Handle a new day event.

        Records the current performance and NAV in history, performs all
        financial calculations, and stores a daily snapshot.
        """
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()
        self._store_snapshot(SnapshotEvent.ON_NEW_DAY)

    def on_new_month(self) -> None:
        """
        Handle a new month event.

        Logs monthly performance metrics if running in live (non-sandbox) mode.
        Performance and drawdown percentages are displayed.
        """
        performance = self._snapshot.performance
        performance_percentage = self._snapshot.performance_percentage * 100
        max_drawdown_percentage = self._snapshot.max_drawdown * 100

        if self._is_running_in_live_mode():
            self._log.info(
                f"Closing month, with: {performance:.2f} ({performance_percentage:.2f}%), "
                f"max drawdown: {max_drawdown_percentage:.2f}%."
            )

    def on_end(self) -> None:
        """
        Handle the end of analytics tracking.

        Records the end timestamp, performs final calculations, stores the
        final snapshot, updates the backtest status to completed, and generates
        the final report.
        """
        self._ended_at = self._tick.date
        self._perform_calculations()
        self._store_snapshot(SnapshotEvent.BACKTEST_END)
        self._update_backtest_to_finished()
        self._report()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _report(self) -> None:
        """
        Generate and log the final analytics report.

        Logs backtest ID and strategy ID, then outputs a detailed JSON report
        containing all snapshot metrics, timestamps, and elapsed days.
        """
        self._log.info(f"Backtest ID: {self._backtest_id}")
        self._log.info(f"Strategy: {self._strategy_id}")

        days_elapsed = (self._ended_at - self._started_at).days

        self._log.debug(
            json.dumps(
                {
                    **self._snapshot.to_dict(),
                    "started_at": self._started_at,
                    "ended_at": self._ended_at,
                    "days_elapsed": days_elapsed,
                    # "performance_history": self._snapshot.performance_history,
                    # "nav_history": self._snapshot.nav_history,
                    # "profit_history": self._snapshot.profit_history,
                },
                indent=4,
                default=str,
            )
        )

    def _perform_calculations(self) -> None:
        """
        Calculate all financial metrics and update the snapshot.

        Computes various risk-adjusted return metrics including R², CAGR,
        Calmar ratio, expected shortfall, profit factor, recovery factor,
        Sharpe ratio, Sortino ratio, and ulcer index.
        """
        allocation = self._snapshot.allocation
        nav = self._snapshot.nav
        elapsed_days = self._elapsed_days
        performance = self._snapshot.performance_percentage
        performance_history = self._snapshot.performance_history
        nav_history = self._snapshot.nav_history
        profit_history = self._snapshot.profit_history
        max_drawdown = self._snapshot.max_drawdown

        self._snapshot.r2 = get_r2(performance_history)
        self._snapshot.cagr = get_cagr(allocation, nav, elapsed_days)
        self._snapshot.calmar_ratio = get_calmar_ratio(self._snapshot.cagr, max_drawdown)
        self._snapshot.expected_shortfall = get_expected_shortfall(nav_history)
        self._snapshot.profit_factor = get_profit_factor(profit_history)
        self._snapshot.recovery_factor = get_recovery_factor(performance, max_drawdown)
        self._snapshot.sharpe_ratio = get_sharpe_ratio(nav_history)
        self._snapshot.sortino_ratio = get_sortino_ratio(nav_history)
        self._snapshot.ulcer_index = get_ulcer_index(nav_history)

    def _refresh(self) -> None:
        """
        Refresh snapshot data from the orderbook.

        Updates NAV, allocation, NAV peak, and max drawdown based on current
        orderbook state.
        """
        self._snapshot.nav = self._orderbook.nav
        self._snapshot.allocation = self._orderbook.allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    def _store_order(self, order: OrderModel) -> None:
        """
        Store an order via the commands queue.

        Converts the order to a dictionary, removes the ID, converts timestamps
        to integers, and queues a command to create the order via Horizon Router.

        Args:
            order: The order model to store.
        """
        order = order.to_dict()
        del order["id"]

        order["created_at"] = int(float(order["created_at"].timestamp()))
        order["updated_at"] = int(float(order["updated_at"].timestamp()))

        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": self._horizon_router.order_create,
                "args": {
                    "body": order,
                },
            }
        )

    def _store_snapshot(self, event: SnapshotEvent) -> None:
        """
        Store a snapshot via the commands queue.

        Sets the snapshot event and timestamp, creates a body dictionary with
        snapshot data, removes computed fields, and queues a command to create
        the snapshot via Horizon Router.

        Args:
            event: The snapshot event type (START_SNAPSHOT, ON_NEW_DAY, BACKTEST_END).
        """
        self._snapshot.event = event
        self._snapshot.created_at = self._tick.date

        body = {
            **self._snapshot.to_dict(),
            "event": event.value,
            "created_at": int(float(self._snapshot.created_at.timestamp())),
        }

        del body["performance"]
        del body["performance_percentage"]

        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": self._horizon_router.snapshot_create,
                "args": {
                    "body": body,
                },
            }
        )

    def _update_backtest_to_finished(self) -> None:
        """
        Update the backtest status to completed.

        Queues a command to update the backtest status to COMPLETED via
        Horizon Router.
        """
        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": self._horizon_router.backtest_update,
                "args": {
                    "id": self._backtest_id,
                    "body": {
                        "status": BacktestStatus.COMPLETED.value,
                    },
                },
            }
        )

    def _is_running_in_live_mode(self) -> bool:
        """
        Check if the service is running in live (non-sandbox) mode.

        Returns:
            True if tick exists and is not in sandbox mode, False otherwise.
        """
        return self._tick is not None and not self._tick.sandbox

    @property
    def _elapsed_days(self) -> int:
        """
        Calculate the number of days elapsed since tracking started.

        Returns:
            Number of days elapsed, or 0 if tick is not yet available.
        """
        if self._tick is None:
            return 0
        return (self._tick.date - self._started_at).days
