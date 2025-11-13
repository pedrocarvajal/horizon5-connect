from typing import Callable, Dict, List, Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from models.order import OrderModel
from models.tick import TickModel
from services.gateway import GatewayService
from services.logging import LoggingService


class OrderbookHandler:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _backtest: bool
    _backtest_id: str
    _allocation: float
    _balance: float
    _leverage: int
    _gateway: GatewayService
    _nav: float
    _exposure: float
    _orders: Dict[str, OrderModel]
    _tick: TickModel
    _on_transaction: Callable[[OrderModel], None]
    _margin_call_active: bool

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        backtest: bool,
        backtest_id: str,
        allocation: float,
        balance: float,
        leverage: int,
        gateway: GatewayService,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._backtest = backtest
        self._backtest_id = backtest_id
        self._allocation = allocation
        self._balance = balance
        self._orders = {}
        self._leverage = leverage if leverage > 0 else 1
        self._tick = None
        self._gateway = gateway
        self._nav = 0.0
        self._exposure = 0.0
        self._on_transaction = on_transaction
        self._margin_call_active = False

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def refresh(self, tick: TickModel) -> None:
        self._tick = tick
        margin_liquidation_ratio = 0.001
        margin_recovery_ratio = 0.05

        if self.used_margin > 0 and self.margin_level < margin_liquidation_ratio:
            if not self._margin_call_active:
                self._margin_call_active = True
                self._log.critical(
                    "Margin call triggered: closing all orders and blocking new operations."
                )

            for order in list(self._orders.values()):
                if order.status is OrderStatus.OPENED:
                    self._log.warning(f"Closing order {order.id}.")
                    self.close(order)

        if self._margin_call_active and self.margin_level > margin_recovery_ratio:
            self._margin_call_active = False
            self._log.info(
                f"Margin call resolved: margin level recovered to {self.margin_level:.2f}. "
                f"New operations allowed."
            )

        for order in list(self._orders.values()):
            order.close_price = tick.price
            order.updated_at = tick.date

            ready_to_close_take_profit = order.check_if_ready_to_close_take_profit(tick)
            ready_to_close_stop_loss = order.check_if_ready_to_close_stop_loss(tick)

            if ready_to_close_take_profit or ready_to_close_stop_loss:
                self._orders[order.id].status = OrderStatus.CLOSING
                self.close(order)

    def clean(self) -> None:
        for order_id in list(self._orders.keys()):
            if self._orders[order_id].status in [
                OrderStatus.CLOSED,
            ]:
                del self._orders[order_id]

    def open(self, order: OrderModel) -> None:
        required_margin = (order.volume * order.price) / self._leverage
        margin_liquidation_ratio = 0.001

        if self._margin_call_active:
            self._log.error(
                "Margin call active: cannot open new orders until margin level recovers."
            )
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        if self._balance <= 0:
            self._log.error("Balance is less than 0, cannot open order.")
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        if self.free_margin < required_margin:
            self._log.error("Free margin is less than required margin, cannot open order.")
            self._log.error(
                f"Volume: {order.volume:.2f} | Price: {order.price:.2f} | "
                f"Required margin: {required_margin:.2f} | "
                f"Free margin: {self.free_margin:.2f}"
            )

            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        projected_used_margin = self.used_margin + required_margin
        projected_balance = self._balance - required_margin
        projected_equity = projected_balance + self.pnl
        projected_margin_level = (
            projected_equity / projected_used_margin
            if projected_used_margin > 0
            else float("inf")
        )

        if projected_margin_level < margin_liquidation_ratio:
            self._log.error(
                f"Projected margin level ({projected_margin_level:.2f}) "
                f"would be below liquidation ratio ({margin_liquidation_ratio}). "
                f"Cannot open order."
            )
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        order.status = OrderStatus.OPENED
        order.executed_volume = order.volume
        order.close_price = order.price
        order.updated_at = self._tick.date

        self._balance -= required_margin
        self._orders[order.id] = order
        self._on_transaction(order)

    def close(self, order: OrderModel) -> None:
        order.status = OrderStatus.CLOSED
        order.close_price = self._tick.price
        order.updated_at = self._tick.date

        if order.status is OrderStatus.CLOSED:
            margin_used = (order.volume * order.price) / self._leverage

            self._balance += margin_used
            self._balance += order.profit

        if order.status is OrderStatus.CANCELLED:
            self._log.error(f"Order {order.id} was cancelled trying to close.")

        self._orders[order.id] = order
        self._on_transaction(order)

    def where(
        self,
        side: Optional[OrderSide] = None,
        status: Optional[OrderStatus] = None,
    ) -> List[OrderModel]:
        return [
            order
            for order in self._orders.values()
            if (side is None or order.side == side)
            and (status is None or order.status == status)
        ]

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _log_before_open(self) -> None:
        self._log.info(
            f"Before open → "
            f"Balance: {self.balance:.2f} | "
            f"NAV: {self.nav:.2f} | "
            f"Free margin: {self.free_margin:.2f} | "
            f"Margin level: {self.margin_level:.2f}"
        )

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def orders(self) -> List[OrderModel]:
        return list(self._orders.values())

    @property
    def balance(self) -> float:
        return self._balance

    @property
    def allocation(self) -> float:
        return self._allocation

    @property
    def nav(self) -> float:
        return self._balance + self.used_margin + self.pnl

    @property
    def exposure(self) -> float:
        return sum(
            (order.volume * order.price)
            for order in self._orders.values()
            if order.status == OrderStatus.OPENED
        )

    @property
    def pnl(self) -> float:
        return sum(
            order.profit
            for order in self._orders.values()
            if order.status == OrderStatus.OPENED
        )

    @property
    def free_margin(self) -> float:
        return self.equity - self.used_margin

    @property
    def used_margin(self) -> float:
        return sum(
            (order.volume * order.price) / self._leverage
            for order in self._orders.values()
            if order.status == OrderStatus.OPENED
        )

    @property
    def equity(self) -> float:
        return self._balance + self.pnl

    @property
    def margin_level(self) -> float:
        if self.used_margin == 0:
            return float("inf")

        return self.equity / self.used_margin
