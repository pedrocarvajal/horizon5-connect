# Code reviewed on 2025-12-02 by Pedro Carvajal

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
    """
    Base test wrapper class for OrderbookService tests.

    Provides common setup and helper methods for testing orderbook
    functionality. Handles test order creation, position management,
    and financial calculation utilities.

    Attributes:
        _INITIAL_BALANCE: Default initial balance for test orderbooks.
        _DEFAULT_SYMBOL: Default trading symbol for test orders.
        _DEFAULT_PRICE: Default price for test orders.
        _EPSILON: Tolerance for floating point comparisons.
        _gateway: Mock gateway service instance.
        _transactions: List of transaction callbacks received.
        _orderbook: OrderbookService instance for testing.
    """

    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _INITIAL_BALANCE: float = 10000.0
    _DEFAULT_SYMBOL: str = "BTCUSDT"
    _DEFAULT_PRICE: float = 50000.0
    _EPSILON: float = 0.01

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _gateway: Mock
    _transactions: List[OrderModel]
    _orderbook: OrderbookService

    # ───────────────────────────────────────────────────────────
    # SETUP
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        """Initialize test wrapper with mock gateway and orderbook service."""
        self._gateway = Mock()
        self._transactions = []
        self._orderbook = self._create_orderbook()

    def _create_orderbook(
        self,
        balance: float = _INITIAL_BALANCE,
        leverage: int = 10,
    ) -> OrderbookService:
        """
        Create OrderbookService instance for testing.

        Args:
            balance: Initial balance for the orderbook.
            leverage: Leverage multiplier for trading.

        Returns:
            Configured OrderbookService instance.
        """
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
        """Callback to track transactions."""
        self._transactions.append(order)

    # ───────────────────────────────────────────────────────────
    # HELPER METHODS
    # ───────────────────────────────────────────────────────────
    def _create_tick(self, price: float) -> TickModel:
        """
        Create a tick model for testing.

        Args:
            price: Price for the tick.

        Returns:
            TickModel instance with current timestamp.
        """
        return TickModel(
            price=price,
            date=datetime.datetime.now(tz=TIMEZONE),
        )

    def _create_order(
        self,
        side: OrderSide = OrderSide.BUY,
        price: float = _DEFAULT_PRICE,
        volume: float = 0.01,
        take_profit_price: float = 0.0,
        stop_loss_price: float = 0.0,
    ) -> OrderModel:
        """
        Create an order model for testing.

        Args:
            side: Order side (BUY or SELL).
            price: Order price.
            volume: Order volume.
            take_profit_price: Take profit price (0 for none).
            stop_loss_price: Stop loss price (0 for none).

        Returns:
            OrderModel instance ready for testing.
        """
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
        """
        Helper to open a position and return the order.

        Args:
            orderbook: OrderbookService instance to use.
            side: Order side (BUY or SELL).
            volume: Order volume.
            price: Order price.

        Returns:
            OrderModel instance for the opened position.
        """
        tick = self._create_tick(price)
        orderbook.refresh(tick)

        order = self._create_order(side=side, price=price, volume=volume)
        orderbook.open(order)
        return order

    def _assert_accounting_identity(
        self,
        orderbook: OrderbookService,
        identity_name: str,
    ) -> None:
        """
        Assert that an accounting identity holds.

        Args:
            orderbook: OrderbookService instance to check.
            identity_name: Name of the identity for error messages.
        """
        nav = orderbook.nav
        balance = orderbook.balance
        used_margin = orderbook.used_margin
        pnl = orderbook.pnl

        expected_nav = balance + used_margin + pnl
        error_msg = (
            f"{identity_name} failed: "
            f"NAV={nav:.2f}, Expected={expected_nav:.2f}, "
            f"Balance={balance:.2f}, Used Margin={used_margin:.2f}, PnL={pnl:.2f}"
        )

        assert abs(nav - expected_nav) < self._EPSILON, error_msg
