from typing import Any

from enums.order_status import OrderStatus
from interfaces.analytic import AnalyticInterface
from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService
from services.strategy.handlers.orderbook import OrderbookHandler


class AnalyticService(AnalyticInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _orderbook: OrderbookHandler
    _tick: TickModel
    _allocation: float
    _nav: float
    _nav_peak: float
    _drawdown: float
    _drawdown_peak: float
    _performance: float
    _performance_in_percentage: float
    _orders_opened: int
    _orders_closed: int
    _orders_cancelled: int

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("analytic_service")

        self._orderbook = kwargs.get("orderbook")
        self._tick = None
        self._allocation = self._orderbook.allocation
        self._nav = self._orderbook.nav
        self._nav_peak = self._nav
        self._drawdown = 0.0
        self._drawdown_peak = 0.0
        self._orders_opened = 0
        self._orders_closed = 0
        self._orders_cancelled = 0

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_transaction(self, order: OrderModel) -> None:
        if order.status is OrderStatus.OPENED:
            self._orders_opened += 1

        elif order.status is OrderStatus.CLOSED:
            self._orders_closed += 1

        elif order.status is OrderStatus.CANCELLED:
            self._orders_cancelled += 1

    def on_tick(self, tick: TickModel) -> None:
        self._tick = tick

    def on_new_day(self) -> None:
        self._refresh()

    def on_end(self) -> None:
        self._refresh()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _refresh(self) -> None:
        self._nav = self._orderbook.nav
        self._allocation = self._orderbook.allocation
        self._nav_peak = max(self._nav_peak, self._nav)
        self._drawdown = (self._nav - self._nav_peak) / self._nav_peak
        self._performance = (self._nav - self._allocation) / self._allocation
        self._performance_in_percentage = self._performance

        if self._drawdown < 0:
            self._drawdown_peak = min(self._drawdown_peak, self._drawdown)
