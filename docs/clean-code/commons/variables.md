# Naming Conventions

Guide on how to name variables, functions, classes, and other elements in Python.

# 1.0 Case Conventions

| Element           | Convention                        | Example                                    |
| ----------------- | --------------------------------- | ------------------------------------------ |
| Classes           | `PascalCase`                      | `OrderModel`, `TickService`                |
| Interfaces        | `PascalCase` + `Interface` suffix | `AssetInterface`, `StrategyInterface`      |
| Models            | `PascalCase` + `Model` suffix     | `TickModel`, `OrderModel`                  |
| Enums             | `PascalCase`                      | `OrderSide`, `OrderStatus`                 |
| Functions/Methods | `snake_case`                      | `get_price()`, `calculate_profit()`        |
| Variables         | `snake_case`                      | `current_price`, `order_count`             |
| Constants         | `UPPER_SNAKE_CASE`                | `MAX_RETRIES`, `DEFAULT_TIMEOUT`           |
| Private methods   | `_snake_case`                     | `_calculate_margin()`, `_validate_order()` |
| Private variables | `_snake_case`                     | `_status`, `_balance`                      |
| Module files      | `snake_case`                      | `order_side.py`, `tick_model.py`           |

# 2.0 Naming Rules

## 2.1 Be Descriptive

Names should clearly describe what they store or do.

Avoid:

```python
x = 100
d = {}
temp = get_data()
```

Preferred:

```python
max_order_volume = 100
order_cache = {}
market_tick = get_latest_tick()
```

## 2.2 Boolean Variables

Use prefixes that indicate state: `is_`, `has_`, `can_`, `should_`, `was_`.

Avoid:

```python
active = True
running = False
permission = True
```

Preferred:

```python
is_active = True
is_running = False
has_permission = True
can_execute = True
should_retry = False
was_processed = True
```

## 2.3 Boolean Methods

Use same prefixes for methods that return boolean:

```python
def is_open(self) -> bool:
    return self._status == "open"

def has_sufficient_balance(self) -> bool:
    return self._balance >= self._minimum_balance

def can_place_order(self) -> bool:
    return self.is_active and self.has_sufficient_balance()
```

## 2.4 Collections

Use plural names for lists, sets, and other collections:

Avoid:

```python
order = []
strategy = {}
```

Preferred:

```python
orders = []
strategies = {}
active_positions = []
```

## 2.5 Functions and Methods

Use verbs that describe the action:

| Action          | Prefix       | Example                                      |
| --------------- | ------------ | -------------------------------------------- |
| Retrieve data   | `get_`       | `get_balance()`, `get_orders()`              |
| Set data        | `set_`       | `set_status()`, `set_price()`                |
| Calculate       | `calculate_` | `calculate_profit()`, `calculate_margin()`   |
| Validate        | `validate_`  | `validate_order()`, `validate_credentials()` |
| Check condition | `check_`     | `check_if_ready()`, `check_balance()`        |
| Convert         | `to_`        | `to_dict()`, `to_json()`                     |
| Parse           | `parse_`     | `parse_response()`, `parse_timestamp()`      |
| Create          | `create_`    | `create_order()`, `create_snapshot()`        |
| Update          | `update_`    | `update_status()`, `update_balance()`        |
| Delete          | `delete_`    | `delete_order()`, `delete_cache()`           |
| Handle          | `handle_`    | `handle_error()`, `handle_tick()`            |
| Process         | `process_`   | `process_order()`, `process_tick()`          |
| Initialize      | `setup_`     | `setup_logging()`, `setup_gateway()`         |

## 2.6 Avoid Abbreviations

Use full words for clarity.

Avoid:

```python
calc_pft()
get_usr_bal()
proc_ord()
```

Preferred:

```python
calculate_profit()
get_user_balance()
process_order()
```

Acceptable abbreviations (widely understood):

- `id` � identifier
- `config` � configuration
- `max` / `min` � maximum / minimum
- `num` � number (only in `num_items` style)

## 2.7 Units in Names

Include units when relevant:

```python
timeout_seconds = 30
timeout_milliseconds = 30000
price_in_usd = 100.0
volume_in_btc = 0.5
timestamp_milliseconds = 1699900000000
```

# 3.0 Anti-patterns to Avoid

- **Single letter variables**: Except `i`, `j`, `k` in small loops.
- **Generic names**: `data`, `info`, `temp`, `result`, `value`.
- **Type in name**: `order_list`, `price_float` (use type hints instead).
- **Negated booleans**: `is_not_active` (use `is_active` and negate in logic).
- **Inconsistent naming**: Mixing conventions within the same codebase.
