"""MetaAPI kline component for candlestick data retrieval."""

from collections.abc import Callable
from datetime import datetime
from time import sleep
from typing import Any, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_kline import GatewayKlineModel

TIMEFRAME_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
    "1mn": 2592000,
}


class KlineComponent(BaseComponent):
    """
    Component for handling MetaAPI kline (candlestick) operations.

    Retrieves historical candlestick data from MetaAPI for MetaTrader accounts.
    Handles pagination, data adaptation to internal models, and rate limiting.

    Attributes:
        Inherits _config and _log from BaseComponent.
    """

    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        *,
        callback: Callable[[list[GatewayKlineModel]], None],
        limit: int = 1000,
    ) -> None:
        """
        Retrieve historical klines from MetaAPI.

        Fetches klines for the specified symbol and timeframe within the given
        date range. MetaAPI returns data in reverse chronological order, so this
        method accumulates all data and delivers it in forward chronological order
        (oldest to newest) for consistent chronological processing.

        Args:
            symbol: Trading symbol (e.g., "XAUUSD", "EURUSD").
            timeframe: Kline interval (e.g., "1m", "5m", "1h", "1d").
            from_date: Start timestamp in seconds (Unix timestamp).
            to_date: End timestamp in seconds (Unix timestamp).
            callback: Callback function that receives batches of klines.
            limit: Maximum klines per API request (default: 1000, max: 1000).
        """
        if not self._validate_get_klines_params(
            symbol=symbol,
            timeframe=timeframe,
            from_date=from_date,
            to_date=to_date,
        ):
            callback([])
            return

        if not self._config.account_id:
            self._log.error("account_id is required")
            callback([])
            return

        all_klines: list[GatewayKlineModel] = []
        current_end = self._to_iso_string(to_date)
        total_range = to_date - from_date if from_date and to_date else 1

        while True:
            klines = self._fetch_klines_batch(
                symbol=symbol,
                timeframe=timeframe,
                start_time=current_end,
                limit=limit,
            )

            if not klines:
                break

            filtered_klines = (
                [kline for kline in klines if kline.open_time >= from_date] if from_date is not None else klines
            )
            all_klines.extend(filtered_klines)
            oldest_kline = min(klines, key=lambda k: k.open_time)
            downloaded_range = to_date - oldest_kline.open_time if to_date else 0
            progress = min((downloaded_range / total_range) * 100, 100.0) if total_range > 0 else 100.0
            current_oldest = datetime.fromtimestamp(oldest_kline.open_time, tz=TIMEZONE)
            target_date = datetime.fromtimestamp(from_date, tz=TIMEZONE) if from_date else None

            log_message = (
                f"[MetaAPI] {symbol} | Reached: {current_oldest:%Y-%m-%d %H:%M} | "
                + f"Target: {target_date:%Y-%m-%d %H:%M} | Progress: {progress:.2f}%"
            )

            self._log.info(log_message)

            if from_date is not None and oldest_kline.open_time <= from_date:
                break

            current_end = self._to_iso_string(oldest_kline.open_time)
            sleep(0.1)

        if not all_klines:
            callback([])
            return

        all_klines.sort(key=lambda k: k.open_time)
        batch_size = limit

        for i in range(0, len(all_klines), batch_size):
            batch = all_klines[i : i + batch_size]
            callback(batch)

        callback([])

    def _fetch_klines_batch(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[str],
        limit: int,
    ) -> list[GatewayKlineModel]:
        """
        Fetch a single batch of klines from MetaAPI.

        Args:
            symbol: Trading symbol.
            timeframe: Kline interval.
            start_time: Start time in ISO 8601 format.
            limit: Maximum number of klines.

        Returns:
            list[GatewayKlineModel]: List of kline models. Returns empty list if
                request fails or error occurs.
        """
        endpoint = (
            f"/users/current/accounts/{self._config.account_id}"
            f"/historical-market-data/symbols/{symbol}"
            f"/timeframes/{timeframe}/candles"
        )

        params: dict[str, Any] = {"limit": limit}

        if start_time:
            params["startTime"] = start_time

        response = self._execute(
            method="GET",
            endpoint=endpoint,
            params=params,
        )

        if not response or not isinstance(response, list):
            return []

        return self._adapt_klines_batch(response, symbol, timeframe)

    def _adapt_klines_batch(
        self,
        response: list[dict[str, Any]],
        symbol: str,
        timeframe: str,
    ) -> list[GatewayKlineModel]:
        """
        Adapt MetaAPI response to GatewayKlineModel list.

        Converts MetaAPI candle format to internal GatewayKlineModel instances.
        Each candle contains: time, open, high, low, close, tickVolume.

        Args:
            response: List of candle objects from MetaAPI.
            symbol: Trading symbol.
            timeframe: Timeframe for calculating close_time.

        Returns:
            list[GatewayKlineModel]: List of adapted kline models.
        """
        timeframe_seconds = TIMEFRAME_SECONDS.get(timeframe, 3600)
        klines: list[GatewayKlineModel] = []

        for item in response:
            open_time = self._parse_iso_timestamp(item.get("time", ""))

            if open_time == 0:
                continue

            close_time = open_time + timeframe_seconds

            kline = GatewayKlineModel(
                source="metaapi",
                symbol=symbol,
                open_time=open_time,
                open_price=float(item.get("open", 0)),
                high_price=float(item.get("high", 0)),
                low_price=float(item.get("low", 0)),
                close_price=float(item.get("close", 0)),
                volume=float(item.get("tickVolume", 0)),
                close_time=close_time,
                quote_asset_volume=0.0,
                number_of_trades=0,
                taker_buy_base_asset_volume=0.0,
                taker_buy_quote_asset_volume=0.0,
                response=item,
            )
            klines.append(kline)

        return klines

    def _parse_iso_timestamp(self, iso_string: str) -> int:
        """
        Parse ISO 8601 timestamp to Unix timestamp seconds.

        Args:
            iso_string: ISO 8601 formatted datetime string.

        Returns:
            Unix timestamp in seconds, or 0 if parsing fails.
        """
        if not iso_string:
            return 0

        try:
            normalized_iso_string = iso_string.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized_iso_string)
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            self._log.error(f"Failed to parse timestamp: {iso_string}")
            return 0

    def _to_iso_string(self, timestamp: Optional[int]) -> Optional[str]:
        """
        Convert Unix timestamp to ISO 8601 string.

        Args:
            timestamp: Unix timestamp in seconds.

        Returns:
            ISO 8601 formatted string, or None.
        """
        if timestamp is None:
            return None

        dt = datetime.fromtimestamp(timestamp, tz=TIMEZONE)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

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

        if not timeframe:
            self._log.error("timeframe is required")
            return False

        if timeframe not in TIMEFRAME_SECONDS:
            self._log.error(f"Invalid timeframe: {timeframe}")
            return False

        if from_date is None:
            self._log.error("from_date is required")
            return False

        if to_date is None:
            self._log.error("to_date is required")
            return False

        return True
