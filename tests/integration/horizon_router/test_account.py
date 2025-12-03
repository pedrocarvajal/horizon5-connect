import unittest
from typing import Optional

from providers.horizon_router import HorizonRouterProvider
from providers.horizon_router.models.account import AccountCreateModel, AccountUpdateModel


class TestAccountResource(unittest.TestCase):
    _created_account_id: Optional[str] = None

    def setUp(self) -> None:
        self._provider = HorizonRouterProvider()

    def test_1_list_accounts(self) -> None:
        response = self._provider.accounts().list()
        assert response is not None, "List accounts response should not be None"
        assert isinstance(response, dict), "List accounts response should be a dictionary"

    def test_2_create_account(self) -> None:
        account_data = AccountCreateModel(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            gateway_id="550e8400-e29b-41d4-a716-446655440001",
            api_key="test_api_key",
            api_secret="test_api_secret",
            is_testnet=True,
            is_active=True,
        )
        response = self._provider.accounts().create(account_data)
        assert response is not None, "Create account response should not be None"
        assert isinstance(response, dict), "Create account response should be a dictionary"
        if "id" in response:
            self.__class__._created_account_id = response["id"]
        elif "data" in response and isinstance(response["data"], dict) and ("id" in response["data"]):
            self.__class__._created_account_id = response["data"]["id"]

    def test_3_get_account(self) -> None:
        if not hasattr(self.__class__, "_created_account_id") or self.__class__._created_account_id is None:
            self.skipTest("No account ID available from creation test")
        response = self._provider.accounts().get(self.__class__._created_account_id)
        assert response is not None, "Get account response should not be None"
        assert isinstance(response, dict), "Get account response should be a dictionary"

    def test_4_update_account(self) -> None:
        if not hasattr(self.__class__, "_created_account_id") or self.__class__._created_account_id is None:
            self.skipTest("No account ID available from creation test")
        update_data = AccountUpdateModel(is_active=False)
        response = self._provider.accounts().update(self.__class__._created_account_id, update_data)
        assert response is not None, "Update account response should not be None"
        assert isinstance(response, dict), "Update account response should be a dictionary"

    def test_5_delete_account(self) -> None:
        if not hasattr(self.__class__, "_created_account_id") or self.__class__._created_account_id is None:
            self.skipTest("No account ID available from creation test")
        response = self._provider.accounts().delete(self.__class__._created_account_id)
        assert response is not None, "Delete account response should not be None"
        assert isinstance(response, dict), "Delete account response should be a dictionary"
