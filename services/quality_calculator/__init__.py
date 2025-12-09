"""Quality calculator service for aggregating child reports into quality metrics."""

from __future__ import annotations

from typing import Any, Dict, Tuple

from enums.asset_quality_method import AssetQualityMethod
from interfaces.quality_calculator import QualityCalculatorInterface
from services.logging import LoggingService


class QualityCalculatorService(QualityCalculatorInterface):
    """Service for aggregating child reports and calculating quality metrics.

    Used by AssetService to aggregate strategy reports and by PortfolioService
    to aggregate asset reports.

    Attributes:
        _quality_method: Method for aggregating child qualities.
        _reports: Collected child reports for aggregation.
        _children_key: Key name for children in the output report.
    """

    _quality_method: AssetQualityMethod
    _reports: Dict[str, Dict[str, Any]]
    _children_key: str
    _log: LoggingService

    def __init__(
        self,
        quality_method: AssetQualityMethod = AssetQualityMethod.WEIGHTED_AVERAGE,
        children_key: str = "children",
    ) -> None:
        """Initialize the quality calculator service.

        Args:
            quality_method: Method for aggregating child qualities.
            children_key: Key name for children in output (e.g., "strategies", "assets").
        """
        self._log = LoggingService()
        self._quality_method = quality_method
        self._reports = {}
        self._children_key = children_key

    def on_report(self, report_id: str, report: Dict[str, Any]) -> None:
        """Record a child report.

        Args:
            report_id: Unique identifier for the report.
            report: Child report dictionary containing metrics.
        """
        self._reports[report_id] = report

    def on_end(self) -> Dict[str, Any]:
        """Build the aggregated report from all child reports.

        Returns:
            Aggregated report with performance and quality data.
        """
        total_allocation = sum(report.get("allocation", 0) for report in self._reports.values())
        total_performance = sum(report.get("performance", 0) for report in self._reports.values())
        performance_percentage = total_performance / total_allocation if total_allocation > 0 else 0.0
        quality, quality_method = self._calculate_aggregated_quality()

        report = {
            "allocation": total_allocation,
            "performance": total_performance,
            "performance_percentage": performance_percentage,
            "quality": quality,
            "quality_method": quality_method,
            self._children_key: self._reports,
        }

        self._log.debug(report)

        return report

    def reset(self) -> None:
        """Reset collected child reports."""
        self._reports = {}

    def _calculate_aggregated_quality(self) -> Tuple[float, str]:
        """Calculate aggregated quality from child reports using selected method.

        Returns:
            Tuple of (aggregated_quality, aggregation_method_name).
        """
        if not self._reports:
            return 0.0, self._quality_method.value

        return self._calculate_weighted_average_quality()

    def _calculate_weighted_average_quality(self) -> Tuple[float, str]:
        """Calculate quality as weighted average by allocation.

        Formula: sum(quality_i * allocation_i) / sum(allocation_i)
        """
        total_allocation = 0.0
        weighted_quality_sum = 0.0

        for report in self._reports.values():
            allocation = report.get("allocation", 0)
            quality = report.get("quality", 0)

            if allocation > 0:
                weighted_quality_sum += quality * allocation
                total_allocation += allocation

        aggregated_quality = weighted_quality_sum / total_allocation if total_allocation > 0 else 0.0
        return round(aggregated_quality, 4), AssetQualityMethod.WEIGHTED_AVERAGE.value
