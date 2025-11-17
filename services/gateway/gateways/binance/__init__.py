import hashlib
import hmac
import json
from collections.abc import Callable
from time import sleep, time
from typing import Any, Dict, List, Optional

import requests
import websockets

from enums.http_status import HttpStatus
from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance.adapter import BinanceAdapter
from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel
from services.logging import LoggingService


class Binance(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _api_url: str = "https://api.binance.com/api/v3"
    _fapi_url: str = "https://fapi.binance.com/fapi/v1"

    _api_ws_url: str = "wss://stream.binance.com:9443/ws"
    _fapi_ws_url: str = "wss://fstream.binance.com/ws"

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _api_key: str
    _api_secret: str
    _sandbox: bool
    _adapter: BinanceAdapter

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        self._log = LoggingService()
        self._log.setup("gateway_binance")
        self._log.info("Initializing Binance gateway")

        self._sandbox = kwargs.get("sandbox", False)
        self._api_key = kwargs.get("api_key")
        self._api_secret = kwargs.get("api_secret")

        self._are_credentials_set()

        self._adapter = BinanceAdapter(source_name="binance", sandbox=self._sandbox)

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
        *,
        callback: Callable[[List[KlineModel]], None],
        **kwargs: Any,
    ) -> None:
        limit = kwargs.get("limit", 1000)
        from_date_ms = int(from_date * 1000)
        to_date_ms = int(to_date * 1000)

        while True:
            if from_date_ms > to_date_ms:
                callback([])
                break

            raw_data = self._get_klines(
                symbol=symbol,
                interval=timeframe,
                start_time=from_date_ms,
                end_time=to_date_ms,
                limit=limit,
                futures=futures,
            )

            if not self._adapter.validate_response(raw_data):
                callback([])
                break

            klines = self._adapter.adapt_klines_batch(raw_data, symbol)

            if not klines:
                callback([])
                break

            last_kline = klines[-1]
            from_date_ms = int(last_kline.close_time * 1000)
            sleep(0.25)

            callback(klines)

    def get_symbol_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[SymbolInfoModel]:
        raw_data = self._get_exchange_info(symbol, futures)

        if not raw_data:
            self._log.error(f"Failed to fetch symbol info for {symbol}")
            return None

        return self._adapter.adapt_symbol_info(raw_data)

    def get_trading_fees(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[TradingFeesModel]:
        if self._sandbox:
            return self._adapter.adapt_trading_fees_sandbox(symbol)

        raw_data = self._get_trading_fees(symbol, futures)

        if not raw_data:
            return None

        return self._adapter.adapt_trading_fees(raw_data, futures)

    def get_leverage_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        if not futures:
            self._log.warning("Leverage info only available for futures")
            return None

        raw_data = self._get_leverage_info(symbol)

        if not raw_data:
            return None

        if isinstance(raw_data, list) and len(raw_data) > 0:
            return raw_data[0]

        return raw_data

    async def stream(
        self,
        futures: bool,
        streams: List[str],
        callback: Callable[[Any], None],
    ) -> None:
        base_url = self._fapi_ws_url if futures else self._api_ws_url
        stream_path = "/".join(streams)
        url = f"{base_url}/{stream_path}"

        self._log.info(f"Connecting to WebSocket: {url}")

        for stream in streams:
            if not any(stream.endswith(suffix) for suffix in ["bookTicker"]):
                self._log.error(f"Unsupported stream: {stream}")
                return

        async with websockets.connect(url) as websocket:
            self._log.info(f"Connected to stream: {stream_path}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                except Exception as e:
                    self._log.error(f"Error processing message: {e}")
                    continue

                if data and data.get("e") == "bookTicker":
                    tick = self._adapter.adapt_tick_from_stream(data)
                    await callback(tick)
                else:
                    self._log.error(f"Unsupported event: {data.get('e')}")
                    continue

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        limit: int = 1000,
        futures: bool = False,
    ) -> Optional[List[Any]]:
        base_url = self._fapi_url if futures else self._api_url

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        try:
            response = requests.get(f"{base_url}/klines", params=params)

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching klines: {e}")
            return None

    def _get_exchange_info(
        self, symbol: str, futures: bool = False
    ) -> Optional[Dict[str, Any]]:
        base_url = self._fapi_url if futures else self._api_url
        params = {"symbol": symbol.upper()}

        try:
            response = requests.get(f"{base_url}/exchangeInfo", params=params)

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching exchange info: {e}")
            return None

    def _get_trading_fees(
        self, symbol: str, futures: bool = False
    ) -> Optional[Dict[str, Any]]:
        if futures:
            base_url = self._fapi_url
            endpoint = "commissionRate"
        else:
            base_url = "https://api.binance.com/sapi/v1"
            endpoint = "asset/tradeFee"

        params = {"symbol": symbol.upper()}
        return self._authenticated_request(f"{base_url}/{endpoint}", params)

    def _get_leverage_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        url = f"{self._fapi_url}/leverageBracket"
        params = {"symbol": symbol.upper()}
        return self._authenticated_request(url, params)

    def _authenticated_request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self._api_key or not self._api_secret:
            self._log.error("API credentials required for authenticated request")
            return None

        request_params = params.copy() if params else {}
        timestamp = int(time() * 1000)
        request_params["timestamp"] = timestamp

        query_string = "&".join(f"{k}={v}" for k, v in request_params.items())
        signature = self._generate_signature(query_string)
        request_params["signature"] = signature

        headers = {"X-MBX-APIKEY": self._api_key}

        try:
            response = requests.get(url, params=request_params, headers=headers)

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error making authenticated request: {e}")
            return None

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

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

    # Helpers
    def _get_masked_value(self, value: str) -> str:
        characters_to_mask = 4

        return (
            "*****" + str(value)[-characters_to_mask:]
            if value and len(value) > characters_to_mask
            else "*****"
        )
