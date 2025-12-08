"""Quality calculator service for aggregating child reports into quality metrics."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from numpy.typing import NDArray

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

    MIN_HISTORY_LENGTH_FOR_CORRELATION = 2
    MIN_STRATEGIES_FOR_CORRELATION = 2
    CORRELATION_PENALTY_FACTOR = 0.5
    MIN_DIVERSIFICATION_FACTOR = 0.5
    MAX_DIVERSIFICATION_FACTOR = 1.0

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

        if self._quality_method == AssetQualityMethod.MINIMUM:
            return self._calculate_minimum_quality()

        if self._quality_method == AssetQualityMethod.CONTRIBUTION_WEIGHTED:
            return self._calculate_contribution_weighted_quality()

        if self._quality_method == AssetQualityMethod.CORRELATION_ADJUSTED:
            return self._calculate_correlation_adjusted_quality()

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

    def _calculate_minimum_quality(self) -> Tuple[float, str]:
        """Calculate quality as minimum of all child qualities.

        Formula: min(quality_1, quality_2, ..., quality_n)
        Conservative approach: parent is only as good as its weakest child.
        """
        qualities = [report.get("quality", 0) for report in self._reports.values() if report.get("allocation", 0) > 0]

        if not qualities:
            return 0.0, AssetQualityMethod.MINIMUM.value

        return round(min(qualities), 4), AssetQualityMethod.MINIMUM.value

    def _calculate_contribution_weighted_quality(self) -> Tuple[float, str]:
        """Calculate quality weighted by absolute P&L contribution.

        Formula: sum(quality_i * abs(performance_i)) / sum(abs(performance_i))
        Children with higher impact (positive or negative) weight more.
        """
        total_abs_performance = 0.0
        weighted_quality_sum = 0.0

        for report in self._reports.values():
            performance = report.get("performance", 0)
            quality = report.get("quality", 0)
            abs_performance = abs(performance)

            if abs_performance > 0:
                weighted_quality_sum += quality * abs_performance
                total_abs_performance += abs_performance

        if total_abs_performance == 0:
            return self._calculate_weighted_average_quality()

        aggregated_quality = weighted_quality_sum / total_abs_performance
        return round(aggregated_quality, 4), AssetQualityMethod.CONTRIBUTION_WEIGHTED.value

    def _calculate_correlation_adjusted_quality(self) -> Tuple[float, str]:
        """Calculate quality adjusted for child correlation.

        Penalizes highly correlated children (less diversification benefit).
        Uses performance_history from each child to compute correlations.

        If correlation data is unavailable, falls back to weighted average.
        """
        performance_histories: List[List[float]] = []
        qualities: List[float] = []
        allocations: List[float] = []

        for report in self._reports.values():
            history: List[float] = report.get("performance_history", [])
            quality: float = report.get("quality", 0)
            allocation: float = report.get("allocation", 0)

            if len(history) >= self.MIN_HISTORY_LENGTH_FOR_CORRELATION and allocation > 0:
                performance_histories.append(history)
                qualities.append(quality)
                allocations.append(allocation)

        if len(performance_histories) < self.MIN_STRATEGIES_FOR_CORRELATION:
            return self._calculate_weighted_average_quality()

        min_length = min(len(h) for h in performance_histories)
        trimmed_histories: List[List[float]] = [h[:min_length] for h in performance_histories]

        try:
            correlation_matrix: NDArray[np.floating[Any]] = np.corrcoef(trimmed_histories)

            if np.isnan(correlation_matrix).any():
                return self._calculate_weighted_average_quality()

            num_children = len(qualities)
            total_weight = sum(allocations)
            weights: List[float] = [a / total_weight for a in allocations]

            adjusted_qualities: List[float] = []
            for i in range(num_children):
                avg_correlation = 0.0
                for j in range(num_children):
                    if i != j:
                        avg_correlation += float(abs(correlation_matrix[i][j])) * weights[j]

                diversification_factor = max(
                    self.MIN_DIVERSIFICATION_FACTOR,
                    min(
                        self.MAX_DIVERSIFICATION_FACTOR,
                        1 - (avg_correlation * self.CORRELATION_PENALTY_FACTOR),
                    ),
                )

                adjusted_qualities.append(qualities[i] * diversification_factor)

            weighted_sum = sum(q * w for q, w in zip(adjusted_qualities, weights, strict=True))
            return (
                round(weighted_sum, 4),
                AssetQualityMethod.CORRELATION_ADJUSTED.value,
            )

        except (ValueError, np.linalg.LinAlgError):
            return self._calculate_weighted_average_quality()
