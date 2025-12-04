# Test Standards

Guidelines for writing tests.
Use this document for code review validation and fixes.

## Structure

### Directory Organization

```
tests/
   {category}/                      # Test category (unit, services, integration, e2e)
      {domain}/                     # Domain grouping when multiple tests share context
         wrappers/                  # Domain-specific wrappers
            {domain}.py             # Wrapper with shared setup, fixtures, assertions
         assets/                    # Test-only implementations (optional)
         fixtures/                  # JSON/data files for test validation (optional)
         test_{feature}.py          # Test files for the domain
      wrappers/                     # Category-level wrappers (when no domain grouping)
      test_{feature}.py             # Standalone tests (when no domain grouping needed)
```

**When to create domain grouping:**

- 2+ test files testing the same domain
- Tests share common setup, fixtures, or assertions
- Domain has specific test assets or data files

**Examples:**

```
tests/
   unit/
      test_get_slug.py              # Standalone (no domain grouping needed)
      test_parse.py
   services/
      wrappers/
         orderbook.py               # Shared wrapper for orderbook tests
      test_service_orderbook.py
      test_service_orderbook_cancel.py
      test_service_orderbook_financial.py
   integration/
      binance/                      # Domain: binance gateway
         wrappers/
            binance.py              # Binance-specific setup, cleanup, assertions
         test_binance_symbol.py
         test_binance_order.py
         test_binance_account.py
   e2e/
      wrappers/
         indicator.py               # Shared wrapper for indicator tests
      assets/
         btcusdt.py                  # Test-only asset implementation
      fixtures/
         indicator_ma_expected.json
      test_indicator_ma.py
      test_indicator_volatility.py
```

### File Naming

- Test files: `test_{feature_name}.py`
- Wrapper files: `wrappers/{wrapper_name}.py`
- Test classes: `Test{FeatureName}(WrapperClass)`

## Wrapper Pattern

Every test category uses base wrappers that encapsulate shared setup and helper methods.

### Wrapper Responsibilities

1. **Initialization** - Service instantiation and dependency injection
2. **Test Fixtures** - Factory methods for creating test objects
3. **Setup/Teardown** - Environment preparation and cleanup
4. **Assertion Helpers** - Domain-specific validation methods

### Wrapper Structure

Follow the class structure defined in [classes.md](./classes.md).

**Additional wrapper-specific methods:**

| Prefix               | Purpose                           | Example                                 |
| -------------------- | --------------------------------- | --------------------------------------- |
| `_create_`           | Factory methods for test entities | `_create_order()`, `_create_tick()`     |
| `_assert_`           | Domain-specific assertion helpers | `_assert_symbol_info_is_valid()`        |
| `_open_` / `_close_` | Resource lifecycle helpers        | `_open_position()`, `_close_position()` |

## Test Class Structure

### Class Constants

Define expected values and tolerances as class-level constants:

```python
class TestFeatureName(WrapperClass):
    _EXPECTED_TOTAL_COUNT: int = 743
    _EXPECTED_SUBSET_COUNT: int = 10
    _TOLERANCE: float = 0.01
```

### Test Method Naming

Format: `test_{action}_{condition}_{expected_outcome}`

Examples:

- `test_open_order_with_sufficient_margin_succeeds`
- `test_initialization_leverage_defaults_to_one_when_zero`
- `test_refresh_closes_order_when_take_profit_reached`

### Test Method Structure

```python
def test_action_condition_outcome(self) -> None:
    # Arrange - Setup preconditions
    tick = self._create_tick(50000.0)
    self._orderbook.refresh(tick)
    order = self._create_order()

    # Act - Execute the action under test
    self._orderbook.open(order)

    # Assert - Verify expected outcomes
    assert order.status == OrderStatus.OPEN
    assert order.executed_volume == 0.01
```

## Assertions

### Direct Assertions

Use `assert` statements with clear conditions:

```python
assert len(candles) == self._EXPECTED_TOTAL_CANDLES
assert order.status == OrderStatus.OPEN
assert abs(actual - expected) < self._TOLERANCE
```

### Assertion Messages (Integration Tests)

Include descriptive messages for external system validations:

```python
assert symbol_info is not None, "Symbol info should not be None"
assert leverage >= 1, f"Leverage should be >= 1, got {leverage}"
```

### Tolerance Comparisons

Use absolute difference for floating-point comparisons:

```python
assert abs(actual_value - expected_value) < self._PRICE_TOLERANCE
```

### Complex Assertions as Helper Methods

Extract domain-specific validations to private methods:

```python
def _assert_symbol_info_is_valid(
    self,
    symbol_info: GatewaySymbolInfoModel,
    expected_symbol: Optional[str] = None,
) -> None:
    if expected_symbol is None:
        expected_symbol = self._SYMBOL

    assert type(symbol_info) is GatewaySymbolInfoModel
    assert symbol_info.symbol == expected_symbol
    assert symbol_info.price_precision >= 0
```

## Test Data

### JSON Fixtures

Store expected values in `tests/{category}/fixtures/`:

```python
def get_json_data(self, path: str) -> List[Dict[str, Any]]:
    json_path = Path(__file__).parent.parent / "fixtures" / path
    with json_path.open() as file:
        return json.load(file)
```

Usage:

```python
expected_values = self.get_json_data("indicator_ma_expected.json")
```

## Linter Compliance

All tests must pass each linter individually:

```bash
uv run ruff format --check .    # Code formatting (PEP 8)
uv run ruff check .             # Linting rules
uv run pyright                  # Static type checking
uv run pydocstyle .             # Docstring conventions (PEP 257)
```

**Test-specific requirements:**

- All methods require type annotations (return `-> None` for test methods)
- Wrappers require module and class docstrings
- Test classes do not require docstrings (behavior described in method names)
