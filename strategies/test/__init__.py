"""Test strategy for validating order flow and management."""

import datetime
from typing import Any, ClassVar, Dict

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.enums.tp_sl_method import TpSlMethod
from vendor.helpers.calculate_stop_loss import calculate_stop_loss
from vendor.helpers.calculate_take_profit import calculate_take_profit
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.strategy import StrategyService


class TestStrategy(StrategyService):
    """Simple test strategy to validate order flow.

    Entry Rules:
    - Opens a BUY order every 5 minutes
    - Only 1 order at a time

    Exit Rules:
    - Fixed TP and SL at 0.1%
    - Force close after 5 minutes if not closed by TP/SL
    """

    _SETTINGS: ClassVar[Dict[str, Any]] = {
        "entry_waiting_time": 5,
        "entry_volume": 0.01,
        "take_profit": 0.1,
        "stop_loss": 0.1,
        "force_close_minutes": 5,
        "log_interval_minutes": 1,
    }

    _enabled = True
    _name = "Test"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize test strategy."""
        super().__init__(**kwargs)

        settings = kwargs.get("settings", {})
        self._settings = {**self._SETTINGS, **settings}
        self._last_order_time: datetime.datetime | None = None
        self._last_log_time: datetime.datetime | None = None

    def on_tick(self, tick: TickModel) -> None:
        """Process incoming tick."""
        super().on_tick(tick)
        self._tick = tick
        self._monitor_open_orders()
        self._check_entry_conditions()

    def on_transaction(self, order: OrderModel) -> None:
        """Handle order transaction events."""
        super().on_transaction(order)

        if order.status.is_open():
            self._log.info(
                "Test order opened",
                order_id=order.id,
                price=f"{order.price:.5f}",
                take_profit=f"{order.take_profit_price:.5f}",
                stop_loss=f"{order.stop_loss_price:.5f}",
            )

        if order.status.is_closed():
            profit_percentage = order.profit_percentage * 100
            self._log.info(
                "Test order closed",
                order_id=order.id,
                profit=f"{order.profit:.2f}",
                profit_percentage=f"{profit_percentage:.2f}%",
            )

    def _can_open_new_order(self) -> bool:
        if not self._tick:
            return False

        open_orders = self.orderbook.where(status=OrderStatus.OPEN)
        if len(open_orders) > 0:
            return False

        waiting_time = self._settings.get("entry_waiting_time", 5)

        if not self._last_order_time:
            return True

        time_since_last_order = self._tick.date - self._last_order_time
        minimum_waiting_time = datetime.timedelta(minutes=waiting_time)

        return time_since_last_order >= minimum_waiting_time

    def _check_entry_conditions(self) -> None:
        if not self.is_live:
            return

        if not self._tick:
            return

        if not self._can_open_new_order():
            return

        current_price = self._tick.close_price
        take_profit_value = self._settings.get("take_profit", 0.1)
        stop_loss_value = self._settings.get("stop_loss", 0.1)

        stop_loss_price = calculate_stop_loss(
            entry_price=current_price,
            value=stop_loss_value,
            method=TpSlMethod.PERCENTAGE,
            side=OrderSide.BUY,
        )

        take_profit_price = calculate_take_profit(
            entry_price=current_price,
            value=take_profit_value,
            method=TpSlMethod.PERCENTAGE,
            side=OrderSide.BUY,
        )

        entry_volume = self._settings.get("entry_volume", 0.01)
        volume = entry_volume * 100

        self._log.info(
            "Opening test order",
            price=f"{current_price:.5f}",
            take_profit=f"{take_profit_price:.5f}",
            stop_loss=f"{stop_loss_price:.5f}",
            volume=f"{volume:.2f}",
        )

        self._last_order_time = self._tick.date

        self.open_order(
            OrderSide.BUY,
            current_price,
            take_profit_price,
            stop_loss_price,
            volume,
        )

    def _monitor_open_orders(self) -> None:
        open_orders = self.orderbook.where(status=OrderStatus.OPEN)

        if not self.is_live:
            return

        if not self._tick:
            return

        if len(open_orders) == 0:
            return

        current_time = self._tick.date
        log_interval = self._settings.get("log_interval_minutes", 1)
        force_close_minutes = self._settings.get("force_close_minutes", 5)

        for order in open_orders:
            if not order.created_at:
                continue

            time_since_open = current_time - order.created_at
            minutes_open = time_since_open.total_seconds() / 60
            should_log = (
                not self._last_log_time or (current_time - self._last_log_time).total_seconds() >= log_interval * 60
            )

            if should_log:
                profit_percentage = order.profit_percentage * 100

                self._log.info(
                    "Open order status",
                    order_id=order.id,
                    minutes_open=f"{minutes_open:.1f}",
                    current_price=f"{order.close_price:.5f}",
                    entry_price=f"{order.price:.5f}",
                    profit=f"{order.profit:.2f}",
                    profit_percentage=f"{profit_percentage:.2f}%",
                )

                self._last_log_time = current_time

            if minutes_open >= force_close_minutes:
                profit_percentage = order.profit_percentage * 100

                self._log.info(
                    "Force closing order after time limit",
                    order_id=order.id,
                    minutes_open=f"{minutes_open:.1f}",
                    profit=f"{order.profit:.2f}",
                    profit_percentage=f"{profit_percentage:.2f}%",
                )

                self.orderbook.close(order)
                self._last_log_time = None
