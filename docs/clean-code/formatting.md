# Code Formatting Conventions

This guide defines the standard for formatting function definitions and function calls in Python.

## Function Arguments Formatting

### Comma Trailing Rule

When a function has **multiple arguments** (more than one), the last argument must be followed by a trailing comma.

**Correct examples:**

```python
def example_function(
    self,
    param1: str,
    param2: int,
) -> None:
    pass

def another_function(
    self,
    value: float,
    name: str,
    optional: Optional[str] = None,
) -> str:
    pass
```

**Incorrect examples:**

```python
def example_function(
    self,
    param1: str,
    param2: int
) -> None:
    pass

def another_function(
    self,
    value: float,
    name: str,
    optional: Optional[str] = None
) -> str:
    pass
```

### Single Argument Exception

When a function has **only one argument** (including only `self`), no trailing comma is required.

**Correct examples:**

```python
def single_param(self) -> None:
    pass

def helper_function(value: str) -> str:
    pass

result = process_data(data)
result = helper_function(value)
```

**Incorrect examples:**

```python
def single_param(self,) -> None:
    pass

def helper_function(value: str,) -> str:
    pass

result = process_data(data,)
result = helper_function(value,)
```

## Function Call Formatting

### Named Arguments Requirement

**All function calls must use named arguments (keyword arguments).** This improves code readability and reduces the risk of passing arguments in the wrong order.

**Correct examples:**

```python
result = adapter.adapt_symbol_info(response=raw_data)
order = gateway.open(
    symbol=symbol,
    side=side,
    order_type=order_type,
    volume=volume,
)
fees = adapter.adapt_trading_fees(
    response=raw_data,
    futures=futures,
)
```

**Incorrect examples:**

```python
result = adapter.adapt_symbol_info(raw_data)
order = gateway.open(symbol, side, order_type, volume)
fees = adapter.adapt_trading_fees(raw_data, futures)
```

### Single Argument Calls

Even when calling a function with a single argument, use named arguments.

**Correct examples:**

```python
result = adapter.adapt_symbol_info(response=raw_data)
leverage = gateway.get_leverage_info(symbol=symbol)
signature = self._generate_signature(query_string=query_string)
```

**Incorrect examples:**

```python
result = adapter.adapt_symbol_info(raw_data)
leverage = gateway.get_leverage_info(symbol)
signature = self._generate_signature(query_string)
```

## Code Block Formatting

### Logical Block Spacing

**Blank lines must be used to separate logical blocks of code.** This improves readability and helps distinguish different logical sections.

#### Rule: Blank Line After Context-Setting Operations

When an operation sets up context for a control structure (if/else, for, while, etc.), there must be a blank line between the context-setting operation and the control structure.

**Correct examples:**

```python
symbol_info = gateway.get_symbol_info(symbol="btcusdt")

if symbol_info is None:
    self._log.warning("Could not get symbol info, using default price")
    limit_price = 200000.0

data = fetch_data()

for item in data:
    process(item)
```

**Incorrect examples:**

```python
symbol_info = gateway.get_symbol_info(symbol="btcusdt")
if symbol_info is None:
    self._log.warning("Could not get symbol info, using default price")
    limit_price = 200000.0

data = fetch_data()
for item in data:
    process(item)
```

#### Rule: Blank Lines Within Logical Blocks

Within a logical block (if/else, for loop body, etc.), use blank lines to separate distinct sub-operations or calculations from subsequent conditional logic.

**Correct examples:**

```python
else:
    min_price = symbol_info.min_price or 100.0
    max_price = symbol_info.max_price or 200000.0
    limit_price = min_price * 10

    if limit_price > max_price:
        limit_price = max_price * 0.9

result = calculate_value()

if result > threshold:
    handle_exception()
```

**Incorrect examples:**

```python
else:
    min_price = symbol_info.min_price or 100.0
    max_price = symbol_info.max_price or 200000.0
    limit_price = min_price * 10
    if limit_price > max_price:
        limit_price = max_price * 0.9

result = calculate_value()
if result > threshold:
    handle_exception()
```

#### Rule: No Blank Lines for Related Operations

Do not add blank lines between closely related operations that form a single logical unit.

**Correct examples:**

```python
min_price = symbol_info.min_price or 100.0
max_price = symbol_info.max_price or 200000.0
limit_price = min_price * 10
```

**Incorrect examples:**

```python
min_price = symbol_info.min_price or 100.0

max_price = symbol_info.max_price or 200000.0

limit_price = min_price * 10
```

## Summary

| Scenario                       | Trailing Comma | Named Arguments | Blank Lines |
| ------------------------------ | -------------- | --------------- | ----------- |
| Function with only `self`      | ❌ No          | N/A             | N/A         |
| Function with `self` + 1 param | ✅ Yes         | ✅ Yes          | N/A         |
| Function with multiple params  | ✅ Yes         | ✅ Yes          | N/A         |
| Call with single argument      | N/A            | ✅ Yes          | N/A         |
| Call with multiple arguments   | N/A            | ✅ Yes          | N/A         |
| Before control structures      | N/A            | N/A             | ✅ Yes      |
| Between sub-operations & logic | N/A            | N/A             | ✅ Yes      |

## Benefits

- **Trailing commas**: Make it easier to add new arguments without modifying existing lines
- **Named arguments**: Improve code readability and prevent argument order mistakes
- **Blank lines**: Separate logical blocks visually, making code flow easier to understand
- **Consistency**: All code follows the same formatting pattern, making it easier to read and maintain
