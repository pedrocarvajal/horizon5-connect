"""Portfolio orderbook component utilities."""

from __future__ import annotations

from multiprocessing import Queue
from typing import Any, Callable, Dict, List, Optional

from vendor.interfaces.asset import AssetInterface
from vendor.interfaces.orderbook import OrderbookInterface
from vendor.models.order import OrderModel
from vendor.services.orderbook import OrderbookService


class OrderbookComponent:
    """Component managing orderbook connections and orderbooks for portfolio assets."""

    _portfolio_id: str
    _backtest_id: Optional[str]
    _on_transaction: Callable[[OrderModel], None]
    _orderbooks: Dict[str, OrderbookInterface]

    _commands_queue: Optional[Queue[Any]]

    def __init__(
        self,
        portfolio_id: str,
        assets: List[AssetInterface],
        on_transaction: Callable[[OrderModel], None],
        backtest_id: Optional[str] = None,
        commands_queue: Optional[Queue[Any]] = None,
    ) -> None:
        """Initialize orderbook component with assets.

        Args:
            portfolio_id: Identifier of the portfolio.
            assets: List of assets to create orderbooks for.
            on_transaction: Callback for order transactions.
            backtest_id: Backtest identifier.
            commands_queue: Queue for commands.
        """
        self._portfolio_id = portfolio_id
        self._backtest_id = backtest_id
        self._on_transaction = on_transaction
        self._commands_queue = commands_queue

        self._orderbooks = {}

        for asset in assets:
            self._orderbooks[asset.symbol] = OrderbookService(
                backtest_id=self._backtest_id,
                asset=asset,
                on_transaction=self._on_transaction,
            )

    def get(self, symbol: str) -> OrderbookInterface:
        """Retrieve a orderbook by its symbol.

        Args:
            symbol: The symbol identifier to look up.

        Returns:
            The Orderbook instance for the symbol.

        Raises:
            KeyError: If symbol not found.
        """
        return self._orderbooks[symbol]
