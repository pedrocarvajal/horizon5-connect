"""Orderbook service for order lifecycle and portfolio state management."""

import threading
from typing import Callable, Dict, List, Optional, Set

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from interfaces.orderbook import OrderbookInterface
from models.order import OrderModel
from models.tick import TickModel
from services.gateway import GatewayService
from services.logging import LoggingService

from .gateway import GatewayHandlerService

MARGIN_LIQUIDATION_RATIO: float = 0.001
MARGIN_RECOVERY_RATIO: float = 0.05


class OrderbookService(OrderbookInterface):
    """
    Service for managing order book operations and portfolio state.

    This service manages the lifecycle of orders, tracks portfolio state
    (balance, margin, exposure), enforces risk management rules (margin calls,
    stop loss, take profit), and coordinates with the gateway handler for
    production order execution.

    The service performs:
    - Order lifecycle management (open, close, refresh)
    - Margin and balance tracking with leverage support
    - Risk management (margin calls, liquidation prevention)
    - Stop loss and take profit enforcement
    - Integration with gateway handler for production trading

    Attributes:
        _backtest: Whether running in backtest mode.
        _backtest_id: Optional backtest identifier.
        _allocation: Initial capital allocation.
        _balance: Current available balance.
        _leverage: Leverage multiplier for trading.
        _nav: Net asset value.
        _exposure: Total exposure across open positions.
        _orders: Dictionary of orders by order ID.
        _tick: Current market tick data.
        _on_transaction: Callback function called on order status changes.
        _margin_call_active: Whether a margin call is currently active.
        _gateway_handler: Handler service for gateway operations.
        _log: Logging service instance for logging operations.
    """

    _backtest: bool
    _backtest_id: Optional[str]
    _allocation: float
    _balance: float
    _leverage: int
    _nav: float
    _exposure: float
    _orders: Dict[str, OrderModel]
    _open_orders_index: Set[str]
    _tick: Optional[TickModel]
    _on_transaction: Callable[[OrderModel], None]
    _margin_call_active: bool
    _gateway_handler: GatewayHandlerService
    _log: LoggingService
    _balance_lock: threading.Lock
    _orders_lock: threading.Lock

    def __init__(
        self,
        backtest: bool,
        backtest_id: Optional[str],
        allocation: float,
        balance: float,
        leverage: int,
        gateway: GatewayService,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        """
        Initialize the orderbook service.

        Args:
            backtest: Whether running in backtest mode.
            backtest_id: Optional backtest identifier.
            allocation: Initial capital allocation.
            balance: Initial available balance.
            leverage: Leverage multiplier for trading.
            gateway: Gateway service instance for trading operations.
            on_transaction: Callback function called on order status changes.
        """
        self._log = LoggingService()
        self._log.setup("orderbook_service")

        self._backtest = backtest
        self._backtest_id = backtest_id
        self._allocation = allocation
        self._balance = balance
        self._orders = {}
        self._open_orders_index = set()
        self._leverage = leverage if leverage > 0 else 1
        self._nav = 0.0
        self._exposure = 0.0
        self._on_transaction = on_transaction
        self._margin_call_active = False
        self._tick = None
        self._balance_lock = threading.Lock()
        self._orders_lock = threading.Lock()

        self._gateway_handler = GatewayHandlerService(
            gateway=gateway,
            backtest=backtest,
            backtest_id=backtest_id,
        )

    def _cancel_order(self, order: OrderModel, reason: str) -> None:
        """
        Cancel an order and record it in the orderbook.

        Args:
            order: OrderModel instance to cancel.
            reason: Reason for cancellation (for logging).
        """
        self._log.error(reason)
        order.status = OrderStatus.CANCELLED
        order.executed_volume = 0

        with self._orders_lock:
            self._orders[order.id] = order

        self._on_transaction(order)

    def refresh(self, tick: TickModel) -> None:
        """
        Refresh orderbook state with new market tick.

        Updates current tick, checks for margin calls, updates order prices,
        and evaluates stop loss/take profit conditions for all open orders.

        Args:
            tick: Current market tick data.
        """
        self._tick = tick

        if self.used_margin > 0 and self.margin_level < MARGIN_LIQUIDATION_RATIO:
            if not self._margin_call_active:
                self._margin_call_active = True
                self._log.critical("Margin call triggered: closing all orders and blocking new operations.")

            with self._orders_lock:
                open_order_ids = list(self._open_orders_index)

            for order_id in open_order_ids:
                order = self._orders[order_id]
                self._log.warning(f"Closing order {order.id}.")
                self.close(order)

        if self._margin_call_active and self.margin_level > MARGIN_RECOVERY_RATIO:
            self._margin_call_active = False
            self._log.info(
                f"Margin call resolved: margin level recovered to {self.margin_level:.2f}. New operations allowed."
            )

        with self._orders_lock:
            open_order_ids = list(self._open_orders_index)

        for order_id in open_order_ids:
            order = self._orders[order_id]
            order.close_price = tick.price
            order.updated_at = tick.date

            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                with self._orders_lock:
                    self._orders[order.id].status = OrderStatus.CLOSING
                self.close(order)

    def clean(self) -> None:
        """
        Remove closed orders from the orderbook.

        Removes orders with CLOSED status from the internal orders dictionary
        and ensures the open orders index is synchronized.
        This helps maintain a clean orderbook and reduces memory usage.
        """
        with self._orders_lock:
            for order_id in list(self._orders.keys()):
                if self._orders[order_id].status in [
                    OrderStatus.CLOSED,
                ]:
                    del self._orders[order_id]
                    self._open_orders_index.discard(order_id)

    def open(self, order: OrderModel) -> None:
        """
        Open a new order.

        Validates margin requirements, checks for margin calls, and opens the
        order if conditions are met. In production mode, delegates execution
        to the gateway handler.

        Args:
            order: OrderModel instance containing order details.
        """
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

        if not self._backtest:
            gateway_success = self._gateway_handler.open_order(order)

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

    def close(self, order: OrderModel) -> None:
        """
        Close an existing order.

        Handles three scenarios based on order execution status:
        1. Not executed (executed_volume = 0): Cancels the order entirely.
        2. Partially executed (0 < executed_volume < volume): Cancels the
           unfilled portion and closes the executed portion.
        3. Fully executed (executed_volume = volume): Closes the order normally.

        Updates order status to CLOSED, returns margin to balance, and applies
        profit/loss. In production mode, delegates execution to the gateway handler.

        Args:
            order: OrderModel instance representing the order to close.
        """
        if self._tick is None:
            self._log.error("Tick must be set before closing orders.")
            return

        if order.executed_volume == 0:
            self._log.info(f"Order {order.id} not executed, cancelling instead of closing")
            self.cancel(order)
            return

        if order.executed_volume < order.volume:
            unexecuted_volume = order.volume - order.executed_volume
            margin_to_free = (unexecuted_volume * order.price) / self._leverage

            msg = f"Order {order.id} partially filled: {order.executed_volume}/{order.volume}."
            self._log.info(f"{msg} Cancelling unfilled portion and closing executed portion.")

            if not self._backtest:
                cancel_success = self._gateway_handler.cancel_order(order)

                if not cancel_success:
                    msg = f"Failed to cancel unfilled portion of order {order.id}."
                    self._log.warning(f"{msg} Proceeding to close executed portion anyway.")

            with self._balance_lock:
                self._balance += margin_to_free

            order.volume = order.executed_volume

        margin_used = (order.executed_volume * order.price) / self._leverage
        profit = order.profit

        order.status = OrderStatus.CLOSED
        order.close_price = self._tick.price
        order.updated_at = self._tick.date

        with self._balance_lock:
            self._balance += margin_used
            self._balance += profit

            with self._orders_lock:
                self._orders[order.id] = order
                self._open_orders_index.discard(order.id)

        if not self._backtest:
            gateway_success = self._gateway_handler.close_order(order)

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

    def cancel(self, order: OrderModel) -> None:
        """
        Cancel an existing order.

        Cancels a pending or open order, releasing the reserved margin back
        to the balance. In production mode, delegates execution to the gateway
        handler to cancel the order on the exchange.

        Args:
            order: OrderModel instance representing the order to cancel.
        """
        if self._tick is None:
            self._log.error("Tick must be set before cancelling orders.")
            return

        if not (order.status.is_opening() or order.status.is_open()):
            msg = f"Order {order.id} cannot be cancelled in status {order.status.value}."
            self._log.error(f"{msg} Only OPENING or OPEN orders can be cancelled.")
            return

        margin_to_release = (order.volume * order.price) / self._leverage

        with self._balance_lock, self._orders_lock:
            if order.id not in self._orders:
                self._log.error(f"Order {order.id} not found in orderbook")
                return

            if not self._backtest:
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

    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        """
        Filter orders by side and/or status.

        Args:
            side: Optional order side to filter by (BUY or SELL).
            status: Optional order status to filter by.

        Returns:
            List of orders matching the filter criteria.
        """
        with self._orders_lock:
            return [
                order
                for order in self._orders.values()
                if (side is None or order.side == side) and (status is None or order.status == status)
            ]

    @property
    def orders(self) -> List[OrderModel]:
        """Return all orders in the orderbook."""
        with self._orders_lock:
            return list(self._orders.values())

    @property
    def balance(self) -> float:
        """Return current cash balance."""
        return self._balance

    @property
    def allocation(self) -> float:
        """Return strategy allocation percentage."""
        return self._allocation

    @property
    def nav(self) -> float:
        """Return net asset value (balance + used margin + unrealized PnL)."""
        return self._balance + self.used_margin + self.pnl

    @property
    def exposure(self) -> float:
        """Return total market exposure from open positions."""
        with self._orders_lock:
            return sum(
                (order.volume * order.price)
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )

    @property
    def pnl(self) -> float:
        """Return unrealized profit and loss from open positions."""
        with self._orders_lock:
            return sum(
                order.profit
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )

    @property
    def free_margin(self) -> float:
        """Return available margin for new positions."""
        return self.equity - self.used_margin

    @property
    def used_margin(self) -> float:
        """Return margin currently used by open positions."""
        with self._orders_lock:
            return sum(
                (order.volume * order.price) / self._leverage
                for order_id in self._open_orders_index
                if (order := self._orders.get(order_id)) is not None
            )

    @property
    def equity(self) -> float:
        """Calculate account equity as balance plus unrealized PnL."""
        return self._balance + self.pnl

    @property
    def margin_level(self) -> float:
        """Return margin level as ratio of equity to used margin."""
        if self.used_margin == 0:
            return float("inf")

        return self.equity / self.used_margin
