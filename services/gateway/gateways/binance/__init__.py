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
    _api_key: str
    _api_secret: str

    _api_url: str = "https://api.binance.com/api/v3"
    _fapi_url: str = "https://fapi.binance.com/fapi/v1"

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("dateway_binance")
        self._log.info("Initializing Binance gateway")

        self._api_key = kwargs.get("api_key")
        self._api_secret = kwargs.get("api_secret")

        self._are_credentials_set()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def get_klines(
        self,
        futures: bool,
        symbol: str,
        timeframe: str,
        from_date: Optional[int],
        to_date: Optional[int],
        callback: Callable[[List[Dict[str, Any]]], None],
        **kwargs: Any,
    ) -> None:
        limit = kwargs.get("limit", 1000)
        from_date = int(from_date * 1000)
        to_date = int(to_date * 1000)

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
                base_url = self._fapi_url if futures else self._api_url
                response = requests.get(f"{base_url}/klines", params=params)

                if response.status_code != 200:
                    self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                    callback([])
                    break

                data = response.json()
            except requests.exceptions.RequestException as e:
                self._log.error(f"Error fetching klines: {e}")
                raise e

            if not data:
                callback([])
                break

            if isinstance(data, dict) and "code" in data:
                error_msg = data.get("msg", "Unknown error")
                self._log.error(f"API Error: {error_msg} (code: {data['code']})")
                callback([])
                break

            if not isinstance(data, list):
                self._log.error(f"Unexpected response type: {type(data)}")
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
            from_date = int(last_item["close_time"] * 1000)
            sleep(0.25)

            callback(candlesticks)

    def get_symbol_settings(self, futures: bool, symbol: str) -> Dict[str, Any]:
        return

    def _are_credentials_set(self) -> bool:
        if not self._api_key or not self._api_secret:
            self._log.warning("API key or API secret is not set")
            return False

        self._log.info("API key and API secret are set")

        masked_api_key = self._get_masked_value(self._api_key)
        masked_api_secret = self._get_masked_value(self._api_secret)

        self._log.info(f"Using API key: {masked_api_key}")
        self._log.info(f"Using API secret: {masked_api_secret}")
        return True

    def _get_masked_value(self, value: str) -> str:
        characters_to_mask = 4

        return (
            "*****" + str(value)[-characters_to_mask:]
            if value and len(value) > characters_to_mask
            else "*****"
        )
