from typing import TYPE_CHECKING, Any, Dict, Optional

from providers.horizon_router.models.order import OrderCreateModel, OrderListQueryModel, OrderUpdateModel

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class OrderResource:
    _provider: "HorizonRouterProvider"

    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def list(self, query: Optional[OrderListQueryModel] = None) -> Dict[str, Any]:
        query_dict = query.model_dump(exclude_none=True) if query else None
        return self._provider.get("/api/v1/orders", query=query_dict)

    def get(self, order_id: str) -> Dict[str, Any]:
        return self._provider.get(f"/api/v1/order/{order_id}")

    def create(self, data: OrderCreateModel) -> Dict[str, Any]:
        return self._provider.post("/api/v1/order", data=data.model_dump(exclude_none=True))

    def update(self, order_id: str, data: OrderUpdateModel) -> Dict[str, Any]:
        return self._provider.put(f"/api/v1/order/{order_id}", data=data.model_dump(exclude_none=True))

    def delete(self, order_id: str) -> Dict[str, Any]:
        return self._provider.delete(f"/api/v1/order/{order_id}")
