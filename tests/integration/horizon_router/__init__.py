import unittest
from typing import Optional
from enums.backtest_status import BacktestStatus
from helpers.get_env import get_env
from providers.horizon_router import HorizonRouterProvider
from providers.horizon_router.models.backtest import BacktestCreateModel, BacktestSettingsModel
from services.logging import LoggingService

class HorizonRouterWrapper(unittest.TestCase):
    _DEFAULT_USER_ID: str = '550e8400-e29b-41d4-a716-446655440000'
    _DEFAULT_BACKTEST_ASSET: str = 'BTCUSDT'
    _DEFAULT_BACKTEST_FROM_DATE: int = 1609459200
    _DEFAULT_BACKTEST_TO_DATE: int = 1640995200
    _provider: HorizonRouterProvider
    _log: LoggingService
    _token: Optional[str]

    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name=self.__class__.__name__)
        self._provider = HorizonRouterProvider()
        self._token = None
        self._authenticate()
        assert self._token is not None, 'Authentication token should not be None'
        self._inject_bearer_token()

    def _authenticate(self) -> None:
        email = get_env('HORIZON_ROUTER_TEST_EMAIL', required=True)
        password = get_env('HORIZON_ROUTER_TEST_PASSWORD', required=True)
        if email is None or password is None:
            raise ValueError('Authentication credentials not configured in environment')
        response = self._provider.auth().login(email, password)
        assert response is not None, 'Login response should not be None'
        assert isinstance(response, dict), 'Login response should be a dictionary'
        if 'data' in response and isinstance(response['data'], dict):
            self._token = response['data'].get('token') or response['data'].get('access_token')
        else:
            self._token = response.get('token') or response.get('access_token')
        assert self._token is not None, 'Login response should contain a token'

    def _inject_bearer_token(self) -> None:
        if self._token:
            self._provider._headers['Authorization'] = f'Bearer {self._token}'

    def _create_test_backtest_payload(self, user_id: Optional[str]=None, asset: Optional[str]=None, strategies: Optional[str]=None, from_date: Optional[int]=None, to_date: Optional[int]=None, status: str='pending') -> BacktestCreateModel:
        settings = BacktestSettingsModel(asset=asset or self._DEFAULT_BACKTEST_ASSET, strategies=strategies or 'default_strategy', from_date=from_date or self._DEFAULT_BACKTEST_FROM_DATE, to_date=to_date or self._DEFAULT_BACKTEST_TO_DATE)
        return BacktestCreateModel(user_id=user_id or self._DEFAULT_USER_ID, status=BacktestStatus(status), settings=settings)
