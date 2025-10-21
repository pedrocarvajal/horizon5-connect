# Naming Conventions

This guide defines the standard for naming variables, functions, classes, constants and more in Python.

## Quick Reference

| Element   | Convention | Correct Example    | Incorrect Example |
| --------- | ---------- | ------------------ | ----------------- |
| Classes   | PascalCase | `Order`, `Trade`   | `order`, `TRADE`  |
| Variables | snake_case | `total_profit`     | `totalProfit`     |
| Functions | snake_case | `calculate_profit` | `CalculateProfit` |
| Constants | UPPER_CASE | `MAX_DAILY_TRADES` | `maxDailyTrades`  |
| Files     | snake_case | `order.py`         | `Order.py`        |

## Classes

Use singular names in `PascalCase`.

Correct examples:

- `Order`
- `Trade`
- `Logger`
- `Strategy`

Incorrect examples:

- `order` (must be PascalCase)
- `STRATEGY` (must be PascalCase)
- `Orders` (must be singular)

## Variables

All variables must be in `snake_case`.

Correct examples:

- `total_profit`
- `order_count`
- `max_drawdown`
- `current_price`

Incorrect examples:

- `totalProfit` (must be snake_case)
- `OrderCount` (must be snake_case)
- `MAXDRAWDOWN` (must be snake_case for variables, use for constants only)

## Functions

Should ideally be an action verb, short and descriptive, always using `snake_case`.

Correct examples:

- `calculate_profit()`
- `open_order()`
- `get_session_time_range()`
- `is_market_closed()`

Incorrect examples:

- `CalculateProfit()` (must be snake_case)
- `calculateProfit()` (must be snake_case)
- `profit()` (must include action verb)

## Constants

Must be in `UPPER_CASE` with underscores.

Correct examples:

- `MAX_DAILY_TRADES`
- `DEFAULT_STOP_LOSS`
- `API_TIMEOUT`

Incorrect examples:

- `maxDailyTrades` (must be UPPER_CASE)
- `Max_Daily_Trades` (must be UPPER_CASE)
- `MAX_DAILY_TRADES_VALUE` (avoid redundant suffixes)

## Files

Must use `snake_case` and match the main class or module they contain.

Correct examples:

- `order.py` for class `Order`
- `strategy.py` for class `Strategy`
- `calculate_profit.py` for function `calculate_profit()`

Incorrect examples:

- `Order.py` (must be snake_case)
- `my-order.py` (use underscores, not hyphens)
- `orders.py` for class `Order` (should match)
