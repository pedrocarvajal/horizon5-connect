from collections.abc import Callable
from datetime import datetime
from time import sleep
from typing import Any, List, Optional

import requests

from configs.timezone import TIMEZONE
from enums.http_status import HttpStatus
from services.gateway.gateways.binance.components.base import BaseComponent
from services.gateway.helpers import has_api_error, parse_timestamp_ms
from services.gateway.models.gateway_kline import GatewayKlineModel


class KlineComponent(BaseComponent):
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
        if not symbol:
            self._log.error("symbol is required")
            callback([])
            return

        if not isinstance(symbol, str):
            self._log.error("symbol must be a string")
            callback([])
            return

        if not timeframe:
            self._log.error("timeframe is required")
            callback([])
            return

        if not isinstance(timeframe, str):
            self._log.error("timeframe must be a string")
            callback([])
            return

        if from_date is None:
            self._log.error("from_date is required")
            callback([])
            return

        if to_date is None:
            self._log.error("to_date is required")
            callback([])
            return

        from_date_dt = datetime.fromtimestamp(from_date, tz=TIMEZONE)
        to_date_dt = datetime.fromtimestamp(to_date, tz=TIMEZONE)
        from_date_ms = parse_timestamp_ms(from_date_dt)
        to_date_ms = parse_timestamp_ms(to_date_dt)

        while True:
            if from_date_ms > to_date_ms:
                callback([])
                break

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

                if response.status_code != HttpStatus.OK.value:
                    self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                    callback([])
                    break

                response = response.json()

            except requests.exceptions.RequestException as e:
                self._log.error(f"Error fetching klines: {e}")
                callback([])
                break

            if not response:
                callback([])
                break

            has_error, error_msg, error_code = has_api_error(
                response=response,
            )

            if has_error:
                self._log.error(f"API Error: {error_msg} (code: {error_code})")
                callback([])
                break

            if not isinstance(response, list):
                self._log.error(f"Unexpected response type: {type(response)}")
                callback([])
                break

            klines = self._adapt_klines_batch(
                response=response,
                symbol=symbol,
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
    def _adapt_klines_batch(
        self,
        response: List[Any],
        symbol: str,
    ) -> List[GatewayKlineModel]:
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
