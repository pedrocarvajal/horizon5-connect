from collections.abc import Callable
from time import sleep
from typing import Any, Dict, List, Optional

import requests

from interfaces.gateway import GatewayInterface
from services.logging import LoggingService


class Binance(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _fapi_url: str = "https://api.binance.com/api/v3"

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("dateway_binance")
        self._log.info(f"Initializing Binance gateway with kwargs: {kwargs}")

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        callback: Callable[[List[Dict[str, Any]]], None],
        **kwargs: Any,
    ) -> None:
        limit = kwargs.get("limit", 1000)
        from_date = int(from_date.timestamp()) * 1000
        to_date = int(to_date.timestamp()) * 1000

        while True:
            if from_date > to_date:
                callback([])
                break

            params = {
                "symbol": symbol.upper(),
                "interval": timeframe,
                "startTime": from_date,
                "endTime": to_date,
                "limit": limit,
            }

            try:
                response = requests.get(f"{self._fapi_url}/klines", params=params)
                data = response.json()
            except requests.exceptions.RequestException as e:
                self._log.error(f"Error fetching klines: {e}")
                raise e

            if not data:
                callback([])
                break

            candlesticks = []

            for item in data:
                open_time = int(float(item[0]) / 1000)
                close_time = int(float(item[6]) / 1000)

                candlesticks.append(
                    {
                        "source": "binance",
                        "symbol": symbol,
                        "open_time": open_time,
                        "open_price": float(item[1]),
                        "high_price": float(item[2]),
                        "low_price": float(item[3]),
                        "close_price": float(item[4]),
                        "volume": float(item[5]),
                        "close_time": close_time,
                        "quote_asset_volume": float(item[7]),
                        "number_of_trades": int(item[8]),
                        "taker_buy_base_asset_volume": float(item[9]),
                        "taker_buy_quote_asset_volume": float(item[10]),
                    }
                )

            last_item = candlesticks[-1]
            from_date = last_item["close_time"] * 1000
            sleep(0.25)

            callback(candlesticks)
