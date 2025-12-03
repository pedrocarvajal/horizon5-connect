from typing import TYPE_CHECKING, Any, Dict, Optional

from providers.horizon_router.models.backtest import BacktestCreateModel, BacktestListQueryModel, BacktestUpdateModel

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class BacktestResource:
    _provider: "HorizonRouterProvider"

    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def list(self, query: Optional[BacktestListQueryModel] = None) -> Dict[str, Any]:
        query_dict = query.model_dump(exclude_none=True) if query else None
        return self._provider.get("/api/v1/backtests", query=query_dict)

    def get(self, backtest_id: str) -> Dict[str, Any]:
        return self._provider.get(f"/api/v1/backtest/{backtest_id}")

    def create(self, data: BacktestCreateModel) -> Dict[str, Any]:
        return self._provider.post("/api/v1/backtest", data=data.model_dump(exclude_none=True))

    def update(self, backtest_id: str, data: BacktestUpdateModel) -> Dict[str, Any]:
        return self._provider.put(f"/api/v1/backtest/{backtest_id}", data=data.model_dump(exclude_none=True))

    def delete(self, backtest_id: str) -> Dict[str, Any]:
        return self._provider.delete(f"/api/v1/backtest/{backtest_id}")
