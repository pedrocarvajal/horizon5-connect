"""Base component class for Binance API operations."""

from vendor.services.gateway.gateways.binance.models.config import BinanceConfigModel
from vendor.services.logging import LoggingService


class BaseComponent:
    """Base class providing common functionality for Binance API components."""

    _config: BinanceConfigModel
    _log: LoggingService

    def __init__(
        self,
        config: BinanceConfigModel,
    ) -> None:
        """Initialize the component with configuration."""
        self._config = config
        self._log = LoggingService()
