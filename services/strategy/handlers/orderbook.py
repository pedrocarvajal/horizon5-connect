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
    _allocation: float
    _balance: float
    _leverage: int
    _gateway: GatewayService
    _nav: float
    _exposure: float
    _orders: Dict[str, OrderModel]
    _tick: TickModel
    _on_transaction: Callable[[OrderModel], None]

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        allocation: float,
        balance: float,
        leverage: int,
        gateway: GatewayService,
        on_transaction: Callable[[OrderModel], None],
    ) -> None:
        self._log = LoggingService()
        self._log.setup("orderbook_handler")

        self._allocation = allocation
        self._balance = balance
        self._orders = {}
        self._leverage = leverage if leverage > 0 else 1
        self._tick = None
        self._gateway = gateway
        self._nav = 0.0
        self._exposure = 0.0
        self._on_transaction = on_transaction

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def refresh(self, tick: TickModel) -> None:
        self._tick = tick
        margin_liquidation_ratio = self._gateway.configs.get(
            "margin_liquidation_ratio", 0.2
        )

        if self._used_margin > 0 and self.margin_level < margin_liquidation_ratio:
            self._log.critical("Margin level is less than 20, closing all orders.")

            for order in list(self._orders.values()):
                if order.status is OrderStatus.OPENED:
                    self.close(order)

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

        if self._balance <= 0:
            self._log.error("Balance is less than 0, cannot open order.")
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        if self.free_margin < required_margin:
            self._log.error("Free margin is less than required margin, cannot open order.")
            order.status = OrderStatus.CANCELLED
            order.executed_volume = 0

            self._orders[order.id] = order
            self._on_transaction(order)
            return

        order.status = OrderStatus.OPENED
        order.executed_volume = order.volume
        order.updated_at = self._tick.date
        order.open()

        self._balance -= required_margin
        self._orders[order.id] = order
        self._on_transaction(order)

    def close(self, order: OrderModel) -> None:
        order.status = OrderStatus.CLOSED
        order.close_price = self._tick.price
        order.updated_at = self._tick.date
        order.close()

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
        return self._balance + self.exposure + self.pnl

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
