"""Gateway service facade for exchange data retrieval."""

from typing import Any, Dict

from vendor.configs.gateways import GATEWAYS
from vendor.interfaces.gateway import GatewayInterface
from vendor.interfaces.logging import LoggingInterface
from vendor.services.logging import LoggingService


class GatewayService(GatewayInterface):
    """Facade for gateway implementations used to fetch historical data."""

    _name: str
    _gateways: Dict[str, Any]

    _gateway: GatewayInterface
    _log: LoggingInterface

    def __init__(
        self,
        gateway: str,
    ) -> None:
        """Initialize the gateway service and instantiate its implementation."""
        self._log = LoggingService()

        self._gateways = GATEWAYS
        self._name = gateway

        self._setup()

    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """Delegate kline retrieval to the underlying gateway implementation."""
        self._gateway.get_klines(**kwargs)

    def _setup(self) -> None:
        """Validate gateway name and instantiate the implementation."""
        if self._name not in self._gateways:
            raise ValueError(f"Gateway {self._name} not found")

        self._log.info(f"Setting up gateway {self._name}")

        gateway_config = self._gateways[self._name]
        gateway_kwargs = gateway_config["kwargs"].copy()

        self._gateway = gateway_config["class"](**gateway_kwargs)

    @property
    def name(self) -> str:
        """Return the gateway name."""
        return self._name
