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
6. Private helper methods (prefixed with `_`)
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
- `PRIVATE METHODS` - Private/helper methods (prefixed with `_`)
- `GETTERS` - Properties and getters

## Access Modifiers

- Public: Methods and variables used externally (no prefix)
- Private: Internal methods and variables (prefix with `_`)

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
