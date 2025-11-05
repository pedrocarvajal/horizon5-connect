import datetime
from multiprocessing import Queue
from typing import Any

from configs.timezone import TIMEZONE
from enums.backtest_status import BacktestStatus
from enums.command import Command
from enums.order_status import OrderStatus
from enums.snapshot_event import SnapshotEvent
from interfaces.analytic import AnalyticInterface
from models.order import OrderModel
from models.tick import TickModel
from providers.horizon_router import HorizonRouterProvider
from services.logging import LoggingService
from services.strategy.handlers.orderbook import OrderbookHandler


class AnalyticService(AnalyticInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _backtest_id: str
    _strategy: str
    _orderbook: OrderbookHandler
    _commands_queue: Queue
    _events_queue: Queue
    _horizon_router: HorizonRouterProvider

    _started: bool
    _started_at: datetime.datetime
    _ended_at: datetime.datetime

    _tick: TickModel
    _allocation: float
    _nav: float
    _nav_peak: float
    _drawdown: float
    _drawdown_peak: float
    _performance: float
    _performance_in_percentage: float
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
        self._strategy = kwargs.get("strategy")
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

        if self._strategy is None:
            raise ValueError("Strategy is required")

        self._started = False
        self._tick = None
        self._allocation = self._orderbook.allocation
        self._nav = self._orderbook.nav
        self._nav_peak = self._nav
        self._drawdown = 0.0
        self._drawdown_peak = 0.0
        self._executed_orders = 0

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_transaction(self, order: OrderModel) -> None:
        if order.status is OrderStatus.OPENED:
            pass

        elif order.status is OrderStatus.CLOSED:
            self._executed_orders += 1
            self._store_order(order)

        elif order.status is OrderStatus.CANCELLED:
            pass

    def on_tick(self, tick: TickModel) -> None:
        self._tick = tick

        if not self._started:
            self._refresh()
            self._store_snapshot(SnapshotEvent.START_SNAPSHOT)
            self._started = True
            self._started_at = self._tick.date

    def on_new_day(self) -> None:
        self._refresh()
        self._store_snapshot(SnapshotEvent.ON_NEW_DAY)

    def on_end(self) -> None:
        self._ended_at = self._tick.date

        self._refresh()
        self._store_snapshot(SnapshotEvent.BACKTEST_END)
        self._update_backtest_to_finished()
        self._report()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _report(self) -> None:
        duration = self._ended_at - self._started_at
        performance_pct = self._performance_in_percentage * 100
        drawdown_pct = self._drawdown_peak * 100

        self._log.info(f"Backtest ID: {self._backtest_id}")
        self._log.info(f"Strategy: {self._strategy}")
        self._log.info(f"Duration: {duration}")
        self._log.info(f"Started at: {self._started_at}")
        self._log.info(f"Ended at: {self._ended_at}")
        self._log.info(f"Executed orders: {self._executed_orders}")
        self._log.info(f"Initial allocation: {self._allocation:.2f}")
        self._log.info(f"Final NAV: {self._nav:.2f}")
        self._log.info(f"Peak NAV: {self._nav_peak:.2f}")
        self._log.info(f"Performance: {performance_pct:.2f}%")
        self._log.info(f"Peak drawdown: {drawdown_pct:.2f}%")

    def _refresh(self) -> None:
        self._nav = self._orderbook.nav
        self._allocation = self._orderbook.allocation
        self._nav_peak = max(self._nav_peak, self._nav)
        self._drawdown = (self._nav - self._nav_peak) / self._nav_peak
        self._performance = (self._nav - self._allocation) / self._allocation
        self._performance_in_percentage = self._performance

        if self._drawdown < 0:
            self._drawdown_peak = min(self._drawdown_peak, self._drawdown)

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
        self._commands_queue.put(
            {
                "command": Command.EXECUTE,
                "function": self._horizon_router.snapshot_create,
                "args": {
                    "body": {
                        "backtest": self._backtest,
                        "backtest_id": self._backtest_id,
                        "source": self._strategy,
                        "event": event.value,
                        "date": int(self._tick.date.timestamp()),
                        "nav": self._nav,
                        "allocation": self._allocation,
                        "nav_peak": self._nav_peak,
                    },
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
