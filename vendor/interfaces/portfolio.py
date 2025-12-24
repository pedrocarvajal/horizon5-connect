"""Portfolio interface for multi-asset container."""

from abc import ABC
from typing import Any, Dict, List

from vendor.interfaces.asset import AssetInterface
from vendor.models.tick import TickModel


class PortfolioInterface(ABC):
    """Abstract interface for portfolio containing multiple trading assets."""

    _name: str
    _id: str
    _allocation: float
    _assets: List[AssetInterface]

    @property
    def id(self) -> str:
        """Return the portfolio identifier."""
        return self._id

    @property
    def name(self) -> str:
        """Return the portfolio name."""
        return self._name

    @property
    def allocation(self) -> float:
        """Return the portfolio allocation."""
        return self._allocation

    @property
    def assets(self) -> List[AssetInterface]:
        """Return the list of assets."""
        return self._assets

    def setup(self, **kwargs: Any) -> None:  # noqa: B027
        """Configure the portfolio with runtime parameters."""
        pass

    def setup_analytic(self, **kwargs: Any) -> None:  # noqa: B027
        """Initialize the portfolio analytics service.

        This method can be called separately when assets are setup externally
        (e.g., by BacktestService for parallel downloads).

        Args:
            **kwargs: Configuration parameters for analytics.
        """
        pass

    def on_tick(self, ticks: Dict[str, TickModel]) -> None:  # noqa: B027
        """Process tick data for all assets.

        Args:
            ticks: Dictionary mapping symbol to tick data.
        """
        pass

    def on_end(self) -> Dict[str, Any]:
        """Finalize portfolio and return aggregated report."""
        return {}
