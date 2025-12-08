"""Quality calculator interface for aggregating child reports into quality metrics."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from enums.asset_quality_method import AssetQualityMethod


class QualityCalculatorInterface(ABC):
    """Interface for services that aggregate child reports and calculate quality metrics."""

    _quality_method: AssetQualityMethod

    @abstractmethod
    def on_end(self) -> Dict[str, Any]:
        """Build and return the aggregated report.

        Returns:
            Dictionary containing aggregated metrics and quality.
        """
        pass

    @abstractmethod
    def on_report(self, report_id: str, report: Dict[str, Any]) -> None:
        """Handle a child report (strategy or asset).

        Args:
            report_id: Unique identifier for the report.
            report: Dictionary containing the child report data.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset collected reports."""
        pass

    @property
    def quality_method(self) -> AssetQualityMethod:
        """Return the current quality aggregation method."""
        return self._quality_method

    @quality_method.setter
    def quality_method(self, value: AssetQualityMethod) -> None:
        """Set the quality aggregation method."""
        self._quality_method = value
