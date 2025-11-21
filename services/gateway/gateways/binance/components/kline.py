# Code reviewed on 2025-11-19 by pedrocarvajal

from collections.abc import Callable
from datetime import datetime
from time import sleep
from typing import Any, List, Optional

import requests

from configs.timezone import TIMEZONE
from enums.http_status import HttpStatus
from helpers.parse import parse_timestamp_ms
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error
from services.gateway.models.gateway_kline import GatewayKlineModel


class KlineComponent(BaseComponent):
    """
    Component for handling Binance kline (candlestick) operations.

    Provides methods to retrieve historical candlestick data from Binance Futures API.
    Handles kline data retrieval, pagination, validation, and adaptation to internal models.

    Attributes:
        Inherits _config and _log from BaseComponent.
    """

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        *,
        callback: Callable[[List[GatewayKlineModel]], None],
        limit: int = 1000,
    ) -> None:
        """
        Retrieve historical klines (candlestick data) from Binance.

        Fetches klines for the specified symbol and timeframe within the given date range.
        Automatically handles pagination to retrieve all klines in the range. Results are
        delivered incrementally via the callback function as batches are retrieved.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            timeframe: Kline interval (e.g., "1m", "5m", "1h", "1d").
            from_date: Start timestamp in seconds (Unix timestamp).
            to_date: End timestamp in seconds (Unix timestamp).
            callback: Callback function that receives batches of klines as they are retrieved.
                Called with an empty list when validation fails or an error occurs.
            limit: Maximum number of klines per API request (default: 1000, max: 1000).

        Example:
            >>> component = KlineComponent(config)
            >>> def handle_klines(klines):
            ...     print(f"Received {len(klines)} klines")
            >>> component.get_klines(
            ...     symbol="BTCUSDT",
            ...     timeframe="1d",
            ...     from_date=1704067200,
            ...     to_date=1704153600,
            ...     callback=handle_klines,
            ... )
        """
        if not self._validate_get_klines_params(
            symbol=symbol,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
        ):
            callback([])
            return

        from_date_ms, to_date_ms = self._convert_dates_to_milliseconds(
            from_date=from_date,
            to_date=to_date,
        )

        while True:
            if from_date_ms > to_date_ms:
                callback([])
                break

            klines = self._fetch_klines_batch(
                symbol=symbol,
                timeframe=timeframe,
                from_date_ms=from_date_ms,
                to_date_ms=to_date_ms,
                limit=limit,
            )

            if not klines:
                callback([])
                break

            last_kline = klines[-1]
            from_date_ms = int(last_kline.close_time * 1000)
            sleep(0.25)

            callback(klines)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_get_klines_params(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
    ) -> bool:
        """
        Validate parameters for get_klines method.

        Args:
            symbol: Trading symbol to validate.
            timeframe: Timeframe string to validate.
            from_date: Start timestamp to validate.
            to_date: End timestamp to validate.

        Returns:
            bool: True if all validations pass, False otherwise.
        """
        if not symbol:
            self._log.error("symbol is required")
            return False

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            return False

        if not timeframe:
            self._log.error("timeframe is required")
            return False

        if not isinstance(timeframe, str):
            self._log.error("timeframe must be a string")
            return False

        if from_date is None:
            self._log.error("from_date is required")
            return False

        if to_date is None:
            self._log.error("to_date is required")
            return False

        return True

    def _convert_dates_to_milliseconds(
        self,
        from_date: Optional[int],
        to_date: Optional[int],
    ) -> tuple[int, int]:
        """
        Convert Unix timestamps (seconds) to milliseconds.

        Args:
            from_date: Start timestamp in seconds.
            to_date: End timestamp in seconds.

        Returns:
            tuple[int, int]: Tuple containing (from_date_ms, to_date_ms) in milliseconds.
        """
        assert from_date is not None, "from_date must not be None"
        assert to_date is not None, "to_date must not be None"

        from_date_dt = datetime.fromtimestamp(from_date, tz=TIMEZONE)
        to_date_dt = datetime.fromtimestamp(to_date, tz=TIMEZONE)
        from_date_ms = parse_timestamp_ms(from_date_dt)
        to_date_ms = parse_timestamp_ms(to_date_dt)

        return from_date_ms, to_date_ms

    def _fetch_klines_batch(
        self,
        symbol: str,
        timeframe: str,
        from_date_ms: int,
        to_date_ms: int,
        limit: int,
    ) -> List[GatewayKlineModel]:
        """
        Fetch a single batch of klines from Binance API.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT").
            timeframe: Kline interval (e.g., "1m", "5m", "1h", "1d").
            from_date_ms: Start timestamp in milliseconds.
            to_date_ms: End timestamp in milliseconds.
            limit: Maximum number of klines to retrieve per request.

        Returns:
            List[GatewayKlineModel]: List of kline models. Returns empty list if
                request fails or error occurs.
        """
        try:
            response = requests.get(
                f"{self._config.fapi_url}/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": timeframe,
                    "startTime": from_date_ms,
                    "endTime": to_date_ms,
                    "limit": limit,
                },
            )

            if not HttpStatus.is_success_code(response.status_code):
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return []

            response_data = response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching klines: {e}")
            return []

        return self._handle_klines_response(
            response=response_data,
            symbol=symbol,
        )

    def _handle_klines_response(
        self,
        response: Any,
        symbol: str,
    ) -> List[GatewayKlineModel]:
        """
        Handle and validate API response for klines request.

        Args:
            response: API response data (can be dict, list, or None).
            symbol: Trading symbol for adaptation.

        Returns:
            List[GatewayKlineModel]: List of adapted kline models. Returns empty list
                if response is invalid, contains errors, or is not a list.
        """
        if not response:
            return []

        has_error, error_msg, error_code = has_api_error(
            response=response,
        )

        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return []

        if not isinstance(response, list):
            self._log.error(f"Unexpected response type: {type(response)}")
            return []

        return self._adapt_klines_batch(
            response=response,
            symbol=symbol,
        )

    def _adapt_klines_batch(
        self,
        response: List[Any],
        symbol: str,
    ) -> List[GatewayKlineModel]:
        """
        Adapt a batch of kline responses from Binance API to GatewayKlineModel list.

        Converts Binance kline array format to internal GatewayKlineModel instances.
        Each kline array contains: [open_time, open, high, low, close, volume,
        close_time, quote_volume, trades, taker_buy_base, taker_buy_quote].

        Args:
            response: List of kline arrays from Binance API.
            symbol: Trading symbol to include in models.

        Returns:
            List[GatewayKlineModel]: List of adapted kline models.
        """
        return [
            GatewayKlineModel(
                source="binance",
                symbol=symbol,
                open_time=int(float(item[0]) / 1000),
                open_price=float(item[1]),
                high_price=float(item[2]),
                low_price=float(item[3]),
                close_price=float(item[4]),
                volume=float(item[5]),
                close_time=int(float(item[6]) / 1000),
                quote_asset_volume=float(item[7]),
                number_of_trades=int(item[8]),
                taker_buy_base_asset_volume=float(item[9]),
                taker_buy_quote_asset_volume=float(item[10]),
                response=item,
            )
            for item in response
        ]
