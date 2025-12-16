"""MetaAPI stream component for REST-based market data polling."""

import asyncio
import datetime
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar, Dict, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.helpers.parse_optional_float import parse_optional_float
from vendor.models.tick import TickModel
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent


class StreamComponent(BaseComponent):
    """
    Component for handling MetaAPI market data streaming via REST polling.

    Uses the readTick REST endpoint with keepSubscription=true to poll
    for real-time price updates. This approach works with all account types
    including MT5 G2 which doesn't support WebSocket streaming.
    """

    DEFAULT_POLL_INTERVAL_SECONDS: ClassVar[float] = 0.5
    MIN_POLL_INTERVAL_SECONDS: ClassVar[float] = 0.25

    def __init__(self, config: Any) -> None:
        """Initialize the stream component."""
        super().__init__(config)
        self._running: bool = False
        self._callback: Optional[Callable[[TickModel], Awaitable[None]]] = None
        self._symbols: List[str] = []
        self._poll_interval: float = self.DEFAULT_POLL_INTERVAL_SECONDS
        self._last_tick_times: Dict[str, str] = {}

    async def stream(
        self,
        symbols: List[str],
        callback: Callable[[TickModel], Awaitable[None]],
        poll_interval: Optional[float] = None,
    ) -> None:
        """
        Stream real-time price data from MetaAPI via REST polling.

        Polls the readTick endpoint at regular intervals and invokes
        the callback with new tick data.

        Args:
            symbols: List of trading symbols to stream (e.g., ["XAUUSD", "EURUSD"]).
            callback: Async callback function that receives TickModel instances.
            poll_interval: Polling interval in seconds (default: 1.0, min: 0.5).
        """
        if not self._validate_stream_params(symbols=symbols):
            return

        if not self._config.account_id or not self._config.auth_token:
            self._log.error("account_id and auth_token required for streaming")
            return

        self._callback = callback
        self._symbols = [s.upper() for s in symbols]
        self._running = True
        self._last_tick_times = {}

        if poll_interval is not None:
            self._poll_interval = max(poll_interval, self.MIN_POLL_INTERVAL_SECONDS)

        self._log.info(
            "Starting REST-based streaming",
            symbols=self._symbols,
            poll_interval=self._poll_interval,
        )

        await self._subscribe_to_symbols()

        try:
            while self._running:
                await self._poll_ticks()
                await asyncio.sleep(self._poll_interval)
        except asyncio.CancelledError:
            self._log.info("Stream polling cancelled")
        finally:
            self._running = False

    async def stop(self) -> None:
        """Stop the streaming polling."""
        self._running = False
        self._log.info("Stream polling stopped")

    def _adapt_tick_from_response(
        self,
        tick_data: Dict[str, Any],
    ) -> TickModel:
        """
        Adapt MetaAPI tick response to TickModel.

        Args:
            tick_data: Dictionary containing MetaAPI tick data with keys:
                - bid: Bid price
                - ask: Ask price
                - time: ISO timestamp

        Returns:
            TickModel instance with price, bid, ask, and timestamp data.
        """
        bid = parse_optional_float(value=tick_data.get("bid", 0)) or 0.0
        ask = parse_optional_float(value=tick_data.get("ask", 0)) or 0.0
        price = (bid + ask) / 2 if bid and ask else 0.0

        time_str = tick_data.get("time", "")
        timestamp = self._parse_timestamp(time_str=time_str)

        return TickModel(
            is_simulated=False,
            close_price=price,
            bid_price=bid,
            ask_price=ask,
            date=timestamp or datetime.datetime.now(tz=TIMEZONE),
        )

    async def _fetch_tick(
        self,
        symbol: str,
        keep_subscription: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current tick data for a symbol.

        Args:
            symbol: Trading symbol to fetch tick for.
            keep_subscription: Whether to maintain long-term subscription.

        Returns:
            Dictionary with tick data or None if request fails.
        """
        endpoint = f"/users/current/accounts/{self._config.account_id}/symbols/{symbol}/current-tick"
        params = {"keepSubscription": "true" if keep_subscription else "false"}

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            params=params,
            use_client_api=True,
        )

        if not response or not isinstance(response, dict):
            return None

        return response

    def _parse_timestamp(
        self,
        time_str: str,
    ) -> Optional[datetime.datetime]:
        """Parse ISO timestamp string to datetime."""
        if not time_str:
            return None

        try:
            time_str_clean = time_str.replace("Z", "+00:00")
            parsed = datetime.datetime.fromisoformat(time_str_clean)
            return parsed.astimezone(TIMEZONE)
        except (ValueError, AttributeError):
            return None

    async def _poll_ticks(self) -> None:
        """Poll for tick updates for all subscribed symbols."""
        for symbol in self._symbols:
            tick_data = await self._fetch_tick(symbol=symbol, keep_subscription=True)

            if tick_data and self._callback:
                tick_time = tick_data.get("time", "")

                if tick_time != self._last_tick_times.get(symbol):
                    self._last_tick_times[symbol] = tick_time
                    tick = self._adapt_tick_from_response(tick_data=tick_data)
                    await self._callback(tick)

    async def _subscribe_to_symbols(self) -> None:
        """Initialize subscriptions for all symbols with keepSubscription=true."""
        for symbol in self._symbols:
            await self._fetch_tick(symbol=symbol, keep_subscription=True)
            self._log.info("Subscribed to symbol", symbol=symbol)

    def _validate_stream_params(
        self,
        symbols: List[str],
    ) -> bool:
        """Validate stream parameters."""
        if not symbols:
            self._log.error("symbols is required")
            return False

        for symbol in symbols:
            if not symbol:
                self._log.error("symbol item cannot be empty")
                return False

        return True
