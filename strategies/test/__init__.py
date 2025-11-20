# Code reviewed on 2025-01-27 by Pedro Carvajal

import datetime
from typing import Any, Dict, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel
from services.logging import LoggingService
from services.strategy import StrategyService


class TestStrategy(StrategyService):
    """
    Test trading strategy for validation and demonstration purposes.

    Entry Rules:
    - Opens a new BUY order every N minutes (configurable via interval_minutes setting)
    - Only opens orders in live mode (not during backtest or historical filling)

    Exit Rules:
    - Take profit: Configurable percentage above entry price (default: 2%)
    - Stop loss: Configurable percentage below entry price (default: 1%)

    Special Conditions:
    - Closes any existing open orders before opening a new one
    - Order volume calculated as percentage of NAV (configurable, default: 1%)
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    # Mandatory variables (from StrategyService base class)
    _enabled = True
    _name = "Test"

    # Class variables
    _settings: Dict[str, Any]
    _tick: Optional[TickModel]
    _last_order_time: Optional[datetime.datetime] = None

    # Dependency injections
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._log = LoggingService()
        self._log.setup("test_strategy")

        self._settings = kwargs.get(
            "settings",
            {
                "volume_percentage": 0.01,
                "take_profit_percentage": 0.02,
                "stop_loss_percentage": 0.01,
                "interval_minutes": 10,
            },
        )
        self._tick = None

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
        self._tick = tick

    def on_new_minute(self) -> None:
        super().on_new_minute()
        self._check_and_open_order()

    def on_transaction(self, order: OrderModel) -> None:
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(f"Order: {order.id}, was opened.")
            if self._tick:
                self._last_order_time = self._tick.date

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100
            profit = order.profit
            self._log.info(f"Order: {order.id}, was closed, with profit: {profit:.2f} ({profit_percentage:.2f}%).")

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _check_and_open_order(self) -> None:
        """
        Check if conditions are met to open a new order and open it.

        Validates that enough time has passed since the last order,
        closes any existing open orders, calculates order parameters,
        and opens a new BUY order.
        """
        if not self._tick:
            return

        if not self._should_open_new_order():
            return

        if not self.is_live:
            return

        self._close_existing_orders()

        current_price = self._tick.price
        take_profit_price, stop_loss_price = self._calculate_order_prices(current_price)
        volume = self._calculate_order_volume(current_price)

        self._log.info(f"Opening new order at price: {current_price}")
        self.open_order(
            OrderSide.BUY,
            current_price,
            take_profit_price,
            stop_loss_price,
            volume,
        )

    def _should_open_new_order(self) -> bool:
        """
        Check if enough time has passed since the last order to open a new one.

        Returns:
            True if enough time has passed, False otherwise.
        """
        if not self._tick:
            return False

        interval_minutes = self._settings.get("interval_minutes", 10)
        current_time = self._tick.date

        if self._last_order_time is None:
            self._last_order_time = current_time - datetime.timedelta(minutes=interval_minutes)

        time_since_last_order = current_time - self._last_order_time
        interval_seconds = interval_minutes * 60

        return time_since_last_order.total_seconds() >= interval_seconds

    def _close_existing_orders(self) -> None:
        """
        Close all existing open orders.

        Iterates through all open orders in the orderbook and closes them,
        logging each closure.
        """
        open_orders = self.orderbook.where(status=OrderStatus.OPEN)

        for order in open_orders:
            self._log.info(f"Closing existing order: {order.id}")
            self.orderbook.close(order)

    def _calculate_order_prices(
        self,
        current_price: float,
    ) -> tuple[float, float]:
        """
        Calculate take profit and stop loss prices based on current price and settings.

        Args:
            current_price: The current market price.

        Returns:
            Tuple containing (take_profit_price, stop_loss_price).
        """
        take_profit_percentage = self._settings.get("take_profit_percentage", 0.02)
        stop_loss_percentage = self._settings.get("stop_loss_percentage", 0.01)

        take_profit_price = current_price + (current_price * take_profit_percentage)
        stop_loss_price = current_price - (current_price * stop_loss_percentage)

        return take_profit_price, stop_loss_price

    def _calculate_order_volume(self, current_price: float) -> float:
        """
        Calculate order volume based on NAV and volume percentage setting.

        Args:
            current_price: The current market price.

        Returns:
            The calculated order volume.
        """
        volume_percentage = self._settings.get("volume_percentage", 0.01)
        return (self.nav / current_price) * volume_percentage
