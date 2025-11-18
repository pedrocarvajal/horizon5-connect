# Last coding review: 2025-01-XX XX:XX:XX
import unittest
from datetime import datetime, timedelta

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from services.gateway import GatewayService
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from services.logging import LoggingService


class TestBinanceOrders(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "btcusdt"

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
        self._log.setup(name="test_binance_orders")
        self._gateway = self._create_gateway()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def test_get_orders_last_3_months(self) -> None:
        end_time = datetime.now(tz=TIMEZONE)
        start_time = end_time - timedelta(days=90)

        orders = self._gateway.get_orders(
            symbol=self._SYMBOL,
            start_time=start_time,
            end_time=end_time,
        )

        assert isinstance(orders, list), "Orders should be a list"

        for order in orders:
            assert isinstance(order, GatewayOrderModel), "Each order should be a GatewayOrderModel"
            assert order.id, "Order ID should be set"
            assert order.symbol, "Order symbol should be set"
            assert order.symbol == order.symbol.upper(), "Order symbol should be uppercase"
            assert order.side in [OrderSide.BUY, OrderSide.SELL], "Order side should be BUY or SELL"
            assert order.order_type is not None, "Order type should be set"
            assert order.status is not None, "Order status should be set"
            assert order.status in [
                GatewayOrderStatus.PENDING,
                GatewayOrderStatus.EXECUTED,
                GatewayOrderStatus.CANCELLED,
            ], f"Order status should be valid GatewayOrderStatus, got {order.status}"
            assert order.volume >= 0, "Order volume should be non-negative"
            assert order.executed_volume >= 0, "Order executed volume should be non-negative"
            assert order.executed_volume <= order.volume, "Executed volume should not exceed order volume"
            assert order.price >= 0, "Order price should be non-negative"
            assert order.response is not None, "Order response should be set"
            assert isinstance(order.response, dict), "Order response should be a dictionary"

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _create_gateway(self) -> GatewayService:
        return GatewayService(
            gateway="binance",
            futures=True,
        )
