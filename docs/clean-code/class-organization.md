# Class Organization

This guide applies when auditing a class during code review.
Follow these organization principles.

## Rules

- Do not modify method signatures or logic
- Reorganize methods vertically into clear sections
- Use proper naming conventions (underscore prefix for private members)

## Recommended Section Order

1. Constants
2. Public variables
3. Private variables (prefixed with `_`)
4. Constructor
5. Main public methods
6. Private methods (prefixed with `_`)
   - Regular private methods first
   - Helper methods last
7. Properties (use `@property` decorator instead of getters/setters)

## Section Separators

Use visual separators to clearly mark each section in the class:

```python
# ───────────────────────────────────────────────────────────
# SECTION NAME
# ───────────────────────────────────────────────────────────
```

Standard section names:

- `CONSTANTS` - Class-level constants
- `PROPERTIES` - Instance variables
- `CONSTRUCTOR` - `__init__` method
- `PUBLIC METHODS` - Public methods
- `PRIVATE METHODS` - Private methods (prefixed with `_`)
  - Regular private methods first
  - Helper methods last (use inline comment to separate them)
- `GETTERS` - Properties and getters

## Access Modifiers

- Public: Methods and variables used externally (no prefix)
- Private: Internal methods and variables (prefix with `_`)

## Function Naming Conventions

Functions should always start with a verb that clearly describes the action they perform.

**Common Verbs for Regular Methods:**

- `calculate_` - Perform calculations (e.g., `calculate_total`, `calculate_profit`)
- `get_` - Retrieve or fetch data (e.g., `get_price`, `get_order`)
- `set_` - Assign or update values (e.g., `set_stop_loss`, `set_status`)
- `update_` - Modify existing data (e.g., `update_position`, `update_state`)
- `validate_` - Check correctness (e.g., `validate_price`, `validate_order`)
- `create_` - Instantiate new objects (e.g., `create_order`, `create_snapshot`)
- `delete_` - Remove data (e.g., `delete_order`, `delete_record`)
- `process_` - Execute business logic (e.g., `process_order`, `process_data`)
- `handle_` - Respond to events (e.g., `handle_tick`, `handle_error`)
- `check_` - Verify conditions (e.g., `check_status`, `check_availability`)
- `is_` - Boolean checks (e.g., `is_valid`, `is_open`)
- `has_` - Existence checks (e.g., `has_position`, `has_permission`)

**Common Verbs for Helper Methods:**

- `_format_` - Transform data presentation (e.g., `_format_timestamp`, `_format_price`)
- `_parse_` - Extract or convert data (e.g., `_parse_response`, `_parse_config`)
- `_convert_` - Transform data types (e.g., `_convert_to_float`, `_convert_timestamp`)
- `_extract_` - Pull specific data (e.g., `_extract_price`, `_extract_metadata`)
- `_build_` - Construct complex objects (e.g., `_build_request`, `_build_payload`)
- `_normalize_` - Standardize data (e.g., `_normalize_symbol`, `_normalize_price`)
- `_sanitize_` - Clean data (e.g., `_sanitize_input`, `_sanitize_string`)

## Example Structure

```python
class Order:
    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    ticket: int
    _entry_price: float
    _stop_loss: float

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, order_ticket: int):
        self.ticket = order_ticket
        self._entry_price = 0.0
        self._stop_loss = 0.0

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def open(self) -> bool:
        pass

    def close(self) -> bool:
        pass

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_price(self, price: float) -> bool:
        pass

    def _update_internal_state(self) -> None:
        pass

    def _calculate_risk_reward(self) -> float:
        pass

    # Helpers
    def _format_order_data(self) -> dict:
        pass

    def _normalize_price(self, price: float) -> float:
        pass

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def entry_price(self) -> float:
        return self._entry_price

    @property
    def stop_loss(self) -> float:
        return self._stop_loss

    @stop_loss.setter
    def stop_loss(self, price: float) -> None:
        if self._validate_price(price):
            self._stop_loss = price
```
