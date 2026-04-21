"""Gateway interface for historical data retrieval."""

from abc import ABC, abstractmethod
from typing import Any


class GatewayInterface(ABC):
    """Abstract interface for exchange/gateway integrations (backtest data only)."""

    @abstractmethod
    def get_klines(
        self,
        **kwargs: Any,
    ) -> None:
        """Retrieve candlestick/kline data from the exchange."""
        pass
