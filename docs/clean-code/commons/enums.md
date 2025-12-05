# Enum Guidelines

Guide on how enums should be structured and organized.

- An enum must pass all linters configured in the project using `make run-linter-checks FILE=path/to/file.py` or directly `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- An enum must be organized based on guideline 1.0
- For code style and formatting, review guideline 2.0
- Enums define a fixed set of named constants for type-safe value handling

# Guidelines

## 1.0 Enum Hierarchy

```python
@unique
class NameEnum(Enum):
    # Enum values (UPPER_CASE)
    # {Blank separator line}

    # Helper methods (if needed)
    # {Blank separator line}
```

## 2.0 How to Define Enums

### 2.1 Basic Enum

Use `@unique` decorator to prevent duplicate values:

```python
from enum import Enum, unique

@unique
class OrderStatus(Enum):
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
```

### 2.2 String Enum

Inherit from `str` for direct string operations and JSON serialization:

```python
@unique
class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

    def is_buy(self) -> bool:
        return self == OrderSide.BUY

    def is_sell(self) -> bool:
        return self == OrderSide.SELL
```

### 2.3 Enum with Methods

Add helper methods for common operations:

```python
@unique
class Timeframe(Enum):
    ONE_MINUTE = "1m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"

    def to_seconds(self) -> int:
        mapping = {
            "1m": 60,
            "1h": 3600,
            "1d": 86400,
        }
        return mapping[self.value]
```

### 2.4 Imports

```python
from enum import Enum, unique
```

### 2.5 File Naming

Each enum should be in its own file under `enums/` directory:

- `enums/order_side.py` ’ `OrderSide`
- `enums/order_status.py` ’ `OrderStatus`
- `enums/timeframe.py` ’ `Timeframe`

## 3.0 Anti-patterns to Avoid

- **Missing `@unique`**: Always use `@unique` decorator to prevent duplicate values.
- **Magic strings**: Use enums instead of raw strings for fixed sets of values.
- **Large enums**: If an enum has too many values, consider if it should be a different data structure.
- **Business logic in enums**: Keep helper methods simple. Complex logic belongs in services.
