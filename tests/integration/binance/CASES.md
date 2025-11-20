# Test Cases - Binance Gateway Integration

This document contains all test cases for Binance gateway integration tests organized by category.

## Summary

| Category             | File                        | Test Count |
| -------------------- | --------------------------- | ---------- |
| Account Management   | `test_binance_account.py`   | 2          |
| Order Management     | `test_binance_order.py`     | 4          |
| Position Management  | `test_binance_positions.py` | 2          |
| Symbol Information   | `test_binance_symbol.py`    | 4          |
| Market Data (Klines) | `test_binance_kline.py`     | 1          |
| Trade History        | `test_binance_trade.py`     | 2          |
| Streaming            | `test_binance_stream.py`    | 1          |
| Gateway Handler      | `test_gateway_handler.py`   | 3          |

---

## 1. Account Management (`test_binance_account.py`)

| Test Method                | Description                                      | Validations/Behaviors                                                                                                                                                                                                                                                |
| -------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_get_futures_account` | Retrieves futures account information            | Returns `GatewayAccountModel` instance<br>Balance > 0<br>NAV > 0<br>Locked >= 0<br>Margin >= 0<br>Exposure >= 0<br>At least 1 balance entry<br>Response data is not None                                                                                             |
| `test_get_verification`    | Verifies account configuration and trading setup | Opens test position to verify account<br>Returns verification dictionary<br>Checks required_leverage (>= 1)<br>Checks usdt_balance (> 0)<br>Checks cross_margin mode<br>Checks one_way_mode<br>Checks trading_permissions<br>Closes test position after verification |

---

## 2. Order Management (`test_binance_order.py`)

| Test Method               | Description                               | Validations/Behaviors                                                                                                                                                                                                                                |
| ------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_place_order_market` | Places a market order through the gateway | Places MARKET BUY order for BTCUSDT<br>Order is valid GatewayOrderModel<br>Order ID is not empty<br>Order type is MARKET<br>Order status is PENDING or EXECUTED<br>Volume > 0<br>Cleans up order after test                                          |
| `test_cancel_order`       | Places and cancels a limit order          | Calculates limit price with discount (90%)<br>Places LIMIT BUY order<br>Order is valid GatewayOrderModel<br>Order type is LIMIT<br>Cancels order through gateway<br>Cancelled order matches original order ID<br>Cancelled order status is CANCELLED |
| `test_get_order`          | Retrieves a single order by ID            | Places MARKET order<br>Retrieves order by ID from gateway<br>Retrieved order matches original order<br>Order ID matches<br>Order symbol matches<br>Response data is not None<br>Cleans up order after test                                           |
| `test_get_orders`         | Retrieves multiple orders with filters    | Queries orders for last 90 days<br>Returns list of GatewayOrderModel instances<br>All orders have valid symbol (BTCUSDT)<br>All orders have non-empty ID<br>All orders have response data                                                            |

---

## 3. Position Management (`test_binance_positions.py`)

| Test Method                    | Description                            | Validations/Behaviors                                                                                                                                                                                                                   |
| ------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_get_positions`           | Retrieves all open positions           | Returns list of positions<br>All positions are GatewayPositionModel instances<br>If positions exist:<br> - Symbol is not empty<br> - Side is BUY, SELL, or None<br> - Volume != 0<br> - Open price >= 0<br> - Response data is not None |
| `test_get_positions_by_symbol` | Retrieves positions filtered by symbol | Filters positions by BTCUSDT symbol<br>Returns list of GatewayPositionModel instances<br>All returned positions match requested symbol<br>Validates position data structure                                                             |

---

## 4. Symbol Information (`test_binance_symbol.py`)

| Test Method              | Description                       | Validations/Behaviors                                                                                                                                                                                 |
| ------------------------ | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_get_symbol_info`   | Retrieves symbol information      | Returns GatewaySymbolInfoModel instance<br>Symbol is not empty<br>Base asset is not empty<br>Quote asset is not empty<br>Price precision >= 0<br>Quantity precision >= 0<br>Response data is not None |
| `test_get_trading_fees`  | Retrieves trading fees for symbol | Returns GatewayTradingFeesModel instance<br>Symbol is not empty<br>Maker commission is not None and >= 0<br>Taker commission is not None and >= 0<br>Response data is not None                        |
| `test_get_leverage_info` | Retrieves leverage information    | Opens test position to get leverage info<br>Returns GatewayLeverageInfoModel instance<br>Symbol is not empty<br>Leverage >= 1<br>Response data is not None<br>Closes test position after verification |
| `test_set_leverage`      | Sets leverage for a symbol        | Sets leverage to 20x for BTCUSDT<br>Returns True on success<br>Verifies leverage was set correctly                                                                                                    |

---

## 5. Market Data - Klines (`test_binance_kline.py`)

| Test Method       | Description                                 | Validations/Behaviors                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `test_get_klines` | Retrieves historical kline/candlestick data | Fetches klines for BTCUSDT (1d timeframe)<br>Date range: 2024-01-01 to 2024-01-02<br>Uses callback to collect klines<br>Returns at least 1 kline<br>All klines are GatewayKlineModel instances<br>Validates kline data:<br> - Symbol is BTCUSDT<br> - Open time > 0<br> - Close time > 0<br> - Open price > 0<br> - High price > 0<br> - Low price > 0<br> - Close price > 0<br> - Volume >= 0<br> - Response data is not None |

---

## 6. Trade History (`test_binance_trade.py`)

| Test Method                 | Description                         | Validations/Behaviors                                                                                                                                                                                                                                                                                |
| --------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_get_trades`           | Retrieves all trade history         | Returns list of trades<br>All trades are GatewayTradeModel instances<br>If trades exist:<br> - Trade ID is not empty<br> - Order ID is not empty<br> - Symbol is not empty<br> - Side is BUY, SELL, or None<br> - Price >= 0<br> - Volume >= 0<br> - Commission >= 0<br> - Response data is not None |
| `test_get_trades_by_symbol` | Retrieves trades filtered by symbol | Filters trades by BTCUSDT symbol<br>Returns list of GatewayTradeModel instances<br>All returned trades match requested symbol<br>Validates trade data structure                                                                                                                                      |

---

## 7. Streaming (`test_binance_stream.py`)

| Test Method   | Description                       | Validations/Behaviors                                                                                                                                                                                                                                                                                                                                |
| ------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_stream` | Tests WebSocket stream connection | Connects to btcusdt@bookTicker stream<br>Runs stream for 5 seconds<br>Receives ticks via async callback<br>Returns at least 1 tick<br>All ticks are TickModel instances<br>Validates tick data:<br> - Price > 0<br> - Bid price > 0<br> - Ask price > 0<br> - Date is not None<br> - is_simulated is False<br>Handles stream cancellation gracefully |

---

## 8. Gateway Handler (`test_gateway_handler.py`)

| Test Method                                     | Description                                     | Validations/Behaviors                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_gateway_handler_initialization`           | Tests GatewayHandler initialization             | Handler is initialized<br>Handler has gateway instance<br>Handler is not in backtest mode<br>Verifies handler configuration                                                                                                                                                                                                                                                                                           |
| `test_open_order_market_with_polling`           | Tests order opening with status polling         | Builds OrderModel for MARKET order<br>Calls handler.open_order()<br>Returns True in production mode<br>Order has gateway_order_id<br>Order status is OPENING or OPEN<br>Polls until order reaches OPEN status<br>Validates executed order:<br> - Status is OPEN<br> - Executed volume > 0<br> - Price >= 0<br> - Updated timestamp is not None<br> - Trades have valid price and volume<br>Cleans up order after test |
| `test_open_order_backtest_mode`                 | Tests order opening prevention in backtest mode | Creates handler with backtest=True<br>Builds OrderModel with backtest=True<br>Calls handler.open_order()<br>Returns False (order not placed)<br>Order does not have gateway_order_id<br>Verifies backtest mode prevents real orders                                                                                                                                                                                   |
| `test_open_order_with_invalid_gateway_response` | Tests error handling for invalid orders         | Builds OrderModel with invalid symbol<br>Builds OrderModel with invalid volume (0.0)<br>Calls handler.open_order()<br>Returns False (order rejected)<br>Verifies invalid orders are properly rejected                                                                                                                                                                                                                 |

---

## Notes

- All tests use `BinanceWrapper` base class for common setup and helper methods
- Tests run against Binance sandbox/testnet environment (sandbox mode must be enabled)
- All tests verify account credentials are properly configured before execution
- Order cleanup is performed after tests that create positions/orders
- Tests use default symbol BTCUSDT and default volume 0.002 for consistency
- Streaming tests use async/await patterns and handle cancellation gracefully
- Gateway Handler tests verify both production and backtest modes
- All tests validate response data structure and required fields
