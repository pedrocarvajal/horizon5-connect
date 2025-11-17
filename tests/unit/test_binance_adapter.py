import datetime
import unittest
from typing import Any, Dict, List
from unittest.mock import patch

from models.tick import TickModel
from services.gateway.gateways.binance.adapter import BinanceAdapter
from services.gateway.helpers import parse_optional_float
from services.gateway.models.gateway_kline import GatewayKlineModel
from services.gateway.models.gateway_symbol_info import GatewaySymbolInfoModel
from services.gateway.models.gateway_trading_fees import GatewayTradingFeesModel


class TestBinanceAdapter(unittest.TestCase):
    def setUp(self) -> None:
        with patch.object(BinanceAdapter, "_load_fees_config"):
            self.adapter = BinanceAdapter(source_name="binance")

    def test_adapt_klines_batch_single_item(self) -> None:
        raw_kline = [
            1704067200000,
            "42350.50",
            "42500.00",
            "42300.00",
            "42450.75",
            "150.5",
            1704153600000,
            "6380000.00",
            1500,
            "75.2",
            "3190000.00",
        ]

        result = self.adapter.adapt_klines_batch([raw_kline], "BTCUSDT")

        assert len(result) == 1
        assert isinstance(result[0], GatewayKlineModel)
        assert result[0].source == "binance"
        assert result[0].symbol == "BTCUSDT"
        assert result[0].open_time == 1704067200
        assert result[0].open_price == 42350.50
        assert result[0].high_price == 42500.00
        assert result[0].low_price == 42300.00
        assert result[0].close_price == 42450.75
        assert result[0].volume == 150.5
        assert result[0].close_time == 1704153600
        assert result[0].quote_asset_volume == 6380000.00
        assert result[0].number_of_trades == 1500
        assert result[0].taker_buy_base_asset_volume == 75.2
        assert result[0].taker_buy_quote_asset_volume == 3190000.00
        assert result[0].response == raw_kline

    def test_adapt_klines_batch_multiple_items(self) -> None:
        raw_klines = [
            [
                1704067200000,
                "42350.50",
                "42500.00",
                "42300.00",
                "42450.75",
                "150.5",
                1704153600000,
                "6380000.00",
                1500,
                "75.2",
                "3190000.00",
            ],
            [
                1704153600000,
                "42450.75",
                "42600.00",
                "42400.00",
                "42550.25",
                "200.3",
                1704240000000,
                "8500000.00",
                2000,
                "100.1",
                "4250000.00",
            ],
        ]

        result = self.adapter.adapt_klines_batch(raw_klines, "BTCUSDT")

        assert len(result) == 2
        assert all(isinstance(k, GatewayKlineModel) for k in result)
        assert result[0].open_price == 42350.50
        assert result[1].open_price == 42450.75

    def test_adapt_symbol_info_valid(self) -> None:
        raw_response: Dict[str, Any] = {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "pricePrecision": 2,
                    "quantityPrecision": 3,
                    "status": "TRADING",
                    "filters": [
                        {
                            "filterType": "PRICE_FILTER",
                            "minPrice": "0.01",
                            "maxPrice": "1000000.00",
                            "tickSize": "0.01",
                        },
                        {
                            "filterType": "LOT_SIZE",
                            "minQty": "0.001",
                            "maxQty": "1000.00",
                            "stepSize": "0.001",
                        },
                        {
                            "filterType": "MIN_NOTIONAL",
                            "notional": "10.00",
                        },
                    ],
                }
            ]
        }

        result = self.adapter.adapt_symbol_info(raw_response)

        assert isinstance(result, GatewaySymbolInfoModel)
        assert result.symbol == "BTCUSDT"
        assert result.base_asset == "BTC"
        assert result.quote_asset == "USDT"
        assert result.price_precision == 2
        assert result.quantity_precision == 3
        assert result.status == "TRADING"
        assert result.min_price == 0.01
        assert result.max_price == 1000000.00
        assert result.tick_size == 0.01
        assert result.min_quantity == 0.001
        assert result.max_quantity == 1000.00
        assert result.step_size == 0.001
        assert result.min_notional == 10.00

    def test_adapt_symbol_info_empty_response(self) -> None:
        result = self.adapter.adapt_symbol_info({})
        assert result is None

    def test_adapt_symbol_info_no_symbols(self) -> None:
        result = self.adapter.adapt_symbol_info({"symbols": []})
        assert result is None

    def test_adapt_symbol_info_with_margin_percent(self) -> None:
        raw_response: Dict[str, Any] = {
            "symbols": [
                {
                    "symbol": "BTCUSDT",
                    "baseAsset": "BTC",
                    "quoteAsset": "USDT",
                    "requiredMarginPercent": "5.0",
                    "filters": [],
                }
            ]
        }

        result = self.adapter.adapt_symbol_info(raw_response)

        assert isinstance(result, GatewaySymbolInfoModel)
        assert result.margin_percent == 0.05

    def test_adapt_trading_fees_spot(self) -> None:
        raw_response: Dict[str, Any] = {
            "symbol": "BTCUSDT",
            "makerCommission": "0.001",
            "takerCommission": "0.001",
        }

        result = self.adapter.adapt_trading_fees(raw_response, futures=False)

        assert isinstance(result, GatewayTradingFeesModel)
        assert result.symbol == "BTCUSDT"
        assert result.maker_commission == 0.001
        assert result.taker_commission == 0.001

    def test_adapt_trading_fees_futures(self) -> None:
        raw_response: Dict[str, Any] = {
            "symbol": "BTCUSDT",
            "makerCommissionRate": "0.0002",
            "takerCommissionRate": "0.0004",
        }

        result = self.adapter.adapt_trading_fees(raw_response, futures=True)

        assert isinstance(result, GatewayTradingFeesModel)
        assert result.symbol == "BTCUSDT"
        assert result.maker_commission == 0.0002
        assert result.taker_commission == 0.0004

    def test_adapt_trading_fees_empty_response(self) -> None:
        result = self.adapter.adapt_trading_fees({}, futures=False)
        assert result is None

    def test_adapt_trading_fees_list_response(self) -> None:
        raw_response: List[Dict[str, Any]] = [
            {
                "symbol": "BTCUSDT",
                "makerCommission": "0.001",
                "takerCommission": "0.001",
            }
        ]

        result = self.adapter.adapt_trading_fees(raw_response, futures=False)

        assert isinstance(result, GatewayTradingFeesModel)
        assert result.symbol == "BTCUSDT"

    def test_adapt_trading_fees_sandbox_with_cached_fees(self) -> None:
        with patch.object(BinanceAdapter, "_load_fees_config"):
            adapter = BinanceAdapter(source_name="binance")
            adapter._cached_fees = {
                "BTCUSDT": {
                    "maker_commission": 0.0002,
                    "taker_commission": 0.0005,
                }
            }

        if hasattr(adapter, "adapt_trading_fees_sandbox"):
            result = adapter.adapt_trading_fees_sandbox("BTCUSDT")

            assert isinstance(result, GatewayTradingFeesModel)
            assert result.symbol == "BTCUSDT"
            assert result.maker_commission == 0.0002
            assert result.taker_commission == 0.0005
            assert result.response is None

    def test_adapt_trading_fees_sandbox_without_cached_fees(self) -> None:
        with patch.object(BinanceAdapter, "_load_fees_config"):
            adapter = BinanceAdapter(source_name="binance")
            adapter._cached_fees = None

        if hasattr(adapter, "adapt_trading_fees_sandbox"):
            result = adapter.adapt_trading_fees_sandbox("BTCUSDT")

            assert isinstance(result, GatewayTradingFeesModel)
            assert result.symbol == "BTCUSDT"
            assert result.maker_commission == 0.0
            assert result.taker_commission == 0.0

    def test_adapt_trading_fees_sandbox_default_values(self) -> None:
        with patch.object(BinanceAdapter, "_load_fees_config"):
            adapter = BinanceAdapter(source_name="binance")
            adapter._cached_fees = {"OTHER": {}}

        if hasattr(adapter, "adapt_trading_fees_sandbox"):
            result = adapter.adapt_trading_fees_sandbox("ETHUSDT")

            assert isinstance(result, GatewayTradingFeesModel)
            assert result.symbol == "ETHUSDT"
            assert result.maker_commission == 0.0002
            assert result.taker_commission == 0.0005

    def test_adapt_tick_from_stream(self) -> None:
        raw_response: Dict[str, Any] = {
            "b": "42350.50",
            "a": "42351.00",
        }

        result = self.adapter.adapt_tick_from_stream(raw_response)

        assert isinstance(result, TickModel)
        assert result.bid_price == 42350.50
        assert result.ask_price == 42351.00
        assert result.price == (42350.50 + 42351.00) / 2
        assert result.sandbox is False
        assert isinstance(result.date, datetime.datetime)

    def test_adapt_tick_from_stream_zero_values(self) -> None:
        raw_response: Dict[str, Any] = {
            "b": "0.0",
            "a": "0.0",
        }

        result = self.adapter.adapt_tick_from_stream(raw_response)

        assert isinstance(result, TickModel)
        assert result.price == 0.0

    def test_validate_response_valid_list(self) -> None:
        response = [
            [1704067200000, "42350.50", "42500.00", "42300.00", "42450.75"],
        ]

        result = self.adapter.validate_response(response)

        assert result is True

    def test_validate_response_empty_list(self) -> None:
        result = self.adapter.validate_response([])
        assert result is False

    def test_validate_response_none(self) -> None:
        result = self.adapter.validate_response(None)
        assert result is False

    def test_validate_response_error_dict(self) -> None:
        response = {
            "code": -1121,
            "msg": "Invalid symbol.",
        }

        result = self.adapter.validate_response(response)

        assert result is False

    def test_validate_response_invalid_type(self) -> None:
        result = self.adapter.validate_response("invalid")
        assert result is False

    def test_parse_filters_price_filter(self) -> None:
        filters = [
            {
                "filterType": "PRICE_FILTER",
                "minPrice": "0.01",
                "maxPrice": "1000000.00",
                "tickSize": "0.01",
            }
        ]

        result = self.adapter._parse_filters(filters)

        assert result["min_price"] == 0.01
        assert result["max_price"] == 1000000.00
        assert result["tick_size"] == 0.01

    def test_parse_filters_lot_size(self) -> None:
        filters = [
            {
                "filterType": "LOT_SIZE",
                "minQty": "0.001",
                "maxQty": "1000.00",
                "stepSize": "0.001",
            }
        ]

        result = self.adapter._parse_filters(filters)

        assert result["min_quantity"] == 0.001
        assert result["max_quantity"] == 1000.00
        assert result["step_size"] == 0.001

    def test_parse_filters_min_notional(self) -> None:
        filters = [
            {
                "filterType": "MIN_NOTIONAL",
                "notional": "10.00",
            }
        ]

        result = self.adapter._parse_filters(filters)

        assert result["min_notional"] == 10.00

    def test_parse_filters_all_types(self) -> None:
        filters = [
            {
                "filterType": "PRICE_FILTER",
                "minPrice": "0.01",
                "maxPrice": "1000000.00",
                "tickSize": "0.01",
            },
            {
                "filterType": "LOT_SIZE",
                "minQty": "0.001",
                "maxQty": "1000.00",
                "stepSize": "0.001",
            },
            {
                "filterType": "MIN_NOTIONAL",
                "notional": "10.00",
            },
        ]

        result = self.adapter._parse_filters(filters)

        assert result["min_price"] == 0.01
        assert result["min_quantity"] == 0.001
        assert result["min_notional"] == 10.00

    def test_parse_margin_percent_required(self) -> None:
        symbol_info = {
            "requiredMarginPercent": "5.0",
        }

        result = self.adapter._parse_margin_percent(symbol_info)

        assert result == 5.0

    def test_parse_margin_percent_maint(self) -> None:
        symbol_info = {
            "maintMarginPercent": "3.0",
        }

        result = self.adapter._parse_margin_percent(symbol_info)

        assert result == 3.0

    def test_parse_margin_percent_none(self) -> None:
        symbol_info = {}

        result = self.adapter._parse_margin_percent(symbol_info)

        assert result is None

    def test_parse_optional_float_valid(self) -> None:
        assert parse_optional_float(value="123.45") == 123.45
        assert parse_optional_float(value=123.45) == 123.45
        assert parse_optional_float(value=123) == 123.0

    def test_parse_optional_float_invalid(self) -> None:
        assert parse_optional_float(value="invalid") is None
        assert parse_optional_float(value=None) is None

    def test_get_first_list(self) -> None:
        data = [{"key": "value"}, {"key2": "value2"}]

        result = self.adapter._get_first(data)

        assert result == {"key": "value"}

    def test_get_first_dict(self) -> None:
        data = {"key": "value"}

        result = self.adapter._get_first(data)

        assert result == {"key": "value"}

    def test_get_first_empty_list(self) -> None:
        data: List[Any] = []

        result = self.adapter._get_first(data)

        assert result == []
