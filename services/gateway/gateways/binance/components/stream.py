# Code reviewed on 2025-01-27 by pedrocarvajal

import datetime
import json
from collections.abc import Awaitable, Callable
from typing import ClassVar, Dict, List

import websockets

from configs.timezone import TIMEZONE
from helpers.parse import parse_optional_float
from models.tick import TickModel
from services.gateway.gateways.binance.components.base import BaseComponent


class StreamComponent(BaseComponent):
    """
    Component for handling Binance WebSocket streaming operations.

    Provides methods to establish WebSocket connections and stream real-time market data
    from Binance Futures API. Handles stream validation, connection management, message
    processing, and adaptation of Binance stream data to internal tick models.

    Attributes:
        SUPPORTED_STREAM_TYPES: List of supported stream type suffixes.
        Inherits _config and _log from BaseComponent.
    """

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    SUPPORTED_STREAM_TYPES: ClassVar[List[str]] = ["bookTicker"]

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    async def stream(
        self,
        streams: List[str],
        callback: Callable[[TickModel], Awaitable[None]],
    ) -> None:
        """
        Stream real-time data from Binance via WebSocket.

        Establishes a WebSocket connection to Binance Futures API and streams market data.
        Validates streams and callback parameters, connects to the WebSocket endpoint,
        and processes incoming messages. Each message is parsed and adapted to a TickModel,
        which is then passed to the provided callback function.

        Args:
            streams: List of stream names to subscribe to (e.g., ["btcusdt@bookTicker"]).
            callback: Async callback function that receives TickModel instances as data arrives.
                Must be an async function that accepts a single TickModel parameter.

        Example:
            >>> component = StreamComponent(config)
            >>> async def handle_tick(tick: TickModel) -> None:
            ...     print(f"Price: {tick.price}, Bid: {tick.bid_price}, Ask: {tick.ask_price}")
            >>> await component.stream(
            ...     streams=["btcusdt@bookTicker"],
            ...     callback=handle_tick,
            ... )
        """
        if not self._validate_streams(streams=streams):
            return

        if not self._validate_callback(callback=callback):
            return

        if not self._validate_supported_streams(streams=streams):
            return

        url = self._build_stream_url(streams=streams)

        async with websockets.connect(url) as websocket:
            async for message in websocket:
                await self._process_websocket_message(
                    message=message,
                    callback=callback,
                )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_streams(
        self,
        streams: List[str],
    ) -> bool:
        """
        Validate the streams parameter.

        Args:
            streams: List of stream names to validate.

        Returns:
            bool: True if streams are valid, False otherwise.
        """
        if not streams:
            self._log.error("streams is required")
            return False

        if not isinstance(streams, list):
            self._log.error("streams must be a list")
            return False

        if len(streams) == 0:
            self._log.error("streams must not be empty")
            return False

        for stream in streams:
            if not stream:
                self._log.error("stream item cannot be empty")
                return False

            if not isinstance(stream, str):
                self._log.error("all stream items must be strings")
                return False

        return True

    def _validate_callback(
        self,
        callback: Callable[[TickModel], Awaitable[None]],
    ) -> bool:
        """
        Validate the callback parameter.

        Args:
            callback: Callback function to validate.

        Returns:
            bool: True if callback is valid, False otherwise.
        """
        if not callback:
            self._log.error("callback is required")
            return False

        if not callable(callback):
            self._log.error("callback must be callable")
            return False

        return True

    def _validate_supported_streams(
        self,
        streams: List[str],
    ) -> bool:
        """
        Validate that all streams are supported types.

        Args:
            streams: List of stream names to validate.

        Returns:
            bool: True if all streams are supported, False otherwise.
        """
        for stream in streams:
            if not any(stream.endswith(suffix) for suffix in self.SUPPORTED_STREAM_TYPES):
                self._log.error(f"Unsupported stream: {stream}")
                return False

        return True

    def _build_stream_url(
        self,
        streams: List[str],
    ) -> str:
        """
        Build the WebSocket URL from stream names.

        Args:
            streams: List of stream names.

        Returns:
            str: Complete WebSocket URL for the streams.
        """
        stream_path = "/".join(streams)
        return f"{self._config.fapi_ws_url}/{stream_path}"

    async def _process_websocket_message(
        self,
        message: str,
        callback: Callable[[TickModel], Awaitable[None]],
    ) -> None:
        """
        Process a single WebSocket message.

        Parses the JSON message, validates the event type, adapts the data to a TickModel,
        and calls the callback with the tick data. Logs errors for unsupported events or
        parsing failures.

        Args:
            message: Raw WebSocket message string (JSON format).
            callback: Async callback function to invoke with the parsed tick data.
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            self._log.error(f"Error parsing message: {e}")
            return

        if not data or data.get("e") != "bookTicker":
            self._log.error(f"Unsupported event: {data.get('e') if data else 'None'}")
            return

        tick = self._adapt_tick_from_stream(response=data)
        await callback(tick)

    def _adapt_tick_from_stream(
        self,
        response: Dict[str, str],
    ) -> TickModel:
        """
        Adapt Binance stream response to TickModel.

        Extracts bid and ask prices from the Binance bookTicker stream response,
        calculates the mid price, and creates a TickModel instance with the current
        timestamp.

        Args:
            response: Dictionary containing Binance stream data with keys:
                - "b": Best bid price (string)
                - "a": Best ask price (string)

        Returns:
            TickModel: Instance containing price, bid, ask, and timestamp data.
        """
        best_bid = parse_optional_float(value=response.get("b", "0.0"))
        best_ask = parse_optional_float(value=response.get("a", "0.0"))
        price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0

        return TickModel(
            is_simulated=False,
            price=price,
            bid_price=best_bid,
            ask_price=best_ask,
            date=datetime.datetime.now(tz=TIMEZONE),
        )
