import datetime
from typing import Optional

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_type import OrderType
from services.gateway.models.enums.gateway_order_status import GatewayOrderStatus
from services.gateway.models.gateway_order import GatewayOrderModel
from tests.integration.binance.wrappers.binance import BinanceWrapper


class TestBinanceOrder(BinanceWrapper):
    _SYMBOL: str = 'BTCUSDT'
    _DEFAULT_VOLUME: float = 0.002

    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name='test_binance_order')

    def test_place_order_market(self) -> None:
        order = self._place_test_order(symbol=self._SYMBOL, side=OrderSide.BUY, volume=self._DEFAULT_VOLUME)
        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        assert order is not None
        self._delete_order_by_id(symbol=self._SYMBOL, order_id=order.id)

    def test_get_order(self) -> None:
        order = self._place_test_order(symbol=self._SYMBOL, side=OrderSide.BUY, volume=self._DEFAULT_VOLUME)
        self._assert_order_is_valid(order=order, expected_type=OrderType.MARKET)
        assert order is not None
        retrieved_order = self._gateway.get_order(symbol=self._SYMBOL, order_id=order.id)
        assert retrieved_order is not None, 'Retrieved order should not be None'
        assert isinstance(retrieved_order, GatewayOrderModel), 'Retrieved order should be a GatewayOrderModel'
        assert retrieved_order.id == order.id, 'Retrieved order ID should match original order ID'
        assert retrieved_order.symbol == self._SYMBOL, f'Retrieved order symbol should be {self._SYMBOL}'
        assert retrieved_order.response is not None, 'Retrieved order response should not be None'
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
        assert orders is not None, 'Orders should not be None'
        assert isinstance(orders, list), 'Orders should be a list'
        assert all(isinstance(o, GatewayOrderModel) for o in orders), 'All orders should be GatewayOrderModel'
        for order in orders:
            assert order.symbol == self._SYMBOL, f'Order symbol should be {self._SYMBOL}'
            assert order.id != '', 'Order ID should not be empty'
            assert order.response is not None, 'Order response should not be None'

    def _assert_order_is_valid(
        self, order: Optional[GatewayOrderModel], expected_type: OrderType, expected_symbol: Optional[str]=None
    ) -> None:
        if expected_symbol is None:
            expected_symbol = self._SYMBOL
        assert order is not None, 'Order should not be None'
        assert isinstance(order, GatewayOrderModel), 'Order should be a GatewayOrderModel'
        assert order.id != '', 'Order ID should not be empty'
        assert order.symbol == expected_symbol, f'Symbol should be {expected_symbol}'
        assert order.order_type == expected_type, f'Order type should be {expected_type}'
        assert order.volume > 0, 'Volume should be > 0'
        assert order.executed_volume >= 0, 'Executed volume should be >= 0'
        if expected_type.is_market():
            assert order.status in [
                GatewayOrderStatus.PENDING,
                GatewayOrderStatus.EXECUTED,
            ], 'Status should be PENDING or EXECUTED'
        assert order.response is not None, 'Response should not be None'
