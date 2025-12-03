import unittest
from typing import Optional

from enums.snapshot_event import SnapshotEvent
from providers.horizon_router import HorizonRouterProvider
from providers.horizon_router.models.snapshot import SnapshotCreateModel, SnapshotUpdateModel


class TestSnapshotResource(unittest.TestCase):
    _created_snapshot_id: Optional[str] = None

    def setUp(self) -> None:
        self._provider = HorizonRouterProvider()

    def test_1_list_snapshots(self) -> None:
        response = self._provider.snapshots().list()
        assert response is not None, "List snapshots response should not be None"
        assert isinstance(response, dict), "List snapshots response should be a dictionary"

    def test_2_create_snapshot(self) -> None:
        snapshot_data = SnapshotCreateModel(
            strategy_id="673fa4234ba7a04b2b0e1be9",
            asset_id="673fa4234ba7a04b2b0e1be8",
            event=SnapshotEvent.START_SNAPSHOT,
            nav=10000.5,
            allocation=0.75,
            backtest=True,
        )
        response = self._provider.snapshots().create(snapshot_data)
        assert response is not None, "Create snapshot response should not be None"
        assert isinstance(response, dict), "Create snapshot response should be a dictionary"
        if "id" in response:
            self.__class__._created_snapshot_id = response["id"]
        elif "data" in response and isinstance(response["data"], dict) and ("id" in response["data"]):
            self.__class__._created_snapshot_id = response["data"]["id"]

    def test_3_get_snapshot(self) -> None:
        if not hasattr(self.__class__, "_created_snapshot_id") or self.__class__._created_snapshot_id is None:
            self.skipTest("No snapshot ID available from creation test")
        response = self._provider.snapshots().get(self.__class__._created_snapshot_id)
        assert response is not None, "Get snapshot response should not be None"
        assert isinstance(response, dict), "Get snapshot response should be a dictionary"

    def test_4_update_snapshot(self) -> None:
        if not hasattr(self.__class__, "_created_snapshot_id") or self.__class__._created_snapshot_id is None:
            self.skipTest("No snapshot ID available from creation test")
        update_data = SnapshotUpdateModel(event=SnapshotEvent.ON_NEW_DAY, nav=11000.75)
        response = self._provider.snapshots().update(self.__class__._created_snapshot_id, update_data)
        assert response is not None, "Update snapshot response should not be None"
        assert isinstance(response, dict), "Update snapshot response should be a dictionary"

    def test_5_delete_snapshot(self) -> None:
        if not hasattr(self.__class__, "_created_snapshot_id") or self.__class__._created_snapshot_id is None:
            self.skipTest("No snapshot ID available from creation test")
        response = self._provider.snapshots().delete(self.__class__._created_snapshot_id)
        assert response is not None, "Delete snapshot response should not be None"
        assert isinstance(response, dict), "Delete snapshot response should be a dictionary"
