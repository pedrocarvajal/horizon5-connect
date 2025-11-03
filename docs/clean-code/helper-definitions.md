# Helper Definitions

This guide defines what helpers are and how to structure them properly.
Follow these principles when creating utility functions.

## What is a Helper?

A helper is a standalone utility function that:

- Performs a single, well-defined task
- Is reusable across different parts of the application
- Has no side effects (pure function when possible)
- Is easy to test in isolation
- Has a clear, descriptive name

## Rules

- One helper = one responsibility
- Prefer pure functions (same input → same output, no side effects)
- Use descriptive names that explain what the helper does
- Keep helpers simple and focused
- Avoid class-based helpers unless state management is required
- Type all parameters and return values
- Raise specific exceptions for error cases

## Naming Conventions

### Action-Based Names

Use verb phrases that describe the action:

```python
get_slug_from(text: str) -> str
calculate_sharpe_ratio(returns: list[float]) -> float
format_currency(amount: float) -> str
parse_date_string(date_str: str) -> datetime
```

### Boolean Helpers

Use `is_`, `has_`, `can_`, or `should_` prefixes:

```python
is_valid_email(email: str) -> bool
has_permission(user: User, permission: str) -> bool
can_access_resource(user: User, resource: Resource) -> bool
should_retry_request(attempt: int, max_attempts: int) -> bool
```

### Conversion Helpers

Use `to_` or `from_` patterns:

```python
to_dict(obj: Any) -> dict
from_json(json_str: str) -> dict
to_snake_case(text: str) -> str
from_camel_case(text: str) -> str
```

## File Organization

### Directory Structure

```
helpers/
├── __init__.py
├── get_slug.py
├── get_sharpe_ratio_from.py
├── get_r2_from.py
└── format_date.py
```

### Module Pattern

Each helper should be in its own file with the same name:

```python
from apps.core.helpers.get_slug import get_slug
from apps.core.helpers.calculate_sharpe_ratio import calculate_sharpe_ratio
```

### **init**.py Exports

Export all helpers for easy imports:

```python
from .get_slug import get_slug
from .calculate_sharpe_ratio import calculate_sharpe_ratio

__all__ = [
    "get_slug",
    "calculate_sharpe_ratio",
]
```

## Helper Structure

### Basic Helper Template

```python
def helper_name(param: Type) -> ReturnType:
    if not param:
        raise ValueError("Description of what went wrong")

    result = perform_operation(param)

    return result
```

### Helper with Default Values

```python
def format_currency(
    amount: float,
    currency: str = "USD",
    decimal_places: int = 2
) -> str:
    if amount < 0:
        raise ValueError("Amount must be non-negative")

    formatted = f"{amount:,.{decimal_places}f}"
    return f"{currency} {formatted}"
```

### Helper with Type Union

```python
def get_value_or_default(
    value: str | None,
    default: str = ""
) -> str:
    return value if value is not None else default
```

## Examples

### String Manipulation

```python
def get_slug(
    text: str,
    separator: str = "-",
    language: str = "en"
) -> str:
    import re
    from unicodedata import normalize

    if not text:
        raise ValueError("Text cannot be empty")

    text = normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", separator, text)

    return text.strip(separator)
```

### Mathematical Calculations

```python
def calculate_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float = 0.0
) -> float:
    import numpy as np

    if not returns:
        raise ValueError("Returns list cannot be empty")

    excess_returns = np.array(returns) - risk_free_rate

    if np.std(excess_returns) == 0:
        return 0.0

    return np.mean(excess_returns) / np.std(excess_returns)
```

### Data Transformation

```python
def to_snake_case(text: str) -> str:
    import re

    if not text:
        return ""

    text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)

    return text.lower()
```

### Validation

```python
def is_valid_email(email: str) -> bool:
    import re

    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
```

### Date/Time Formatting

```python
def format_date(
    date: datetime,
    format: str = "%Y-%m-%d"
) -> str:
    if not isinstance(date, datetime):
        raise TypeError("Expected datetime object")

    return date.strftime(format)
```

### Collection Operations

```python
def chunk_list(
    items: list[Any],
    chunk_size: int
) -> list[list[Any]]:
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    return [
        items[i:i + chunk_size]
        for i in range(0, len(items), chunk_size)
    ]
```

### Safe Operations

```python
def safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0
) -> float:
    return numerator / denominator if denominator != 0 else default
```

## Anti-Patterns to Avoid

### ❌ Multiple Responsibilities

```python
def process_user_data(user: dict) -> dict:
    validated = validate_user(user)
    formatted = format_user(validated)
    saved = save_user(formatted)
    email_sent = send_welcome_email(saved)
    return saved
```

Instead, split into separate helpers.

### ❌ Side Effects

```python
def get_user_count() -> int:
    users = database.query("SELECT * FROM users")
    logger.info("Fetched user count")
    return len(users)
```

Helpers should not have side effects like logging or database calls directly.

### ❌ Vague Names

```python
def process(data: Any) -> Any:
    return do_something(data)

def util(x: int) -> int:
    return x * 2
```

Use descriptive names that explain the purpose.

### ❌ Class-Based Helpers Without State

```python
class StringHelper:
    @staticmethod
    def to_upper(text: str) -> str:
        return text.upper()
```

Use simple functions instead of classes with only static methods.

## Testing Helpers

Each helper should have comprehensive tests:

```python
def test_get_slug():
    assert get_slug("Hello World") == "hello-world"
    assert get_slug("Python is great!") == "python-is-great"
    assert get_slug("Café") == "cafe"

    with pytest.raises(ValueError):
        get_slug("")

def test_calculate_sharpe_ratio():
    returns = [0.1, 0.2, -0.05, 0.15]
    ratio = calculate_sharpe_ratio(returns)
    assert isinstance(ratio, float)
    assert ratio > 0

def test_is_valid_email():
    assert is_valid_email("user@example.com") == True
    assert is_valid_email("invalid-email") == False
    assert is_valid_email("") == False
```

## When to Create a Helper

Create a helper when:

- The same logic is used in 2+ places
- The function is pure and stateless
- The operation is generic and reusable
- It simplifies complex code
- It improves testability

Don't create a helper when:

- The logic is highly specific to one use case
- It requires access to instance state
- It's a simple one-liner that doesn't improve readability
- It would create unnecessary abstraction
