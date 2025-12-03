from typing import TYPE_CHECKING, Any, Dict, Optional

from providers.horizon_router.models.user import UserCreateModel, UserListQueryModel, UserUpdateModel

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class UserResource:
    _provider: "HorizonRouterProvider"

    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def list(self, query: Optional[UserListQueryModel] = None) -> Dict[str, Any]:
        query_dict = query.model_dump(exclude_none=True) if query else None
        return self._provider.get("/api/v1/users", query=query_dict)

    def get(self, user_id: str) -> Dict[str, Any]:
        return self._provider.get(f"/api/v1/user/{user_id}")

    def create(self, data: UserCreateModel) -> Dict[str, Any]:
        return self._provider.post("/api/v1/user", data=data.model_dump(exclude_none=True))

    def update(self, user_id: str, data: UserUpdateModel) -> Dict[str, Any]:
        return self._provider.put(f"/api/v1/user/{user_id}", data=data.model_dump(exclude_none=True))

    def delete(self, user_id: str) -> Dict[str, Any]:
        return self._provider.delete(f"/api/v1/user/{user_id}")
