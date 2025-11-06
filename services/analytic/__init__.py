import datetime
import json
from multiprocessing import Queue
from typing import Any

from enums.backtest_status import BacktestStatus
from enums.command import Command
from enums.order_status import OrderStatus
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
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _backtest_id: str
    _strategy_id: str
    _orderbook: OrderbookHandler
    _commands_queue: Queue
    _events_queue: Queue
    _horizon_router: HorizonRouterProvider

    _started: bool
    _started_at: datetime.datetime
    _ended_at: datetime.datetime

    _tick: TickModel
    _snapshot: SnapshotModel
    _executed_orders: int

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("analytic_service")

        self._horizon_router = HorizonRouterProvider()

        self._backtest = kwargs.get("backtest", False)
        self._backtest_id = kwargs.get("backtest_id")
        self._strategy_id = kwargs.get("strategy_id")
        self._orderbook = kwargs.get("orderbook")
        self._commands_queue = kwargs.get("commands_queue")
        self._events_queue = kwargs.get("events_queue")

        if self._backtest_id is None:
            raise ValueError("Backtest ID is required")

        if self._backtest is None:
            raise ValueError("Backtest is required")

        if self._commands_queue is None:
            raise ValueError("Commands queue is required")

        if self._events_queue is None:
            raise ValueError("Events queue is required")

        if self._strategy_id is None:
            raise ValueError("Strategy is required")

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
        if order.status is OrderStatus.OPENED:
            pass

        elif order.status is OrderStatus.CLOSED:
            self._executed_orders += 1
            self._snapshot.profit_history.append(order.profit)
            self._store_order(order)

        elif order.status is OrderStatus.CANCELLED:
            pass

    def on_tick(self, tick: TickModel) -> None:
        self._tick = tick
        self._refresh()

        if not self._started:
            self._started = True
            self._started_at = self._tick.date
            self._store_snapshot(SnapshotEvent.START_SNAPSHOT)

    def on_new_day(self) -> None:
        self._snapshot.performance_history.append(self._snapshot.performance)
        self._snapshot.nav_history.append(self._snapshot.nav)
        self._perform_calculations()
        self._store_snapshot(SnapshotEvent.ON_NEW_DAY)

    def on_end(self) -> None:
        self._ended_at = self._tick.date
        self._perform_calculations()
        self._store_snapshot(SnapshotEvent.BACKTEST_END)
        self._update_backtest_to_finished()
        self._report()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _report(self) -> None:
        self._log.info(f"Backtest ID: {self._backtest_id}")
        self._log.info(f"Strategy: {self._strategy_id}")

        self._log.debug(
            json.dumps(
                {
                    **self._snapshot.to_dict(),
                    "performance_history": self._snapshot.performance_history,
                    "nav_history": self._snapshot.nav_history,
                    "profit_history": self._snapshot.profit_history,
                },
                indent=4,
                default=str,
            )
        )

    def _perform_calculations(self) -> None:
        allocation = self._snapshot.allocation
        nav = self._snapshot.nav
        elapsed_days = self._elapsed_days
        performance = self._snapshot.performance
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
        self._snapshot.nav = self._orderbook.nav
        self._snapshot.allocation = self._orderbook.allocation
        self._snapshot.nav_peak = max(self._snapshot.nav_peak, self._snapshot.nav)

        if self._snapshot.drawdown < 0:
            self._snapshot.max_drawdown = min(
                self._snapshot.max_drawdown,
                self._snapshot.drawdown,
            )

    def _store_order(self, order: OrderModel) -> None:
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
        self._snapshot.event = event
        self._snapshot.created_at = self._tick.date

        body = {
            **self._snapshot.to_dict(),
            "created_at": int(float(self._snapshot.created_at.timestamp())),
        }

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

    @property
    def _elapsed_days(self) -> int:
        return (self._tick.date - self._started_at).days
