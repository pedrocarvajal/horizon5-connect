from interfaces.asset import AssetInterface
from services.analytics import AnalyticsService


class AssetService(AssetInterface):
    def __init__(self) -> None:
        super().__init__()

        self._analytics = AnalyticsService()

    @property
    def analytics(self) -> AnalyticsService:
        return self._analytics
