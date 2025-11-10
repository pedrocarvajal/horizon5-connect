import hashlib
import hmac
from collections.abc import Callable
from time import sleep, time
from typing import Any, Dict, List, Optional

import requests

from enums.http_status import HttpStatus
from interfaces.gateway import GatewayInterface
from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel
from services.logging import LoggingService


class Binance(GatewayInterface):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
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
        callback: Callable[[List[KlineModel]], None],
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

                if response.status_code != HttpStatus.OK.value:
                    self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                    callback([])
                    break

                data = response.json()
            except requests.exceptions.RequestException as e:
                self._log.error(f"Error fetching klines: {e}")
                raise e

            if not self._validate_api_response(data):
                callback([])
                break

            klines = []

            for item in data:
                open_time = int(float(item[0]) / 1000)
                close_time = int(float(item[6]) / 1000)

                kline = KlineModel(
                    source="binance",
                    symbol=symbol,
                    open_time=open_time,
                    open_price=float(item[1]),
                    high_price=float(item[2]),
                    low_price=float(item[3]),
                    close_price=float(item[4]),
                    volume=float(item[5]),
                    close_time=close_time,
                    quote_asset_volume=float(item[7]),
                    number_of_trades=int(item[8]),
                    taker_buy_base_asset_volume=float(item[9]),
                    taker_buy_quote_asset_volume=float(item[10]),
                    response=item,
                )

                klines.append(kline)

            last_kline = klines[-1]
            from_date = int(last_kline.close_time * 1000)
            sleep(0.25)

            callback(klines)

    def get_symbol_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[SymbolInfoModel]:
        base_url = self._fapi_url if futures else self._api_url
        endpoint = "exchangeInfo"
        url = f"{base_url}/{endpoint}"
        params = {
            "symbol": symbol.upper(),
        }

        try:
            response = requests.get(
                url,
                params=params,
            )

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            data = response.json()

            if "symbols" in data and len(data["symbols"]) > 0:
                symbol_info = data["symbols"][0]
                filters = self._parse_binance_filters(symbol_info.get("filters", []))

                return SymbolInfoModel(
                    symbol=symbol_info.get("symbol", ""),
                    base_asset=symbol_info.get("baseAsset", ""),
                    quote_asset=symbol_info.get("quoteAsset", ""),
                    price_precision=symbol_info.get("pricePrecision", 2),
                    quantity_precision=symbol_info.get("quantityPrecision", 2),
                    min_price=filters.get("min_price"),
                    max_price=filters.get("max_price"),
                    tick_size=filters.get("tick_size"),
                    min_quantity=filters.get("min_quantity"),
                    max_quantity=filters.get("max_quantity"),
                    step_size=filters.get("step_size"),
                    min_notional=filters.get("min_notional"),
                    status=symbol_info.get("status", "TRADING"),
                    margin_percent=self._parse_margin_percent(symbol_info),
                    response=symbol_info,
                )

            return None

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error fetching symbol info: {e}")
            return None

    def get_trading_fees(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[TradingFeesModel]:
        if futures:
            base_url = self._fapi_url
            endpoint = "commissionRate"
            params = {"symbol": symbol.upper()}
        else:
            base_url = "https://api.binance.com/sapi/v1"
            endpoint = "asset/tradeFee"
            params = {"symbol": symbol.upper()}

        url = f"{base_url}/{endpoint}"
        data = self._request(url, params=params, requires_auth=True)

        if not data:
            return None

        fees_data = self._get_first(data)

        if not fees_data:
            return None

        symbol_name = fees_data.get("symbol", symbol.upper())

        if futures:
            maker_commission = fees_data.get("makerCommissionRate")
            taker_commission = fees_data.get("takerCommissionRate")
        else:
            maker_commission = fees_data.get("makerCommission")
            taker_commission = fees_data.get("takerCommission")

        return TradingFeesModel(
            symbol=symbol_name,
            maker_commission=maker_commission,
            taker_commission=taker_commission,
            response=fees_data,
        )

    def get_leverage_info(
        self,
        futures: bool,
        symbol: str,
    ) -> Optional[Dict[str, Any]]:
        if not futures:
            self._log.warning("Leverage info only available for futures")
            return None

        url = f"{self._fapi_url}/leverageBracket"
        params = {"symbol": symbol.upper()}
        data = self._request(url, params=params, requires_auth=True)

        if not data:
            return None

        return self._get_first(data)

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
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

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        requires_auth: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if requires_auth and (not self._api_key or not self._api_secret):
            self._log.error("API credentials required for authenticated request")
            return None

        headers = {}
        request_params = params.copy() if params else {}

        if requires_auth:
            timestamp = int(time() * 1000)
            request_params["timestamp"] = timestamp
            query_string = "&".join(f"{k}={v}" for k, v in request_params.items())
            signature = self._generate_signature(query_string)
            request_params["signature"] = signature
            headers["X-MBX-APIKEY"] = self._api_key

        try:
            response = requests.get(url, params=request_params, headers=headers)

            if response.status_code != HttpStatus.OK.value:
                self._log.error(f"HTTP Error {response.status_code}: {response.text}")
                return None

            return response.json()

        except requests.exceptions.RequestException as e:
            self._log.error(f"Error making request to {url}: {e}")
            return None

    def _validate_api_response(self, data: Any) -> bool:
        if not data:
            return False

        if isinstance(data, dict) and "code" in data:
            error_msg = data.get("msg", "Unknown error")
            self._log.error(f"API Error: {error_msg} (code: {data['code']})")
            return False

        if not isinstance(data, list):
            self._log.error(f"Unexpected response type: {type(data)}")
            return False

        return True

    def _get_first(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, list) and len(data) > 0:
            return data[0]

        return data

    def _parse_binance_filters(
        self, filters: List[Dict[str, Any]]
    ) -> Dict[str, Optional[float]]:
        result = {
            "min_price": None,
            "max_price": None,
            "tick_size": None,
            "min_quantity": None,
            "max_quantity": None,
            "step_size": None,
            "min_notional": None,
        }

        for filter_item in filters:
            filter_type = filter_item.get("filterType", "")

            if filter_type == "PRICE_FILTER":
                result["min_price"] = self._safe_float(filter_item.get("minPrice"))
                result["max_price"] = self._safe_float(filter_item.get("maxPrice"))
                result["tick_size"] = self._safe_float(filter_item.get("tickSize"))

            elif filter_type == "LOT_SIZE":
                result["min_quantity"] = self._safe_float(filter_item.get("minQty"))
                result["max_quantity"] = self._safe_float(filter_item.get("maxQty"))
                result["step_size"] = self._safe_float(filter_item.get("stepSize"))

            elif filter_type == "MIN_NOTIONAL":
                result["min_notional"] = self._safe_float(filter_item.get("notional"))

        return result

    def _parse_margin_percent(self, symbol_info: Dict[str, Any]) -> Optional[float]:
        if "requiredMarginPercent" in symbol_info:
            return self._safe_float(symbol_info.get("requiredMarginPercent"))

        if "maintMarginPercent" in symbol_info:
            return self._safe_float(symbol_info.get("maintMarginPercent"))

        return None

    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            return float(value) if value is not None else None

        except (ValueError, TypeError):
            return None
