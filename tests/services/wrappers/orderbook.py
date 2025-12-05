"""Orderbook test wrapper module."""

import datetime
import unittest
from typing import List
from unittest.mock import Mock

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_type import OrderType
from models.order import OrderModel
from models.tick import TickModel
from services.orderbook import OrderbookService


class OrderbookWrapper(unittest.TestCase):
    """Base test wrapper for OrderbookService tests."""

    _INITIAL_BALANCE: float = 10000.0
    _DEFAULT_SYMBOL: str = "BTCUSDT"
    _DEFAULT_PRICE: float = 50000.0
    _EPSILON: float = 0.01

    def __init__(self, method_name: str = "runTest") -> None:
        """Initialize test case."""
        super().__init__(method_name)
        self._gateway: Mock = Mock()
        self._transactions: List[OrderModel] = []
        self._orderbook: OrderbookService = None  # type: ignore[assignment]

    def setUp(self) -> None:
        """Set up test fixtures."""
        self._gateway = Mock()
        self._transactions = []
        self._orderbook = self._create_orderbook()

    def _create_orderbook(
        self,
        balance: float = _INITIAL_BALANCE,
        leverage: int = 10,
    ) -> OrderbookService:
        return OrderbookService(
            backtest=True,
            backtest_id="test-orderbook-123",
            allocation=balance,
            balance=balance,
            leverage=leverage,
            gateway=self._gateway,
            on_transaction=self._on_transaction_callback,
        )

    def _on_transaction_callback(self, order: OrderModel) -> None:
        self._transactions.append(order)

    def _create_tick(self, price: float) -> TickModel:
        return TickModel(price=price, date=datetime.datetime.now(tz=TIMEZONE))

    def _create_order(
        self,
        side: OrderSide = OrderSide.BUY,
        price: float = _DEFAULT_PRICE,
        volume: float = 0.01,
        take_profit_price: float = 0.0,
        stop_loss_price: float = 0.0,
    ) -> OrderModel:
        return OrderModel(
            symbol=self._DEFAULT_SYMBOL,
            side=side,
            order_type=OrderType.MARKET,
            price=price,
            volume=volume,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            backtest=True,
            created_at=datetime.datetime.now(tz=TIMEZONE),
            updated_at=datetime.datetime.now(tz=TIMEZONE),
        )

    def _open_position(
        self,
        orderbook: OrderbookService,
        side: OrderSide,
        volume: float,
        price: float,
    ) -> OrderModel:
        tick = self._create_tick(price)
        orderbook.refresh(tick)
        order = self._create_order(side=side, price=price, volume=volume)
        orderbook.open(order)
        return order

    def _assert_accounting_identity(self, orderbook: OrderbookService, identity_name: str) -> None:
        nav = orderbook.nav
        balance = orderbook.balance
        used_margin = orderbook.used_margin
        pnl = orderbook.pnl
        expected_nav = balance + used_margin + pnl
        error_msg = (
            f"{identity_name} failed: NAV={nav:.2f}, Expected={expected_nav:.2f}, "
            f"Balance={balance:.2f}, Used Margin={used_margin:.2f}, PnL={pnl:.2f}"
        )
        assert abs(nav - expected_nav) < self._EPSILON, error_msg
