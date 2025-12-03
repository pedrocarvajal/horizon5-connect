import unittest
from typing import Optional
from helpers.get_env import get_env
from providers.horizon_router import HorizonRouterProvider

class TestAuthResource(unittest.TestCase):
    _token: Optional[str] = None

    def setUp(self) -> None:
        self._provider = HorizonRouterProvider()
        self._email = get_env('HORIZON_ROUTER_TEST_EMAIL', required=True)
        self._password = get_env('HORIZON_ROUTER_TEST_PASSWORD', required=True)

    def test_1_login(self) -> None:
        if self._email is None or self._password is None:
            self.skipTest('Email or password not configured in environment')
        response = self._provider.auth().login(self._email, self._password)
        assert response is not None, 'Login response should not be None'
        assert isinstance(response, dict), 'Login response should be a dictionary'
        assert 'token' in response or 'access_token' in response, 'Login response should contain a token'
        self.__class__._token = response.get('token') or response.get('access_token')

    def test_2_me(self) -> None:
        if not hasattr(self.__class__, '_token') or self.__class__._token is None:
            self.skipTest('Login token not available')
        response = self._provider.auth().me()
        assert response is not None, 'User info response should not be None'
        assert isinstance(response, dict), 'User info response should be a dictionary'
        assert 'id' in response or 'user' in response, 'User info should contain user data'

    def test_3_refresh(self) -> None:
        if not hasattr(self.__class__, '_token') or self.__class__._token is None:
            self.skipTest('Login token not available')
        response = self._provider.auth().refresh()
        assert response is not None, 'Refresh response should not be None'
        assert isinstance(response, dict), 'Refresh response should be a dictionary'
        assert 'token' in response or 'access_token' in response, 'Refresh response should contain a token'

    def test_4_logout(self) -> None:
        if not hasattr(self.__class__, '_token') or self.__class__._token is None:
            self.skipTest('Login token not available')
        response = self._provider.auth().logout()
        assert response is not None, 'Logout response should not be None'
        assert isinstance(response, dict), 'Logout response should be a dictionary'
