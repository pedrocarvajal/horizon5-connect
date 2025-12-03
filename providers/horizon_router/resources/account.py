from typing import TYPE_CHECKING, Any, Dict, Optional

from providers.horizon_router.models.account import AccountCreateModel, AccountListQueryModel, AccountUpdateModel

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class AccountResource:
    _provider: "HorizonRouterProvider"

    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def list(self, query: Optional[AccountListQueryModel] = None) -> Dict[str, Any]:
        query_dict = query.model_dump(exclude_none=True) if query else None
        return self._provider.get("/api/v1/accounts", query=query_dict)

    def get(self, account_id: str) -> Dict[str, Any]:
        return self._provider.get(f"/api/v1/account/{account_id}")

    def create(self, data: AccountCreateModel) -> Dict[str, Any]:
        return self._provider.post("/api/v1/account", data=data.model_dump(exclude_none=True))

    def update(self, account_id: str, data: AccountUpdateModel) -> Dict[str, Any]:
        return self._provider.put(f"/api/v1/account/{account_id}", data=data.model_dump(exclude_none=True))

    def delete(self, account_id: str) -> Dict[str, Any]:
        return self._provider.delete(f"/api/v1/account/{account_id}")
