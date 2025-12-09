"""Portfolio service for managing collections of trading assets."""

from typing import Any, Dict

from enums.asset_quality_method import AssetQualityMethod
from interfaces.portfolio import PortfolioInterface
from models.tick import TickModel
from services.logging import LoggingService
from services.quality_calculator import QualityCalculatorService


class PortfolioService(PortfolioInterface):
    """Service for managing a portfolio of trading assets."""

    _portfolio_quality_method: AssetQualityMethod

    _log: LoggingService
    _quality_calculator: QualityCalculatorService

    def __init__(self) -> None:
        """Initialize the portfolio with an empty asset list."""
        self._assets = []
        self._asset_instances = []
        self._log = LoggingService()

        if not hasattr(self, "_portfolio_quality_method"):
            self._portfolio_quality_method = AssetQualityMethod.WEIGHTED_AVERAGE

        self._quality_calculator = QualityCalculatorService(
            quality_method=self._portfolio_quality_method,
            children_key="assets",
        )

    def on_end(self) -> Dict[str, Any]:
        """Finalize portfolio and return aggregated report."""
        self._quality_calculator.reset()

        for asset in self._asset_instances:
            asset_report = asset.on_end()

            if asset_report:
                self._quality_calculator.on_report(asset.symbol, asset_report)

        return self._quality_calculator.on_end()

    def on_tick(self, ticks: Dict[str, TickModel]) -> None:
        """Process tick data for all assets.

        Args:
            ticks: Dictionary mapping symbol to tick data.
        """
        for asset in self._asset_instances:
            tick = ticks.get(asset.symbol)

            if tick is not None:
                asset.on_tick(tick)

    def setup(self, **kwargs: Any) -> None:
        """Configure the portfolio and instantiate all assets."""
        for asset_class, allocation in self._assets:
            asset_instance = asset_class(allocation=allocation)

            if not asset_instance.enabled:
                self._log.warning(f"Asset {asset_instance.symbol} is not enabled")
                continue

            asset_instance.setup(**kwargs)
            self._asset_instances.append(asset_instance)
