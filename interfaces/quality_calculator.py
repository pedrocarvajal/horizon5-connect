"""Quality calculator interface for aggregating child reports into quality metrics."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class QualityCalculatorInterface(ABC):
    """Interface for services that aggregate child reports and calculate quality metrics."""

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
