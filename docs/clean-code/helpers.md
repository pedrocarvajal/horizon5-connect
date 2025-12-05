# Helper Guidelines

Guide on how helpers should be structured and organized.

- A helper must pass all linters using `make run-linter-checks FILE=path/to/file.py` or `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- A helper is a standalone function that performs a single, reusable task

# 1.0 File Structure

Each helper function must have its own dedicated file:

- `helpers/get_duration.py` - Contains `get_duration()`
- `helpers/get_env.py` - Contains `get_env()`
- `helpers/get_portfolio_by_path.py` - Contains `get_portfolio_by_path()`
- `helpers/get_progress_between_dates.py` - Contains `get_progress_between_dates()`
- `helpers/get_slug.py` - Contains `get_slug()`
- `helpers/parse_int.py` - Contains `parse_int()`
- `helpers/parse_float.py` - Contains `parse_float()`

**Rule**: One helper function per file. The file name must match the function name.

# 2.0 Naming Conventions

## 2.1 File and Function Names

| Requirement       | Description                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Start with a verb | `get_`, `parse_`, `format_`, `calculate_`, `validate_`, `convert_`, `build_`, `extract_` |
| Descriptive       | Name should clearly indicate what the function does                                      |
| Snake case        | Use `snake_case` for both file and function names                                        |
| Match exactly     | File name must equal function name (e.g., `get_duration.py` contains `get_duration()`)   |

## 2.2 Common Verb Prefixes

| Prefix       | Use Case                                 | Example                                        |
| ------------ | ---------------------------------------- | ---------------------------------------------- |
| `get_`       | Retrieve or compute a value              | `get_env()`, `get_duration()`, `get_slug()`    |
| `parse_`     | Convert input to specific type/format    | `parse_int()`, `parse_float()`, `parse_date()` |
| `format_`    | Transform data for display               | `format_currency()`, `format_percentage()`     |
| `calculate_` | Perform mathematical computation         | `calculate_profit()`, `calculate_margin()`     |
| `validate_`  | Check if input meets criteria            | `validate_email()`, `validate_symbol()`        |
| `convert_`   | Transform between types/units            | `convert_timestamp()`, `convert_currency()`    |
| `build_`     | Construct complex objects                | `build_query()`, `build_request()`             |
| `extract_`   | Pull specific data from larger structure | `extract_errors()`, `extract_metadata()`       |

# 3.0 Helper Template

```python
"""Brief description of what this helper does."""

from typing import ...  # Required type imports


def helper_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    One-line description of the function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised (if applicable)
    """
    # Implementation
    return result
```

# 4.0 Type Annotations

All helpers require complete type annotations:

```python
# Required: Full type annotations
def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    ...

# Required: Use typing module types
from typing import Any, Dict, List, Optional

def parse_optional_float(value: Any) -> Optional[float]:
    ...
```

# 5.0 Private Helper Functions

If a helper requires auxiliary functions, they must be private (prefixed with underscore) and placed in the same file:

```python
"""URL-friendly slug generation utilities."""

import re
import unicodedata


def _normalize_to_ascii(text: str) -> str:
    """Remove accentuated characters, converting to ASCII."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def get_slug(title: str, separator: str = "-") -> str:
    """Generate URL-friendly slug from a title."""
    title = _normalize_to_ascii(title)
    # ... rest of implementation
    return title.strip(separator)
```

**Rules for private helpers**:

- Prefix with underscore (`_normalize_to_ascii`, not `ascii`)
- Only used by the main helper in the same file
- Not exported or used elsewhere

# 6.0 File Location

## 6.1 Generic Helpers

Reusable helpers go in the root `helpers/` directory:

- `helpers/get_duration.py`
- `helpers/get_env.py`
- `helpers/parse_int.py`

## 6.2 Domain-Specific Helpers

Helpers specific to a service go in `services/<service>/helpers/`:

- `services/gateway/helpers/build_order_params.py`
- `services/gateway/helpers/validate_credentials.py`
- `services/orderbook/helpers/calculate_margin.py`
- `services/orderbook/helpers/validate_order.py`

# 7.0 Examples

## 7.1 Simple Helper

```python
"""Environment variable retrieval utilities."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable value.

    Args:
        key: Environment variable key
        default: Default value if key doesn't exist (default: None)
        required: If True, raises ValueError when variable is not set (default: False)

    Returns:
        Environment variable value or default if key doesn't exist

    Raises:
        ValueError: If required=True and the environment variable is not set
    """
    value = os.getenv(key, default)

    if required and value is None:
        raise ValueError(f"Environment variable '{key}' is required but not set.")

    return value
```

## 7.2 Helper with Private Function

```python
"""URL-friendly slug generation utilities."""

import re
import unicodedata
from typing import Dict, Optional


def _normalize_to_ascii(text: str) -> str:
    """Remove accentuated characters, converting to ASCII."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def get_slug(
    title: str,
    separator: str = "-",
    dictionary: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generate URL-friendly slug from a title.

    Args:
        title: Title to convert to slug
        separator: Separator character (default: "-")
        dictionary: Custom replacement dictionary (default: {"@": "at"})

    Returns:
        URL-friendly slug string
    """
    if dictionary is None:
        dictionary = {"@": "at"}

    title = _normalize_to_ascii(title)
    # ... implementation
    return title.strip(separator)
```

# 8.0 Anti-patterns to Avoid

| Anti-pattern                    | Problem                          | Solution                           |
| ------------------------------- | -------------------------------- | ---------------------------------- |
| Multiple helpers in one file    | Violates single-responsibility   | Split into separate files          |
| File name differs from function | Hard to locate and import        | Rename file to match function      |
| Non-descriptive names           | Unclear purpose                  | Use verb prefix + descriptive name |
| Public auxiliary functions      | Pollutes namespace               | Prefix with underscore             |
| Missing type annotations        | Reduces code quality             | Add complete type hints            |
| Generic names like `utils.py`   | Becomes a dumping ground         | Use specific helper files          |
| Helper without verb prefix      | Unclear if it's a helper         | Start with `get_`, `parse_`, etc.  |
| Business logic in helpers       | Helpers should be pure utilities | Move logic to services             |

# 9.0 Importing Helpers

```python
# Import specific helper function
from helpers.get_env import get_env
from helpers.parse_int import parse_int

# Usage
api_key = get_env("API_KEY", required=True)
count = parse_int(raw_value)
```

# 10.0 Testing Helpers

Helper tests go in `tests/unit/` with the pattern `test_<helper_name>.py`:

- `tests/unit/test_get_duration.py`
- `tests/unit/test_get_env.py`
- `tests/unit/test_parse_int.py`
