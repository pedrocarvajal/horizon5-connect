from interfaces.asset import AssetInterface
from services.analytic import AnalyticService


class AssetService(AssetInterface):
    def __init__(self) -> None:
        super().__init__()

        self._analytic = AnalyticService()

    @property
    def analytic(self) -> AnalyticService:
        return self._analytic
