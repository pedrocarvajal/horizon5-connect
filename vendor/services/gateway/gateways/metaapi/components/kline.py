"""MetaAPI kline component for candlestick data retrieval."""

from collections.abc import Callable
from datetime import datetime
from time import sleep
from typing import Any, Dict, List, Optional

from vendor.configs.timezone import TIMEZONE
from vendor.services.gateway.gateways.metaapi.components.base import BaseComponent
from vendor.services.gateway.models.gateway_kline import GatewayKlineModel

TIMEFRAME_SECONDS = {
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
    """

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
        Retrieve historical klines from MetaAPI.

        Fetches klines for the specified symbol and timeframe within the given
        date range. Handles pagination automatically and delivers results via
        callback as batches are retrieved.

        Args:
            symbol: Trading symbol (e.g., "XAUUSD", "EURUSD").
            timeframe: Kline interval (e.g., "1m", "5m", "1h", "1d").
            from_date: Start timestamp in seconds (Unix timestamp).
            to_date: End timestamp in seconds (Unix timestamp).
            callback: Callback function that receives batches of klines.
            limit: Maximum klines per API request (default: 1000, max: 1000).
        """
        if not self._validate_params(symbol, timeframe, from_date, to_date):
            callback([])
            return

        if not self._config.account_id:
            self._log.error("account_id is required")
            callback([])
            return

        current_end = self._to_iso_string(to_date)

        while True:
            klines = self._fetch_klines_batch(
                symbol=symbol,
                timeframe=timeframe,
                start_time=current_end,
                limit=limit,
            )

            if not klines:
                callback([])
                break

            filtered_klines = [kline for kline in klines if kline.open_time >= from_date]

            if filtered_klines:
                filtered_klines.sort(key=lambda k: k.open_time)
                callback(filtered_klines)

            oldest_kline = min(klines, key=lambda k: k.open_time)
            if oldest_kline.open_time <= from_date:
                callback([])
                break

            current_end = self._to_iso_string(oldest_kline.open_time)
            sleep(0.25)

    def _fetch_klines_batch(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[str],
        limit: int,
    ) -> List[GatewayKlineModel]:
        """
        Fetch a single batch of klines from MetaAPI.

        Args:
            symbol: Trading symbol.
            timeframe: Kline interval.
            start_time: Start time in ISO 8601 format.
            limit: Maximum number of klines.

        Returns:
            List of GatewayKlineModel instances.
        """
        endpoint = (
            f"/users/current/accounts/{self._config.account_id}"
            f"/historical-market-data/symbols/{symbol}"
            f"/timeframes/{timeframe}/candles"
        )

        params: Dict[str, Any] = {"limit": limit}

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
        response: List[Dict[str, Any]],
        symbol: str,
        timeframe: str,
    ) -> List[GatewayKlineModel]:
        """
        Adapt MetaAPI response to GatewayKlineModel list.

        Args:
            response: List of candle objects from MetaAPI.
            symbol: Trading symbol.
            timeframe: Timeframe for calculating close_time.

        Returns:
            List of adapted GatewayKlineModel instances.
        """
        timeframe_seconds = TIMEFRAME_SECONDS.get(timeframe, 3600)
        klines: List[GatewayKlineModel] = []

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

    def _validate_params(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
    ) -> bool:
        """Validate get_klines parameters."""
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
