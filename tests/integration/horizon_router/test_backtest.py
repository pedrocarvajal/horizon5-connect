from typing import Optional

from enums.backtest_status import BacktestStatus
from providers.horizon_router.models.backtest import BacktestUpdateModel
from tests.integration.horizon_router import HorizonRouterWrapper


class TestBacktestResource(HorizonRouterWrapper):
    _created_backtest_id: Optional[str] = None

    def setUp(self) -> None:
        super().setUp()
        self._log.setup(name="test_backtest_resource")

    def test_1_list_backtests(self) -> None:
        response = self._provider.backtests().list()
        assert response is not None, "List backtests response should not be None"
        assert isinstance(response, dict), "List backtests response should be a dictionary"

    def test_2_create_backtest(self) -> None:
        backtest_data = self._create_test_backtest_payload()
        response = self._provider.backtests().create(backtest_data)
        assert response is not None, "Create backtest response should not be None"
        assert isinstance(response, dict), "Create backtest response should be a dictionary"
        if "id" in response:
            self.__class__._created_backtest_id = response["id"]
        elif "data" in response and isinstance(response["data"], dict) and ("id" in response["data"]):
            self.__class__._created_backtest_id = response["data"]["id"]

    def test_3_get_backtest(self) -> None:
        if not hasattr(self.__class__, "_created_backtest_id") or self.__class__._created_backtest_id is None:
            self.skipTest("No backtest ID available from creation test")
        response = self._provider.backtests().get(self.__class__._created_backtest_id)
        assert response is not None, "Get backtest response should not be None"
        assert isinstance(response, dict), "Get backtest response should be a dictionary"

    def test_4_update_backtest(self) -> None:
        if not hasattr(self.__class__, "_created_backtest_id") or self.__class__._created_backtest_id is None:
            self.skipTest("No backtest ID available from creation test")
        update_data = BacktestUpdateModel(status=BacktestStatus.RUNNING)
        response = self._provider.backtests().update(self.__class__._created_backtest_id, update_data)
        assert response is not None, "Update backtest response should not be None"
        assert isinstance(response, dict), "Update backtest response should be a dictionary"

    def test_5_delete_backtest(self) -> None:
        if not hasattr(self.__class__, "_created_backtest_id") or self.__class__._created_backtest_id is None:
            self.skipTest("No backtest ID available from creation test")
        response = self._provider.backtests().delete(self.__class__._created_backtest_id)
        assert response is not None, "Delete backtest response should not be None"
        assert isinstance(response, dict), "Delete backtest response should be a dictionary"
