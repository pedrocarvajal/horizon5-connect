from typing import TYPE_CHECKING, Any, Dict, Optional

from providers.horizon_router.models.snapshot import SnapshotCreateModel, SnapshotListQueryModel, SnapshotUpdateModel

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class SnapshotResource:
    _provider: "HorizonRouterProvider"

    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def list(self, query: Optional[SnapshotListQueryModel] = None) -> Dict[str, Any]:
        query_dict = query.model_dump(exclude_none=True) if query else None
        return self._provider.get("/api/v1/snapshots", query=query_dict)

    def get(self, snapshot_id: str) -> Dict[str, Any]:
        return self._provider.get(f"/api/v1/snapshot/{snapshot_id}")

    def create(self, data: SnapshotCreateModel) -> Dict[str, Any]:
        return self._provider.post("/api/v1/snapshot", data=data.model_dump(exclude_none=True))

    def update(self, snapshot_id: str, data: SnapshotUpdateModel) -> Dict[str, Any]:
        return self._provider.put(f"/api/v1/snapshot/{snapshot_id}", data=data.model_dump(exclude_none=True))

    def delete(self, snapshot_id: str) -> Dict[str, Any]:
        return self._provider.delete(f"/api/v1/snapshot/{snapshot_id}")
