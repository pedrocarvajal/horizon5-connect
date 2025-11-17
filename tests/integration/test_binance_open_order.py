# Last coding review: 2025-11-17 17:36:36
import unittest
from typing import Optional

from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from services.gateway import GatewayService
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.logging import LoggingService


class TestBinanceOpenOrder(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "btcusdt"
    _DEFAULT_LEVERAGE: int = 5

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _log: LoggingService
    _gateway: GatewayService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name="test_binance_open_order")
        self._gateway = self._create_gateway()
        self._setup_leverage()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def test_open_market_order_and_close(self) -> None:
        volume = 0.002
        account_before = self._gateway.account()

        order = self._open_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            volume=volume,
        )

        if self._is_order_executed(order=order, account_before=account_before):
            self._close_position(order=order)
        else:
            self._cancel_order(order=order, account_before=account_before)

        self._verify_account_clean()

    def test_open_limit_order_and_cancel(self) -> None:
        limit_price = self._calculate_safe_limit_price()
        volume = self._calculate_min_volume_for_notional(price=limit_price, min_notional=100.0)

        order = self._open_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            volume=volume,
            price=limit_price,
        )

        cancelled_order = self._cancel_order(order=order, account_before=None)
        self._assert_cancelled_order(cancelled_order=cancelled_order, original_order=order)
        self._verify_account_clean()

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _create_gateway(self) -> GatewayService:
        return GatewayService(
            gateway="binance",
            futures=True,
        )

    def _setup_leverage(self) -> None:
        leverage_set = self._gateway.set_leverage(
            symbol=self._SYMBOL,
            leverage=self._DEFAULT_LEVERAGE,
        )
        assert leverage_set, "Leverage should be set successfully"

    def _open_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
    ) -> GatewayOrderModel:
        order = self._gateway.open(
            symbol=symbol,
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
        )

        if order is None:
            if order_type == OrderType.LIMIT:
                self.fail("LIMIT order should be created. Check order parameters and API connection.")
            else:
                self.skipTest("Order not available for testing. Check account balance and margin requirements.")

        self._assert_order_valid(order=order, side=side, order_type=order_type, volume=volume, price=price)
        return order

    def _assert_order_valid(
        self,
        order: GatewayOrderModel,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
    ) -> None:
        assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
        assert order.symbol == self._SYMBOL.upper(), "Symbol should match"
        assert order.side == side, f"Side should be {side.value}"
        assert order.order_type == order_type, f"Order type should be {order_type.value}"
        assert order.volume == volume, f"Volume should be {volume}"
        assert order.status is not None, "Status should be set"

        if price is not None:
            assert order.price == price, f"Price should be {price}"

    def _is_order_executed(
        self,
        order: GatewayOrderModel,
        account_before: Optional[GatewayAccountModel],
    ) -> bool:
        if order.status == OrderStatus.OPENED:
            return True

        account_after = self._gateway.account()

        if account_before and account_after:
            return account_after.margin > account_before.margin

        return False

    def _close_position(
        self,
        order: GatewayOrderModel,
    ) -> None:
        close_volume = order.executed_volume if order.executed_volume > 0 else order.volume
        opposite_side = OrderSide.SELL if order.side == OrderSide.BUY else OrderSide.BUY

        close_order = self._gateway.open(
            symbol=self._SYMBOL,
            side=opposite_side,
            order_type=OrderType.MARKET,
            volume=close_volume,
        )

        if close_order is None:
            self.fail("Position should be closed. Failed to open opposite order.")

    def _cancel_order(
        self,
        order: GatewayOrderModel,
        account_before: Optional[GatewayAccountModel],
    ) -> Optional[GatewayOrderModel]:
        closed_order = self._gateway.close(
            symbol=self._SYMBOL,
            order_id=order.id,
        )

        if closed_order is None:
            if account_before:
                account_check = self._gateway.account()

                if account_check and account_check.margin > account_before.margin:
                    self._close_position(order=order)
                    return None

            self.fail("Order should be cancelled. Check if the order was already filled or executed.")

        return closed_order

    def _assert_cancelled_order(
        self,
        cancelled_order: GatewayOrderModel,
        original_order: GatewayOrderModel,
    ) -> None:
        assert isinstance(cancelled_order, GatewayOrderModel), "Cancelled order should be a GatewayOrderModel"
        assert cancelled_order.symbol == original_order.symbol, "Symbol should match"
        assert cancelled_order.id == original_order.id, "Order ID should match"
        assert cancelled_order.side == original_order.side, "Side should match original order"
        assert cancelled_order.order_type == original_order.order_type, "Order type should match original order"
        assert cancelled_order.volume == original_order.volume, "Volume should match original order"
        assert cancelled_order.status == OrderStatus.CANCELLED, (
            f"Order status should be CANCELLED, but got {cancelled_order.status.value}"
        )

        if original_order.price is not None:
            assert cancelled_order.price == original_order.price, "Price should match original order"

    def _calculate_safe_limit_price(self) -> float:
        symbol_info = self._gateway.get_symbol_info(symbol=self._SYMBOL)

        if symbol_info is None:
            return 200000.0

        min_price = symbol_info.min_price or 100.0
        max_price = symbol_info.max_price or 200000.0
        limit_price = min_price * 10

        if limit_price > max_price:
            limit_price = max_price * 0.9

        return limit_price

    def _calculate_min_volume_for_notional(
        self,
        price: float,
        min_notional: float = 100.0,
    ) -> float:
        min_volume = min_notional / price
        min_volume = max(min_volume, 0.001)

        return round(min_volume, 3)

    def _verify_account_clean(self) -> None:
        account_after = self._gateway.account()

        if account_after:
            assert account_after.locked == 0, "No orders should remain locked after closing"
            assert account_after.margin == 0, "No positions should remain open after closing"
