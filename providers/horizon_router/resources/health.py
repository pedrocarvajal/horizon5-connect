from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from providers.horizon_router import HorizonRouterProvider


class HealthResource:
    def __init__(self, provider: "HorizonRouterProvider") -> None:
        self._provider = provider

    def check(self) -> Dict[str, Any]:
        return self._provider.get("/api/v1/health")
