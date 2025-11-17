import hashlib
import hmac
import json
from collections.abc import Callable
from time import sleep, time
from typing import Any, Dict, List, Optional

import requests
import websockets

from enums.http_status import HttpStatus
from enums.order_side import OrderSide
from enums.order_type import OrderType
from interfaces.gateway import GatewayInterface
from services.gateway.gateways.binance.adapter import BinanceAdapter
from services.gateway.models.gateway_account import GatewayAccountModel
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class Binance(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _api_url: str
    _fapi_url: str
    _fapi_v2_url: str

    _api_ws_url: str
    _fapi_ws_url: str

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
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        self._log = LoggingService()
        self._log.setup("gateway_binance")
        self._log.info("Initializing Binance gateway")

        self._sandbox = kwargs.get("sandbox", False)
        self._api_key = kwargs.get("api_key")
        self._api_secret = kwargs.get("api_secret")

        self._api_url = "https://api.binance.com/api/v3"
        self._fapi_url = "https://fapi.binance.com/fapi/v1"
        self._fapi_v2_url = "https://fapi.binance.com/fapi/v2"
        self._api_ws_url = "wss://stream.binance.com:9443/ws"
        self._fapi_ws_url = "wss://fstream.binance.com/ws"

        self._are_credentials_set()

        self._adapter = BinanceAdapter(
            source_name="binance",
        )

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
        callback: Callable[[List[GatewayKlineModel]], None],
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

            klines = self._adapter.adapt_klines_batch(
                response=raw_data,
                symbol=symbol,
            )

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
    ) -> Optional[GatewaySymbolInfoModel]:
        raw_data = self._get_exchange_info(
            symbol=symbol,
            futures=futures,
        )

        if not raw_data:
            self._log.error(f"Failed to fetch symbol info for {symbol}")
            return None

        return self._adapter.adapt_symbol_info(response=raw_data)

    def get_trading_fees(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[GatewayTradingFeesModel]:
        raw_data = self._get_trading_fees(
            symbol=symbol,
            futures=futures,
        )

        if not raw_data:
            return None

        return self._adapter.adapt_trading_fees(
            response=raw_data,
            futures=futures,
        )

    def get_leverage_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        if not futures:
            self._log.warning("Leverage info only available for futures")
            return None

        raw_data = self._get_leverage_info(symbol=symbol)

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
                    tick = self._adapter.adapt_tick_from_stream(response=data)
                    await callback(tick)
                else:
                    self._log.error(f"Unsupported event: {data.get('e')}")
                    continue

    def open(
        self,
        futures: bool,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[GatewayOrderModel]:
        if not futures:
            self._log.warning("Spot trading not yet implemented for open()")
            return None

        order = self._open_order(
            symbol=symbol.upper(),
            side=side,
            order_type=order_type,
            volume=volume,
            price=price,
            client_order_id=client_order_id,
        )

        if not order:
            return None

        return self._adapter.adapt_order_response(
            response=order,
            symbol=symbol.upper(),
        )

    def set_leverage(
        self,
        futures: bool,
        symbol: str,
        leverage: int,
    ) -> bool:
        if not futures:
            self._log.warning("Leverage setting only available for futures")
            return False

        result = self._set_leverage(
            symbol=symbol.upper(),
            leverage=leverage,
        )

        if result:
            self._log.info(f"Leverage set to {leverage}x for {symbol.upper()}")
            return True

        return False

    def account(
        self,
        futures: bool,
        **kwargs: Any,
    ) -> Optional[GatewayAccountModel]:
        account_data = self._get_account(
            futures=futures,
        )

        if not account_data:
            return None

        return self._adapter.adapt_account_response(
            response=account_data,
            futures=futures,
        )

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
        self,
        symbol: str,
        futures: bool = False,
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
        self,
        symbol: str,
        futures: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if futures:
            base_url = self._fapi_url
            endpoint = "commissionRate"
        else:
            base_url = "https://api.binance.com/sapi/v1"
            endpoint = "asset/tradeFee"

        return self._execute(
            method="GET",
            url=f"{base_url}/{endpoint}",
            params={
                "symbol": symbol.upper(),
            },
        )

    def _get_leverage_info(
        self,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self._fapi_url}/leverageBracket"
        params = {"symbol": symbol.upper()}
        return self._execute(
            method="GET",
            url=url,
            params=params,
        )

    def _execute(
        self,
        method: str,
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
        signature = self._generate_signature(query_string=query_string)
        request_params["signature"] = signature
        headers = {"X-MBX-APIKEY": self._api_key}

        try:
            if method.upper() == "GET":
                response = requests.get(url, params=request_params, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, params=request_params, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, params=request_params, headers=headers)
            else:
                self._log.error(f"Unsupported HTTP method: {method}")
                return None

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error making authenticated {method} request: {e}")
            return None

    def _open_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self._fapi_url}/order"

        params = {
            "symbol": symbol,
            "side": side.value.upper(),
            "type": order_type.value.upper(),
            "quantity": volume,
        }

        if order_type == OrderType.LIMIT:
            if not price:
                self._log.error("Price is required for LIMIT orders")
                return None
            params["price"] = price
            params["timeInForce"] = "GTC"

        if client_order_id:
            params["newClientOrderId"] = client_order_id

        return self._execute(
            method="POST",
            url=url,
            params=params,
        )

    def _set_leverage(
        self,
        symbol: str,
        leverage: int,
    ) -> bool:
        url = f"{self._fapi_url}/leverage"
        params = {
            "symbol": symbol,
            "leverage": leverage,
        }

        result = self._execute(
            method="POST",
            url=url,
            params=params,
        )

        if not result:
            return False

        if isinstance(result, dict) and "code" in result:
            error_msg = result.get("msg", "Unknown error")
            self._log.error(f"Failed to set leverage: {error_msg} (code: {result['code']})")
            return False

        return True

    def _get_account(
        self,
        futures: bool,
    ) -> Optional[Dict[str, Any]]:
        url = f"{self._fapi_v2_url}/account" if futures else f"{self._api_url}/account"

        result = self._execute(
            method="GET",
            url=url,
            params=None,
        )

        if not result:
            return None

        if isinstance(result, dict) and "code" in result:
            error_msg = result.get("msg", "Unknown error")
            error_code = result["code"]
            self._log.error(f"Failed to get account info: {error_msg} (code: {error_code})")
            return None

        return result

    def _generate_signature(
        self,
        query_string: str,
    ) -> str:
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _are_credentials_set(
        self,
    ) -> bool:
        if not self._api_key or not self._api_secret:
            self._log.warning("API key or API secret is not set")
            return False

        self._log.info("API key and API secret are set")

        masked_api_key = self._get_masked_value(value=self._api_key)
        masked_api_secret = self._get_masked_value(value=self._api_secret)

        self._log.info(f"Using API key: {masked_api_key}")
        self._log.info(f"Using API secret: {masked_api_secret}")
        return True

    # Helpers
    def _get_masked_value(
        self,
        value: str,
    ) -> str:
        characters_to_mask = 4

        return "*****" + str(value)[-characters_to_mask:] if value and len(value) > characters_to_mask else "*****"
