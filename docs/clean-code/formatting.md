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

## Summary

| Scenario                       | Trailing Comma | Named Arguments |
| ------------------------------ | -------------- | --------------- |
| Function with only `self`      | ❌ No          | N/A             |
| Function with `self` + 1 param | ✅ Yes         | ✅ Yes          |
| Function with multiple params  | ✅ Yes         | ✅ Yes          |
| Call with single argument      | N/A            | ✅ Yes          |
| Call with multiple arguments   | N/A            | ✅ Yes          |

## Benefits

- **Trailing commas**: Make it easier to add new arguments without modifying existing lines
- **Named arguments**: Improve code readability and prevent argument order mistakes
- **Consistency**: All code follows the same formatting pattern, making it easier to read and maintain
