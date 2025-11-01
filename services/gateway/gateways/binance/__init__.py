from collections.abc import Callable
from time import sleep
from typing import Any, List, Optional

import requests

from interfaces.gateway import GatewayInterface
from models.candlestick import CandlestickModel
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
        callback: Callable[[List[CandlestickModel]], None],
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

            # Parse and response
            candlesticks = []

            for item in data:
                candlestick = CandlestickModel()
                candlestick.source = "binance"
                candlestick.symbol = symbol
                candlestick.kline_open_time = item[0]
                candlestick.open_price = float(item[1])
                candlestick.high_price = float(item[2])
                candlestick.low_price = float(item[3])
                candlestick.close_price = float(item[4])
                candlestick.volume = float(item[5])
                candlestick.kline_close_time = item[6]
                candlestick.quote_asset_volume = float(item[7])
                candlestick.number_of_trades = int(item[8])
                candlestick.taker_buy_base_asset_volume = float(item[9])
                candlestick.taker_buy_quote_asset_volume = float(item[10])
                candlesticks.append(candlestick)

            last_item = candlesticks[-1]
            from_date = int(last_item.kline_close_time.timestamp() * 1000)
            sleep(0.25)

            callback(candlesticks)
