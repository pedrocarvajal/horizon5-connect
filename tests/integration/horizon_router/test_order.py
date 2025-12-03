import unittest
from typing import Optional
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from providers.horizon_router import HorizonRouterProvider
from providers.horizon_router.models.order import OrderCreateModel, OrderUpdateModel

class TestOrderResource(unittest.TestCase):
    _created_order_id: Optional[str] = None

    def setUp(self) -> None:
        self._provider = HorizonRouterProvider()

    def test_1_list_orders(self) -> None:
        response = self._provider.orders().list()
        assert response is not None, 'List orders response should not be None'
        assert isinstance(response, dict), 'List orders response should be a dictionary'

    def test_2_create_order(self) -> None:
        order_data = OrderCreateModel(strategy_id='507f1f77bcf86cd799439011', asset_id='507f1f77bcf86cd799439012', account_id='507f1f77bcf86cd799439014', backtest=True, symbol='BTCUSDT', side=OrderSide.BUY, order_type=OrderType.MARKET, volume=0.01, price=50000)
        response = self._provider.orders().create(order_data)
        assert response is not None, 'Create order response should not be None'
        assert isinstance(response, dict), 'Create order response should be a dictionary'
        if 'id' in response:
            self.__class__._created_order_id = response['id']
        elif 'data' in response and isinstance(response['data'], dict) and ('id' in response['data']):
            self.__class__._created_order_id = response['data']['id']

    def test_3_get_order(self) -> None:
        if not hasattr(self.__class__, '_created_order_id') or self.__class__._created_order_id is None:
            self.skipTest('No order ID available from creation test')
        response = self._provider.orders().get(self.__class__._created_order_id)
        assert response is not None, 'Get order response should not be None'
        assert isinstance(response, dict), 'Get order response should be a dictionary'

    def test_4_update_order(self) -> None:
        if not hasattr(self.__class__, '_created_order_id') or self.__class__._created_order_id is None:
            self.skipTest('No order ID available from creation test')
        update_data = OrderUpdateModel(status=OrderStatus.CLOSED, executed_volume=0.01)
        response = self._provider.orders().update(self.__class__._created_order_id, update_data)
        assert response is not None, 'Update order response should not be None'
        assert isinstance(response, dict), 'Update order response should be a dictionary'

    def test_5_delete_order(self) -> None:
        if not hasattr(self.__class__, '_created_order_id') or self.__class__._created_order_id is None:
            self.skipTest('No order ID available from creation test')
        response = self._provider.orders().delete(self.__class__._created_order_id)
        assert response is not None, 'Delete order response should not be None'
        assert isinstance(response, dict), 'Delete order response should be a dictionary'
