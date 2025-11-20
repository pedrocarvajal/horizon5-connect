# Last coding review: 2025-11-18 13:55:00

import datetime

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.gateway_order import GatewayOrderModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceOrder(BinanceWrapper):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "BTCUSDT"
    _DEFAULT_VOLUME: float = 0.002
    _LIMIT_PRICE_DISCOUNT: float = 0.9
    _KLINES_LOOKBACK_MINUTES: int = 5

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_binance_order")

    def test_place_order_market(self) -> None:
        self._log.info("Placing a market BUY order for BTCUSDT")

        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        self._log.info(f"Order placed successfully: {order.id}")

        self._log.info(f"Closing order {order.id}")
        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.id)

    def test_cancel_order(self) -> None:
        self._log.info("Placing a limit order to cancel")

        limit_price = self._get_limit_price(
            symbol=self._SYMBOL,
            discount=self._LIMIT_PRICE_DISCOUNT,
            lookback_minutes=self._KLINES_LOOKBACK_MINUTES,
        )

        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
            price=limit_price,
        )

        self._assert_order_is_valid(order=order, expected_type=OrderType.LIMIT)
        self._log.info(f"Limit order placed successfully: {order.id}")

        cancelled_order = self._gateway.cancel_order(
            symbol=self._SYMBOL,
            order=order,
        )

        self._assert_order_is_cancelled(cancelled_order=cancelled_order, original_order=order)
        self._log.info(f"Order cancelled successfully: {cancelled_order.id}")

    def test_get_order(self) -> None:
        self._log.info("Placing an order to retrieve")

        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        self._log.info(f"Order placed successfully: {order.id}")

        retrieved_order = self._gateway.get_order(
            symbol=self._SYMBOL,
            order_id=order.id,
        )

        assert retrieved_order is not None, "Retrieved order should not be None"
        assert isinstance(retrieved_order, GatewayOrderModel), "Retrieved order should be a GatewayOrderModel"
        assert retrieved_order.id == order.id, "Retrieved order ID should match original order ID"
        assert retrieved_order.symbol == self._SYMBOL, f"Retrieved order symbol should be {self._SYMBOL}"
        assert retrieved_order.response is not None, "Retrieved order response should not be None"

        self._log.info(f"Order retrieved successfully: {retrieved_order.id}")
        self._log.info(f"Closing order {order.id}")

        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.id)

    def test_get_orders(self) -> None:
        self._log.info("Querying orders")

        end_time = datetime.datetime.now(tz=TIMEZONE)
        start_time = end_time - datetime.timedelta(days=90)

        orders = self._gateway.get_orders(
            symbol=self._SYMBOL,
            pair=self._SYMBOL,
            order_id=1,
            start_time=start_time,
            end_time=end_time,
            limit=100,
        )

        assert orders is not None, "Orders should not be None"
        assert isinstance(orders, list), "Orders should be a list"
        assert all(isinstance(o, GatewayOrderModel) for o in orders), "All orders should be GatewayOrderModel"

        for order in orders:
            assert order.symbol == self._SYMBOL, f"Order symbol should be {self._SYMBOL}"
            assert order.id != "", "Order ID should not be empty"
            assert order.response is not None, "Order response should not be None"

        self._log.info(f"Found {len(orders)} orders")
