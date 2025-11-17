import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from configs.timezone import TIMEZONE
from enums.order_side import OrderSide
from enums.order_status import OrderStatus
from enums.order_type import OrderType
from models.tick import TickModel
from services.gateway.adapter import BaseGatewayAdapter
from services.gateway.helpers import has_api_error, parse_optional_float
from services.gateway.models.gateway_account import (
    GatewayAccountBalanceModel,
    GatewayAccountModel,
)
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_order import GatewayOrderModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel
from services.logging import LoggingService


class BinanceAdapter(BaseGatewayAdapter):
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _source: str
    _cached_fees: Optional[Dict[str, Any]] = None
    _log: LoggingService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        source_name: str = "binance",
    ) -> None:
        self._log = LoggingService()
        self._log.setup("binance_adapter")

        self._source = source_name

        self._load_fees_config()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def adapt_klines_batch(
        self,
        response: List[Any],
        symbol: str,
    ) -> List[GatewayKlineModel]:
        return [
            GatewayKlineModel(
                source=self._source,
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

    def adapt_symbol_info(
        self,
        response: Dict[str, Any],
    ) -> Optional[GatewaySymbolInfoModel]:
        if not response or "symbols" not in response or len(response["symbols"]) == 0:
            return None

        symbol_info = response["symbols"][0]
        filters = self._parse_filters(filters=symbol_info.get("filters", []))

        return GatewaySymbolInfoModel(
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
            margin_percent=self._parse_margin_percent(symbol_info=symbol_info),
            response=symbol_info,
        )

    def adapt_trading_fees(
        self,
        response: Dict[str, Any],
        futures: bool,
    ) -> Optional[GatewayTradingFeesModel]:
        if not response:
            return None

        fees_data = self._get_first(data=response)

        if not fees_data:
            return None

        symbol_name = fees_data.get("symbol", "")

        if futures:
            maker_commission = fees_data.get("makerCommissionRate")
            taker_commission = fees_data.get("takerCommissionRate")
        else:
            maker_commission = fees_data.get("makerCommission")
            taker_commission = fees_data.get("takerCommission")

        return GatewayTradingFeesModel(
            symbol=symbol_name,
            maker_commission=maker_commission,
            taker_commission=taker_commission,
            response=fees_data,
        )

    def adapt_tick_from_stream(
        self,
        response: Dict[str, Any],
    ) -> TickModel:
        best_bid = parse_optional_float(value=response.get("b", 0.0))
        best_ask = parse_optional_float(value=response.get("a", 0.0))

        price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0

        return TickModel(
            sandbox=False,
            price=price,
            bid_price=best_bid,
            ask_price=best_ask,
            date=datetime.datetime.now(tz=TIMEZONE),
        )

    def validate_response(
        self,
        response: Any,
    ) -> bool:
        if not response:
            return False

        has_error, error_msg, error_code = has_api_error(response=response)
        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return False

        if not isinstance(response, list):
            self._log.error(f"Unexpected response type: {type(response)}")
            return False

        return True

    def adapt_order_response(
        self,
        response: Dict[str, Any],
        symbol: str,
    ) -> Optional[GatewayOrderModel]:
        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)
        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return None

        order_id = str(response.get("orderId", ""))
        side_str = response.get("side", "").upper()
        type_str = response.get("type", "").upper()
        status_str = response.get("status", "").upper()
        side = OrderSide.BUY if side_str == "BUY" else OrderSide.SELL
        order_type = self._map_order_type(type_str=type_str)
        status = self.adapt_order_status(status_str=status_str)
        price = parse_optional_float(value=response.get("price", 0))
        executed_qty = parse_optional_float(value=response.get("executedQty", 0))
        orig_qty = parse_optional_float(value=response.get("origQty", 0))

        return GatewayOrderModel(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            volume=orig_qty or 0.0,
            executed_volume=executed_qty or 0.0,
            price=price or 0.0,
            response=response,
        )

    def adapt_order_status(
        self,
        status_str: str,
    ) -> OrderStatus:
        status_map = {
            "NEW": OrderStatus.OPENING,
            "PARTIALLY_FILLED": OrderStatus.OPENING,
            "FILLED": OrderStatus.OPENED,
            "CANCELED": OrderStatus.CANCELLED,
            "PENDING_CANCEL": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.CANCELLED,
            "EXPIRED": OrderStatus.CANCELLED,
        }

        return status_map.get(status_str.upper(), OrderStatus.OPENING)

    def adapt_account_response(
        self,
        response: Dict[str, Any],
        futures: bool,
    ) -> Optional[GatewayAccountModel]:
        balances: List[GatewayAccountBalanceModel] = []

        if not response:
            return None

        has_error, error_msg, error_code = has_api_error(response=response)
        if has_error:
            self._log.error(f"API Error: {error_msg} (code: {error_code})")
            return None

        if futures:
            assets = response.get("assets", [])

            for asset_data in assets:
                wallet_balance = parse_optional_float(value=asset_data.get("walletBalance", 0))
                locked_balance = parse_optional_float(value=asset_data.get("locked", 0))

                balances.append(
                    GatewayAccountBalanceModel(
                        asset=asset_data.get("asset", ""),
                        balance=wallet_balance,
                        locked=locked_balance,
                        response=asset_data,
                    )
                )

            total_wallet_balance = parse_optional_float(value=response.get("totalWalletBalance", 0))
            total_margin_balance = parse_optional_float(value=response.get("totalMarginBalance", 0))
            total_unrealized_pnl = parse_optional_float(value=response.get("totalUnrealizedProfit", 0))
            total_position_initial_margin = parse_optional_float(value=response.get("totalPositionInitialMargin", 0))
            total_open_order_initial_margin = parse_optional_float(value=response.get("totalOpenOrderInitialMargin", 0))

            return GatewayAccountModel(
                balances=balances,
                balance=total_wallet_balance,
                nav=total_margin_balance,
                locked=total_open_order_initial_margin,
                margin=total_position_initial_margin,
                exposure=total_position_initial_margin,
                pnl=total_unrealized_pnl,
                response=response,
            )

        spot_balances = response.get("balances", [])
        total_balance = 0.0
        total_locked = 0.0

        for balance_data in spot_balances:
            free = parse_optional_float(value=balance_data.get("free", 0))
            locked = parse_optional_float(value=balance_data.get("locked", 0))
            total_balance += free + locked
            total_locked += locked

            balances.append(
                GatewayAccountBalanceModel(
                    asset=balance_data.get("asset", ""),
                    balance=free + locked,
                    locked=locked,
                    response=balance_data,
                )
            )

        return GatewayAccountModel(
            balances=balances,
            balance=total_balance,
            nav=total_balance,
            locked=total_locked,
            margin=0.0,
            exposure=0.0,
            pnl=0.0,
            response=response,
        )

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _map_order_type(
        self,
        type_str: str,
    ) -> OrderType:
        type_map = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
            "STOP": OrderType.STOP_LOSS,
            "STOP_MARKET": OrderType.STOP_LOSS,
            "TAKE_PROFIT": OrderType.TAKE_PROFIT,
            "TAKE_PROFIT_MARKET": OrderType.TAKE_PROFIT,
        }

        return type_map.get(type_str.upper(), OrderType.MARKET)

    def _parse_filters(
        self,
        filters: List[Dict[str, Any]],
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
                result["min_price"] = parse_optional_float(value=filter_item.get("minPrice"))
                result["max_price"] = parse_optional_float(value=filter_item.get("maxPrice"))
                result["tick_size"] = parse_optional_float(value=filter_item.get("tickSize"))

            elif filter_type == "LOT_SIZE":
                result["min_quantity"] = parse_optional_float(value=filter_item.get("minQty"))
                result["max_quantity"] = parse_optional_float(value=filter_item.get("maxQty"))
                result["step_size"] = parse_optional_float(value=filter_item.get("stepSize"))

            elif filter_type == "MIN_NOTIONAL":
                result["min_notional"] = parse_optional_float(value=filter_item.get("notional"))

        return result

    def _parse_margin_percent(
        self,
        symbol_info: Dict[str, Any],
    ) -> Optional[float]:
        if "requiredMarginPercent" in symbol_info:
            return parse_optional_float(value=symbol_info.get("requiredMarginPercent"))

        if "maintMarginPercent" in symbol_info:
            return parse_optional_float(value=symbol_info.get("maintMarginPercent"))

        return None

    def _load_fees_config(
        self,
    ) -> None:
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

    # Helpers
    def _get_first(
        self,
        data: Any,
    ) -> Dict[str, Any]:
        if isinstance(data, list) and len(data) > 0:
            return data[0]

        return data


# coding review: 2025-11-17T12:52:12Z
