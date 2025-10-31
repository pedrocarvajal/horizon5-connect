# Class Organization

This guide applies when auditing a class during code review.
Follow these organization principles.

## Rules

- Do not modify method signatures or logic
- Reorganize methods vertically into clear sections
- Use proper naming conventions (underscore prefix for private members)

## Recommended Section Order

1. Public variables
2. Private variables (prefixed with `_`)
3. Constructor
4. Main public methods
5. Private helper methods (prefixed with `_`)
6. Properties (use `@property` decorator instead of getters/setters)

## Access Modifiers

- Public: Methods and variables used externally (no prefix)
- Private: Internal methods and variables (prefix with `_`)

## Example Structure

```python
class Order:
    ticket: int

    _entry_price: float
    _stop_loss: float

    def __init__(self, order_ticket: int):
        self.ticket = order_ticket
        self._entry_price = 0.0
        self._stop_loss = 0.0

    def open(self) -> bool:
        pass

    def close(self) -> bool:
        pass

    def _validate_price(self, price: float) -> bool:
        pass

    def _update_internal_state(self) -> None:
        pass

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
