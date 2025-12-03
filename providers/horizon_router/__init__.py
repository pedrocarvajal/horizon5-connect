from typing import Any, Dict
from helpers.get_env import get_env
from providers import BaseProvider
from providers.horizon_router.models.backtest import BacktestCreateModel, BacktestUpdateModel
from providers.horizon_router.models.order import OrderCreateModel
from providers.horizon_router.models.snapshot import SnapshotCreateModel
from providers.horizon_router.resources import AccountResource, AuthResource, BacktestResource, HealthResource, OrderResource, SnapshotResource, UserResource

class HorizonRouterProvider(BaseProvider):

    def __init__(self) -> None:
        base_url = get_env('HORIZON_ROUTER_BASE_URL', required=True)
        api_key = get_env('HORIZON_ROUTER_API_KEY', required=True)
        if base_url is None or api_key is None:
            raise ValueError('Required environment variables are not set.')
        headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
        super().__init__(base_url=base_url, headers=headers, timeout=30, retry_times=3, retry_delay=100)

    def get_service_name(self) -> str:
        return 'horizon_router'

    def accounts(self) -> AccountResource:
        return AccountResource(self)

    def auth(self) -> AuthResource:
        return AuthResource(self)

    def backtests(self) -> BacktestResource:
        return BacktestResource(self)

    def health(self) -> HealthResource:
        return HealthResource(self)

    def orders(self) -> OrderResource:
        return OrderResource(self)

    def snapshots(self) -> SnapshotResource:
        return SnapshotResource(self)

    def users(self) -> UserResource:
        return UserResource(self)

    def backtest_create(self, body: BacktestCreateModel) -> Dict[str, Any]:
        return self.backtests().create(body)

    def backtest_update(self, backtest_id: str, body: BacktestUpdateModel) -> Dict[str, Any]:
        return self.backtests().update(backtest_id, body)

    def order_create(self, body: OrderCreateModel) -> Dict[str, Any]:
        return self.orders().create(body)

    def snapshot_create(self, body: SnapshotCreateModel) -> Dict[str, Any]:
        return self.snapshots().create(body)
