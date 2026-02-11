"""Orderbook service for managing order lifecycle and margin."""

import datetime
import threading
from typing import Callable, Dict, List, Optional

from vendor.enums.order_side import OrderSide
from vendor.enums.order_status import OrderStatus
from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.gateway import GatewayInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.interfaces.orderbook import OrderbookInterface
from vendor.models.order import OrderModel
from vendor.models.tick import TickModel
from vendor.services.gateway.models.gateway_account import GatewayAccountModel
from vendor.services.logging import LoggingService
from vendor.services.orderbook.models import OrderSyncResult

from .gateway import GatewayHandlerService

MARGIN_LIQUIDATION_RATIO: float = 0.001
MARGIN_RECOVERY_RATIO: float = 0.05
SYNC_INTERVAL_SECONDS: int = 60


class OrderbookService(OrderbookInterface):
    """Manage order lifecycle, margin, and gateway synchronization."""

    _backtest_id: Optional[str]
    _nav: float
    _exposure: float
    _tick: Optional[TickModel]
    _on_transaction: Callable[[OrderModel], None]
    _log: LoggingInterface
    _balance_lock: threading.Lock
    _orders_lock: threading.Lock
    _last_sync_time: Optional[datetime.datetime]

    def __init__(
        self,
        backtest_id: Optional[str],
        asset: AssetInterface,
        account: GatewayAccountModel,
        gateway: GatewayInterface,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        """Initialize orderbook with asset allocation and gateway handler."""
        self._log = LoggingService()

        self._backtest_id = backtest_id
        self._balance = asset.allocation
        self._orders = {}
        self._open_orders_index = set()
        self._leverage = account.leverage
        self._nav = 0.0
        self._exposure = 0.0
        self._on_transaction = on_transaction
        self._margin_call_active = False
        self._tick = None
        self._balance_lock = threading.Lock()
        self._orders_lock = threading.Lock()
        self._last_sync_time = None

        self._gateway_handler = GatewayHandlerService(
            gateway=gateway,
            backtest_id=backtest_id,
        )

    def cancel(self, order: OrderModel) -> None:
        """Cancel an opening or open order and release its margin."""
        if self._tick is None:
            self._log.error("Tick must be set before cancelling orders.")
            return

        if not (order.status.is_opening() or order.status.is_open()):
            self._log.error(
                "Order cannot be cancelled",
                order_id=order.id,
                status=order.status.value,
                reason="Only OPENING or OPEN orders can be cancelled",
            )
            return

        margin_to_release = (order.volume * order.price) / self._leverage

        with self._balance_lock, self._orders_lock:
            if order.id not in self._orders:
                self._log.error(
                    "Order not found in orderbook",
                    order_id=order.id,
                )
                return

            if not self.is_backtest:
                gateway_success = self._gateway_handler.cancel_order(order)

                if not gateway_success:
                    self._log.critical(
                        f"Failed to cancel order {order.id} on gateway. Order remains {order.status.value}."
                    )
                    return

            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0
            order.updated_at = self._tick.date

            self._balance += margin_to_release
            self._orders[order.id] = order
            self._open_orders_index.discard(order.id)

        self._on_transaction(order)

    def clean(self) -> None:
        """Remove closed orders from the orderbook."""
        with self._orders_lock:
            for order_id in list(self._orders.keys()):
                if self._orders[order_id].status in [
                    OrderStatus.CLOSED,
                ]:
                    del self._orders[order_id]
                    self._open_orders_index.discard(order_id)

    def close(self, order: OrderModel) -> None:
        """Close an order, settle profit, and release margin."""
        if self._tick is None:
            self._log.error("Tick must be set before closing orders.")
            return

        if order.status.is_closed():
            return

        if order.executed_volume == 0:
            self._log.info(
                "Order not executed, cancelling instead of closing",
                order_id=order.id,
            )
            self.cancel(order)
            return

        if order.executed_volume < order.volume:
            unexecuted_volume = order.volume - order.executed_volume
            margin_to_free = (unexecuted_volume * order.price) / self._leverage

            self._log.info(
                "Order partially filled, cancelling unfilled portion",
                order_id=order.id,
                executed=order.executed_volume,
                total=order.volume,
            )

            if not self.is_backtest:
                cancel_success = self._gateway_handler.cancel_order(order)

                if not cancel_success:
                    self._log.warning(
                        "Failed to cancel unfilled portion, proceeding to close anyway",
                        order_id=order.id,
                    )

            with self._balance_lock:
                self._balance += margin_to_free

            order.volume = order.executed_volume

        margin_used = (order.executed_volume * order.price) / self._leverage
        profit = order.profit

        order.status = OrderStatus.CLOSED
        order.close_price = self._tick.close_price
        order.updated_at = self._tick.date

        with self._balance_lock:
            self._balance += margin_used
            self._balance += profit

            with self._orders_lock:
                self._orders[order.id] = order
                self._open_orders_index.discard(order.id)

        if not self.is_backtest:
            gateway_success = self._gateway_handler.close_position(order)

            if not gateway_success:
                with self._balance_lock:
                    self._balance -= margin_used
                    self._balance -= profit

                    with self._orders_lock:
                        self._open_orders_index.add(order.id)

                order.status = OrderStatus.OPEN

                self._log.critical(
                    f"Failed to close order {order.id} on gateway. Reverted balance changes. Order remains OPEN."
                )
                return

        self._on_transaction(order)

    def open(self, order: OrderModel) -> None:
        """Open an order after validating margin requirements."""
        if self._tick is None:
            self._log.error("Tick must be set before opening orders.")
            return

        required_margin = (order.volume * order.price) / self._leverage

        if self._margin_call_active:
            self._cancel_order(
                order,
                "Margin call active: cannot open new orders until margin level recovers.",
            )
            return

        if self._balance <= 0:
            self._cancel_order(order, "Balance is less than 0, cannot open order.")
            return

        with self._balance_lock:
            if self.free_margin < required_margin:
                error_msg = (
                    f"Strategy: {order.strategy_id} "
                    f"Free margin is less than required margin, cannot open order. "
                    f"Volume: {order.volume:.2f} | Price: {order.price:.2f} | "
                    f"Required margin: {required_margin:.2f} | "
                    f"Free margin: {self.free_margin:.2f}"
                )

                self._cancel_order(order, error_msg)
                return

            projected_used_margin = self.used_margin + required_margin
            projected_balance = self._balance - required_margin
            projected_equity = projected_balance + self.pnl

            if projected_used_margin > 0:
                projected_margin_level = projected_equity / projected_used_margin
            else:
                projected_margin_level = float("inf")

            if projected_margin_level < MARGIN_LIQUIDATION_RATIO:
                error_msg = (
                    f"Projected margin level ({projected_margin_level:.2f}) "
                    f"would be below liquidation ratio ({MARGIN_LIQUIDATION_RATIO}). "
                    f"Cannot open order."
                )
                self._cancel_order(order, error_msg)
                return

            order.status = OrderStatus.OPEN
            order.executed_volume = order.volume
            order.close_price = order.price
            order.updated_at = self._tick.date

            self._balance -= required_margin

            with self._orders_lock:
                self._orders[order.id] = order
                self._open_orders_index.add(order.id)

        if not self.is_backtest:
            gateway_success = self._gateway_handler.place_order(order)

            if not gateway_success:
                with self._balance_lock:
                    self._balance += required_margin

                    with self._orders_lock:
                        self._open_orders_index.discard(order.id)

                order.status = OrderStatus.CANCELLED
                order.executed_volume = 0

                self._log.critical(
                    f"Failed to open order {order.id} on gateway. Reverted balance change: +{required_margin:.2f}"
                )
                return

        self._on_transaction(order)

    def refresh(self, tick: TickModel) -> None:
        """Update tick, check margin levels, and sync open orders."""
        self._tick = tick

        if self.used_margin > 0 and self.margin_level < MARGIN_LIQUIDATION_RATIO:
            if not self._margin_call_active:
                self._margin_call_active = True
                self._log.critical("Margin call triggered: closing all orders and blocking new operations.")

            with self._orders_lock:
                open_order_ids = list(self._open_orders_index)

            for order_id in open_order_ids:
                order = self._orders[order_id]
                self._log.warning(
                    "Closing order due to margin call",
                    order_id=order.id,
                )
                self.close(order)

        if self._margin_call_active and self.margin_level > MARGIN_RECOVERY_RATIO:
            self._margin_call_active = False
            self._log.info(
                "Margin call resolved, new operations allowed",
                margin_level=f"{self.margin_level:.2f}",
            )

        self._sync_orders()

        with self._orders_lock:
            open_order_ids = list(self._open_orders_index)

        for order_id in open_order_ids:
            order = self._orders[order_id]
            order.close_price = tick.close_price
            order.updated_at = tick.date

            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                with self._orders_lock:
                    self._orders[order.id].status = OrderStatus.CLOSING

                self.close(order)

    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        """Filter orders by side and status."""
        with self._orders_lock:
            return [
                order
                for order in self._orders.values()
                if (side is None or order.side == side) and (status is None or order.status == status)
            ]

    def _cancel_order(self, order: OrderModel, reason: str) -> None:
        self._log.error(reason)
        order.status = OrderStatus.CANCELLED
        order.executed_volume = 0

        with self._orders_lock:
            self._orders[order.id] = order

        self._on_transaction(order)

    def _sync_orders(self) -> None:
        if self.is_backtest:
            return

        if self._tick is None:
            return

        current_time = self._tick.date

        if self._last_sync_time is not None:
            elapsed = (current_time - self._last_sync_time).total_seconds()

            if elapsed < SYNC_INTERVAL_SECONDS:
                return

        self._last_sync_time = current_time

        with self._orders_lock:
            open_orders: Dict[str, OrderModel] = {
                order_id: self._orders[order_id]
                for order_id in self._open_orders_index
                if order_id in self._orders and self._orders[order_id].status.is_open()
            }

        if not open_orders:
            return

        update_results = self._gateway_handler.sync_orders(open_orders)

        for order_id, result in update_results.items():
            self._process_order_update(order_id, result)

    def _process_order_update(
        self,
        order_id: str,
        result: OrderSyncResult,
    ) -> None:
        with self._orders_lock:
            if order_id not in self._orders:
                return

            order = self._orders[order_id]

        if not order.status.is_open():
            return

        if result.exists:
            return

        margin_used = (order.executed_volume * order.price) / self._leverage

        order.status = result.status
        order.close_price = result.close_price

        if self._tick:
            order.updated_at = self._tick.date

        with self._balance_lock:
            self._balance += margin_used
            self._balance += result.profit

            with self._orders_lock:
                self._orders[order.id] = order
                self._open_orders_index.discard(order.id)

        self._log.info(
            "Order closed due to external intervention",
            order_id=order.id,
            close_price=result.close_price,
            profit=result.profit,
        )

        self._on_transaction(order)

    @property
    def exposure(self) -> float:
        """Return total notional exposure of open orders."""
        with self._orders_lock:
            return sum(
                (order.volume * order.price)
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )

    @property
    def nav(self) -> float:
        """Return net asset value (balance + used margin + unrealized PnL)."""
        return self._balance + self.used_margin + self.pnl

    @property
    def orders(self) -> List[OrderModel]:
        """Return all orders in the orderbook."""
        with self._orders_lock:
            return list(self._orders.values())

    @property
    def pnl(self) -> float:
        """Return total unrealized profit/loss of open orders."""
        with self._orders_lock:
            return sum(
                order.profit
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )

    @property
    def used_margin(self) -> float:
        """Return total margin used by open orders."""
        with self._orders_lock:
            return sum(
                (order.volume * order.price) / self._leverage
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )
