"""Portfolio service for managing collections of trading assets."""

from typing import Any, Dict

from enums.asset_quality_method import AssetQualityMethod
from interfaces.portfolio import PortfolioInterface
from services.quality_calculator import QualityCalculatorService


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _portfolio_quality_method: AssetQualityMethod
    _quality_calculator: QualityCalculatorService

    def __init__(self) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._assets = []

        if not hasattr(self, "_portfolio_quality_method"):
            self._portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

        self._quality_calculator = QualityCalculatorService(
            quality_method=self._portfolio_quality_method,
            children_key="assets",
        )

    def on_end(self, asset_reports: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Build the portfolio report from asset reports.

        Args:
            asset_reports: Dictionary of asset reports keyed by asset name.

        Returns:
            Portfolio report with aggregated performance and quality data.
        """
        self._quality_calculator.reset()

        for asset_id, asset_report in asset_reports.items():
            self._quality_calculator.on_report(asset_id, asset_report)

        return self._quality_calculator.on_end()
