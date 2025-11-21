# Code reviewed on 2025-11-21 by Pedro Carvajal

import datetime

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from tests.integration.binance.wrappers.binance import BinanceWrapper
from typing import List, Optional


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
        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.id)

    def test_cancel_order(self) -> None:
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

        cancelled_order = self._gateway.cancel_order(
            symbol=self._SYMBOL,
            order=order,
        )

        self._assert_order_is_cancelled(cancelled_order=cancelled_order, original_order=order)

    def test_get_order(self) -> None:
        order = self._place_test_order(
            symbol=self._SYMBOL,
            side=OrderSide.BUY,
            volume=self._DEFAULT_VOLUME,
        )

        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)

        retrieved_order = self._gateway.get_order(
            symbol=self._SYMBOL,
            order_id=order.id,
        )

        assert retrieved_order is not None, "Retrieved order should not be None"
        assert isinstance(retrieved_order, GatewayOrderModel), "Retrieved order should be a GatewayOrderModel"
        assert retrieved_order.id == order.id, "Retrieved order ID should match original order ID"
        assert retrieved_order.symbol == self._SYMBOL, f"Retrieved order symbol should be {self._SYMBOL}"
        assert retrieved_order.response is not None, "Retrieved order response should not be None"

        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.id)

    def test_get_orders(self) -> None:
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

    # ───────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ───────────────────────────────────────────────────────────
    def _assert_order_is_valid(
        self,
        order: Optional[GatewayOrderModel],
        expected_type: OrderType,
        expected_symbol: Optional[str] = None,
    ) -> None:
        if expected_symbol is None:
            expected_symbol = self._SYMBOL

        assert order is not None, "Order should not be None"
        assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
        assert order.id != "", "Order ID should not be empty"
        assert order.symbol == expected_symbol, f"Symbol should be {expected_symbol}"
        assert order.order_type == expected_type, f"Order type should be {expected_type}"
        assert order.volume > 0, "Volume should be > 0"
        assert order.executed_volume >= 0, "Executed volume should be >= 0"

        if expected_type.is_market():
            assert order.status in [
                GatewayOrderStatus.PENDING,
                GatewayOrderStatus.EXECUTED,
            ], "Status should be PENDING or EXECUTED"

        assert order.response is not None, "Response should not be None"

    def _assert_order_is_cancelled(
        self,
        cancelled_order: Optional[GatewayOrderModel],
        original_order: GatewayOrderModel,
    ) -> None:
        assert cancelled_order is not None, "Cancelled order should not be None"
        assert isinstance(cancelled_order, GatewayOrderModel), "Cancelled order should be a GatewayOrderModel"
        assert cancelled_order.id == original_order.id, "Cancelled order ID should match original order ID"
        assert cancelled_order.status == GatewayOrderStatus.CANCELLED, "Order status should be CANCELLED"
        assert cancelled_order.response is not None, "Response should not be None"

    def _fetch_latest_candle(
        self,
        symbol: str,
        timeframe: str = "1m",
        lookback_minutes: int = 5,
    ) -> GatewayKlineModel:
        latest_kline: Optional[GatewayKlineModel] = None

        def callback(klines: List[GatewayKlineModel]) -> None:
            nonlocal latest_kline

            if klines:
                latest_kline = klines[-1]

        end_time = datetime.datetime.now(tz=TIMEZONE)
        start_time = end_time - datetime.timedelta(minutes=lookback_minutes)

        self._gateway.get_klines(
            symbol=symbol,
            timeframe=timeframe,
            from_date=start_time.timestamp(),
            to_date=end_time.timestamp(),
            callback=callback,
        )

        assert latest_kline is not None, "Latest kline should not be None"
        assert latest_kline.close_price > 0, "Close price should be > 0"

        return latest_kline

    def _get_limit_price(
        self,
        symbol: str,
        discount: float = 0.9,
        lookback_minutes: int = 5,
    ) -> float:
        symbol_info = self._gateway.get_symbol_info(symbol=symbol)

        assert symbol_info is not None, "Symbol info should not be None"
        assert symbol_info.tick_size is not None, "Tick size should not be None"

        latest_kline = self._fetch_latest_candle(
            symbol=symbol,
            timeframe="1m",
            lookback_minutes=lookback_minutes,
        )

        current_price = latest_kline.close_price
        limit_price_raw = current_price * discount
        tick_size = symbol_info.tick_size
        limit_price_rounded = round(limit_price_raw / tick_size) * tick_size
        limit_price = round(limit_price_rounded, symbol_info.price_precision)

        discount_percent = int(discount * 100)

        self._log.info(f"Current price: {current_price}, Limit price ({discount_percent}%): {limit_price}")

        return limit_price
