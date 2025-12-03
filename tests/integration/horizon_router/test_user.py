import unittest
from typing import Optional
from providers.horizon_router.models.user import UserAnalyticsModel, UserCreateModel, UserUpdateModel
from tests.integration.horizon_router import HorizonRouterWrapper

class TestUserResource(unittest.TestCase):
    _created_user_id: Optional[str] = None

    def setUp(self) -> None:
        self._wrapper = HorizonRouterWrapper()
        self._wrapper.setUp()
        self._provider = self._wrapper._provider

    def test_1_list_users(self) -> None:
        response = self._provider.users().list()
        assert response is not None, 'List users response should not be None'
        assert isinstance(response, dict), 'List users response should be a dictionary'

    def test_2_create_user(self) -> None:
        analytics = UserAnalyticsModel(user_agent='Mozilla/5.0 (Test)', timestamp='2025-12-03T00:00:00Z')
        user_data = UserCreateModel(name='Test User', email=f'test.user.{id(self)}@example.com', password='TestPassword123', password_confirmation='TestPassword123', analytics=analytics)
        response = self._provider.users().create(user_data)
        assert response is not None, 'Create user response should not be None'
        assert isinstance(response, dict), 'Create user response should be a dictionary'
        if 'id' in response:
            self.__class__._created_user_id = response['id']
        elif 'data' in response and isinstance(response['data'], dict) and ('id' in response['data']):
            self.__class__._created_user_id = response['data']['id']

    def test_3_get_user(self) -> None:
        if not hasattr(self.__class__, '_created_user_id') or self.__class__._created_user_id is None:
            self.skipTest('No user ID available from creation test')
        response = self._provider.users().get(self.__class__._created_user_id)
        assert response is not None, 'Get user response should not be None'
        assert isinstance(response, dict), 'Get user response should be a dictionary'

    def test_4_update_user(self) -> None:
        if not hasattr(self.__class__, '_created_user_id') or self.__class__._created_user_id is None:
            self.skipTest('No user ID available from creation test')
        update_data = UserUpdateModel(name='Updated Test User')
        response = self._provider.users().update(self.__class__._created_user_id, update_data)
        assert response is not None, 'Update user response should not be None'
        assert isinstance(response, dict), 'Update user response should be a dictionary'

    def test_5_delete_user(self) -> None:
        if not hasattr(self.__class__, '_created_user_id') or self.__class__._created_user_id is None:
            self.skipTest('No user ID available from creation test')
        response = self._provider.users().delete(self.__class__._created_user_id)
        assert response is not None, 'Delete user response should not be None'
        assert isinstance(response, dict), 'Delete user response should be a dictionary'
