import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from configs.timezone import TIMEZONE
from models.tick import TickModel
from services.gateway.adapter import BaseGatewayAdapter
from services.gateway.models.kline import KlineModel
from services.gateway.models.symbol_info import SymbolInfoModel
from services.gateway.models.trading_fees import TradingFeesModel
from services.logging import LoggingService


class BinanceAdapter(BaseGatewayAdapter):
    _source: str
    _cached_fees: Optional[Dict[str, Any]] = None

    def __init__(self, source_name: str = "binance", sandbox: bool = False) -> None:
        self._log = LoggingService()
        self._log.setup("binance_adapter")

        self._source = source_name
        self._sandbox = sandbox

        self._load_fees_config()

    def adapt_kline(self, raw_data: Any, symbol: str) -> KlineModel:
        return KlineModel(
            source=self._source,
            symbol=symbol,
            open_time=int(float(raw_data[0]) / 1000),
            open_price=float(raw_data[1]),
            high_price=float(raw_data[2]),
            low_price=float(raw_data[3]),
            close_price=float(raw_data[4]),
            volume=float(raw_data[5]),
            close_time=int(float(raw_data[6]) / 1000),
            quote_asset_volume=float(raw_data[7]),
            number_of_trades=int(raw_data[8]),
            taker_buy_base_asset_volume=float(raw_data[9]),
            taker_buy_quote_asset_volume=float(raw_data[10]),
            response=raw_data,
        )

    def adapt_klines_batch(self, raw_data: List[Any], symbol: str) -> List[KlineModel]:
        return [self.adapt_kline(item, symbol) for item in raw_data]

    def adapt_symbol_info(self, raw_data: Dict[str, Any]) -> Optional[SymbolInfoModel]:
        if not raw_data or "symbols" not in raw_data or len(raw_data["symbols"]) == 0:
            return None

        symbol_info = raw_data["symbols"][0]
        filters = self._parse_filters(symbol_info.get("filters", []))

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

    def adapt_trading_fees(
        self, raw_data: Dict[str, Any], futures: bool
    ) -> Optional[TradingFeesModel]:
        if not raw_data:
            return None

        fees_data = self._get_first(raw_data)

        if not fees_data:
            return None

        symbol_name = fees_data.get("symbol", "")

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

    def adapt_trading_fees_sandbox(self, symbol: str) -> TradingFeesModel:
        if self._cached_fees:
            symbol_fees = self._cached_fees.get(symbol.upper(), {})
            maker_commission = symbol_fees.get("maker_commission", 0.0002)
            taker_commission = symbol_fees.get("taker_commission", 0.0005)
        else:
            maker_commission = 0.0
            taker_commission = 0.0

        return TradingFeesModel(
            symbol=symbol,
            maker_commission=maker_commission,
            taker_commission=taker_commission,
            response=None,
        )

    def adapt_tick_from_stream(self, raw_data: Dict[str, Any]) -> TickModel:
        best_bid = self._safe_float(raw_data.get("b", 0.0))
        best_ask = self._safe_float(raw_data.get("a", 0.0))

        price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0

        return TickModel(
            sandbox=False,
            price=price,
            bid_price=best_bid,
            ask_price=best_ask,
            date=datetime.datetime.now(tz=TIMEZONE),
        )

    def validate_response(self, raw_data: Any) -> bool:
        if not raw_data:
            return False

        if isinstance(raw_data, dict) and "code" in raw_data:
            error_msg = raw_data.get("msg", "Unknown error")
            self._log.error(f"API Error: {error_msg} (code: {raw_data['code']})")
            return False

        if not isinstance(raw_data, list):
            self._log.error(f"Unexpected response type: {type(raw_data)}")
            return False

        return True

    def _parse_filters(self, filters: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
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

    def _get_first(self, data: Any) -> Dict[str, Any]:
        if isinstance(data, list) and len(data) > 0:
            return data[0]

        return data

    def _load_fees_config(self) -> None:
        fees_file_path = Path(__file__).parent / "configs" / "fees.json"

        if fees_file_path.exists():
            try:
                with fees_file_path.open("r") as f:
                    self._cached_fees = json.load(f)
                    self._log.info(f"Loaded trading fees from {fees_file_path}")
                    return

            except json.JSONDecodeError as e:
                self._log.error(f"Error decoding JSON from {fees_file_path}: {e}")
                self._cached_fees = {}
                return

            except Exception as e:
                self._log.error(f"Error reading or parsing {fees_file_path}: {e}")
                self._cached_fees = {}
                return

        self._log.warning(f"Trading fees configuration file not found at {fees_file_path}")
        self._cached_fees = {}
