# Class Guidelines

Guide on how a class should be structured and organized.

- A class must pass all linters configured in the project using `make run-linter-checks FILE=path/to/file.py` or directly `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- A class must be organized based on guideline 1.0
- For code style and formatting, review guideline 2.0
- A class must have its correct interface implementation (see how interfaces are defined or built in: [interfaces.md](./interfaces.md))
- For variable naming conventions, see [variables.md](./commons/variables.md)
- For complex types, create models instead of using `Dict[str, Any]` or similar. See [models.md](./commons/models.md)

# Guidelines

## 1.0 Class Hierarchy

```python
class Name(Interface):
    # Constants (UPPER_CASE)
    # {Blank separator line}

    # Variables (_lower_case with underscore prefix)
    # {Blank separator line}

    # External services or class definitions
    # {Blank separator line}

    # Initialization function __init__
    # {Blank separator line}

    # Public methods (sorted alphabetically)
    # {Blank separator line}

    # Private methods (sorted alphabetically)
    # {Blank separator line}

    # Getters
    # {Blank separator line}

    # Setters
    # {Blank separator line}
```

### 1.1 Constants vs Variables

- **Constants**: Use `UPPER_CASE`. Values that never change during class lifetime.
- **Variables**: Use `_lower_case` with underscore prefix. Instance state that may change.

## 2.0 How to Format Correctly

### 2.1 Multi-line Parameters

Avoid:

```python
def get_progress_between_dates( start_date_in_timestamp: int, end_date_in_timestamp: int, current_date_in_timestamp: int) -> float:
```

Preferred:

```python
def get_progress_between_dates(
    start_date_in_timestamp: int,
    end_date_in_timestamp: int,
    current_date_in_timestamp: int,
) -> float:
```

The goal is to avoid long lines and use proper formatting, with parameters listed one below another.
This applies to function definitions, function calls, class usage, argument passing, and even variable destructuring.

### 2.2 Imports

Group imports in this order, separated by blank lines:

```python
import os
import sys

from typing import List, Optional

from pydantic import BaseModel

from enums.order_side import OrderSide
from models.tick import TickModel
```

Order: standard library, third-party, local imports.

### 2.3 Lists and Dictionaries

Avoid:

```python
config = {"key_one": "value", "key_two": "value", "key_three": "value"}
```

Preferred:

```python
config = {
    "key_one": "value",
    "key_two": "value",
    "key_three": "value",
}
```

Always use trailing commas in multi-line structures.

### 2.4 Complex Conditionals

Avoid:

```python
if user.is_active and user.has_permission("admin") and user.account.is_verified:
```

Preferred:

```python
if (
    user.is_active
    and user.has_permission("admin")
    and user.account.is_verified
):
```

### 2.5 Getters and Setters

Use `@property` for getters and `@<name>.setter` for setters.

**Important**: If the class implements an interface, public getters and setters must be defined in the interface first (see [interfaces.md](./interfaces.md)). The class only provides the implementation.

```python
class OrderbookService(OrderbookInterface):
    def __init__(self) -> None:
        self._balance: float = 0.0

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        self._balance = value
```

For classes without an interface:

```python
class Order:
    def __init__(self) -> None:
        self._status: str = "pending"

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value
```

## 3.0 Anti-patterns to Avoid

- **God classes**: Classes with too many responsibilities. Split into smaller, focused classes.
- **Long methods**: Methods doing multiple things. Extract into smaller private methods.
- **Deep nesting**: More than 3 levels of indentation. Use early returns or extract logic.
- **Magic numbers**: Use named constants instead of hardcoded values.
- **Duplicate code**: Extract common logic into reusable methods or helpers.
