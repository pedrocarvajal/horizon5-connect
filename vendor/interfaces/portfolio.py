"""Portfolio interface for multi-asset container."""

from abc import ABC
from typing import Any, Dict, List, Type

from typing_extensions import NotRequired, TypedDict

from vendor.interfaces.asset import AssetInterface
from vendor.models.tick import TickModel


class AssetConfig(TypedDict):
    """Configuration for an asset in a portfolio."""

    asset: Type[AssetInterface]
    allocation: float
    enabled: NotRequired[bool]


class PortfolioInterface(ABC):
    """Abstract interface for portfolio containing multiple trading assets."""

    _id: str
    _assets: List[AssetConfig]
    _asset_instances: List[AssetInterface]

    @property
    def id(self) -> str:
        """Return the portfolio identifier."""
        return self._id

    @property
    def assets(self) -> List[AssetConfig]:
        """Return the list of asset configurations."""
        return self._assets

    @property
    def asset_instances(self) -> List[AssetInterface]:
        """Return the list of instantiated assets."""
        return self._asset_instances

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
