"""Portfolio gateway component utilities."""

from __future__ import annotations

from multiprocessing import Queue
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.gateway import GatewayInterface
from vendor.services.gateway import GatewayService


class Gateway(BaseModel):
    """Gateway wrapper holding the exchange data client."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    gateway: GatewayInterface


class GatewayComponent:
    """Component managing gateway connections for portfolio assets."""

    _portfolio_id: str
    _backtest_id: Optional[str]
    _gateways: Dict[str, Gateway]

    _commands_queue: Optional[Queue[Any]]

    def __init__(
        self,
        portfolio_id: str,
        assets: List[AssetInterface],
        backtest_id: Optional[str] = None,
        commands_queue: Optional[Queue[Any]] = None,
    ) -> None:
        """Initialize gateway component with assets.

        Args:
            portfolio_id: Identifier of the portfolio.
            assets: List of assets to create gateways for.
            backtest_id: Backtest identifier.
            commands_queue: Queue for commands.
        """
        self._portfolio_id = portfolio_id
        self._backtest_id = backtest_id
        self._commands_queue = commands_queue

        self._gateways = {}

        for gateway_name in {asset.gateway_name for asset in assets}:
            gateway_service = GatewayService(gateway_name)

            self._gateways[gateway_name] = Gateway(
                gateway=gateway_service,
            )

    def get(self, gateway: str) -> Gateway | None:
        """Retrieve a gateway by its identifier."""
        return self._gateways.get(gateway)

    @property
    def gateways(self) -> Dict[str, Gateway]:
        """Return dictionary of gateway interfaces by name."""
        return self._gateways
