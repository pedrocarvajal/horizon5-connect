# Testing Conventions

This guide defines the standard for writing integration and unit tests in Python using `unittest`. For general coding conventions, see the other clean-code documentation files.

## Test Class Structure

Test classes follow the same organization principles as regular classes (see `class-organization.md`), with specific sections for test-specific elements.

**Recommended Section Order:**

1. **CONSTANTS** - Test configuration values (symbols, default values, etc.)
2. **PROPERTIES** - Instance variables (logger, gateway, services)
3. **CONSTRUCTOR** - `setUp()` method for test initialization
4. **PUBLIC METHODS** - Test methods (prefixed with `test_`)
5. **PRIVATE METHODS** - Helper methods for test operations

**Correct example:**

```python
class TestBinanceOpenOrder(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "btcusdt"
    _DEFAULT_LEVERAGE: int = 5

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────
    _log: LoggingService
    _gateway: GatewayService

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def setUp(self) -> None:
        self._log = LoggingService()
        self._log.setup(name="test_binance_open_order")
        self._gateway = self._create_gateway()
        self._setup_leverage()

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def test_open_market_order_and_close(self) -> None:
        pass

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _create_gateway(self) -> GatewayService:
        pass
```

## Test Method Naming

Test methods must start with `test_` prefix and use descriptive names that explain what is being tested.

**Correct examples:**

```python
def test_open_market_order_and_close(self) -> None:
    pass

def test_open_limit_order_and_cancel(self) -> None:
    pass

def test_get_futures_account(self) -> None:
    pass
```

**Incorrect examples:**

```python
def test_order(self) -> None:  # Too vague
    pass

def test1(self) -> None:  # Not descriptive
    pass

def open_market_order(self) -> None:  # Missing test_ prefix
    pass
```

## Test Method Structure

Test methods should follow the **Arrange-Act-Assert** pattern:

1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the operation being tested
3. **Assert**: Verify the results

**Correct example:**

```python
def test_open_market_order_and_close(self) -> None:
    volume = 0.002
    account_before = self._gateway.account()

    order = self._open_order(
        symbol=self._SYMBOL,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=volume,
    )

    if self._is_order_executed(order=order, account_before=account_before):
        self._close_position(order=order)
    else:
        self._cancel_order(order=order, account_before=account_before)

    self._verify_account_clean()
```

## Setup and Teardown

### setUp Method

Use `setUp()` to initialize common test dependencies. This method runs before each test method.

**Correct example:**

```python
def setUp(self) -> None:
    self._log = LoggingService()
    self._log.setup(name="test_binance_open_order")
    self._gateway = self._create_gateway()
    self._setup_leverage()
```

### tearDown Method

Use `tearDown()` only when cleanup is necessary (e.g., closing connections, cleaning up resources). For integration tests that interact with external APIs, prefer cleanup within test methods.

**When to use tearDown:**

```python
def tearDown(self) -> None:
    if self._gateway:
        self._gateway.close_connection()
```

**When NOT to use tearDown:**

For integration tests that need to verify cleanup (like checking account state), perform cleanup and verification within the test method itself.

## Assertions in Tests

### Assertion Messages

Always provide descriptive assertion messages that explain what failed and why.

**Correct examples:**

```python
assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
assert order.symbol == self._SYMBOL.upper(), "Symbol should match"
assert order.volume == volume, f"Volume should be {volume}"
assert order.status == OrderStatus.CANCELLED, (
    f"Order status should be CANCELLED, but got {cancelled_order.status.value}"
)
```

**Incorrect examples:**

```python
assert isinstance(order, GatewayOrderModel)  # No message
assert order.symbol == self._SYMBOL.upper()  # No message
```

### Assertion Helpers

Create private helper methods for complex or repeated assertion patterns.

**Correct example:**

```python
def _assert_order_valid(
    self,
    order: GatewayOrderModel,
    side: OrderSide,
    order_type: OrderType,
    volume: float,
    price: Optional[float] = None,
) -> None:
    assert isinstance(order, GatewayOrderModel), "Order should be a GatewayOrderModel"
    assert order.symbol == self._SYMBOL.upper(), "Symbol should match"
    assert order.side == side, f"Side should be {side.value}"
    assert order.order_type == order_type, f"Order type should be {order_type.value}"
    assert order.volume == volume, f"Volume should be {volume}"
    assert order.status is not None, "Status should be set"

    if price is not None:
        assert order.price == price, f"Price should be {price}"
```

## Test Helper Methods

Extract common test operations into private helper methods. These should follow the same naming conventions as regular helper methods (see `helper-definitions.md`), but are specific to test operations.

**Common test helper patterns:**

- `_create_*` - Create test objects (e.g., `_create_gateway()`)
- `_setup_*` - Configure test environment (e.g., `_setup_leverage()`)
- `_assert_*` - Verify conditions (e.g., `_assert_order_valid()`)
- `_is_*` - Boolean checks (e.g., `_is_order_executed()`)
- `_verify_*` - Final verification steps (e.g., `_verify_account_clean()`)
- `_calculate_*` - Compute test values (e.g., `_calculate_safe_limit_price()`)

**Correct example:**

```python
def _open_order(
    self,
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    volume: float,
    price: Optional[float] = None,
) -> GatewayOrderModel:
    order = self._gateway.open(
        symbol=symbol,
        side=side,
        order_type=order_type,
        volume=volume,
        price=price,
    )

    if order is None:
        self.skipTest("Order not available for testing. Check account balance and margin requirements.")

    self._assert_order_valid(order=order, side=side, order_type=order_type, volume=volume, price=price)
    return order
```

## Error Handling in Tests

### Skipping Tests

Use `self.skipTest()` when preconditions are not met (e.g., insufficient account balance, API unavailable).

**Correct example:**

```python
if order is None:
    self.skipTest("Order not available for testing. Check account balance and margin requirements.")
```

### Failing Tests

Use `self.fail()` with descriptive messages when test conditions cannot be met.

**Correct example:**

```python
if close_order is None:
    self.fail("Position should be closed. Failed to open opposite order.")
```

### Handling External Dependencies

For integration tests that depend on external services, gracefully handle failures:

```python
def _cancel_order(
    self,
    order: GatewayOrderModel,
    account_before: Optional[GatewayAccountModel],
) -> Optional[GatewayOrderModel]:
    closed_order = self._gateway.close(
        symbol=self._SYMBOL,
        order_id=order.id,
    )

    if closed_order is None:
        if account_before:
            account_check = self._gateway.account()

            if account_check and account_check.margin > account_before.margin:
                self._close_position(order=order)
                return None

        self.fail("Order should be cancelled. Check if the order was already filled or executed.")

    return closed_order
```

## Test Cleanup and Verification

### Verify Test State

Always verify that tests leave the system in a clean state, especially for integration tests.

**Correct example:**

```python
def _verify_account_clean(self) -> None:
    account_after = self._gateway.account()

    if account_after:
        assert account_after.locked == 0, "No orders should remain locked after closing"
        assert account_after.margin == 0, "No positions should remain open after closing"
```

### Cleanup in Test Methods

Perform cleanup operations within test methods to ensure proper verification:

```python
def test_open_market_order_and_close(self) -> None:
    volume = 0.002
    account_before = self._gateway.account()

    order = self._open_order(
        symbol=self._SYMBOL,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=volume,
    )

    if self._is_order_executed(order=order, account_before=account_before):
        self._close_position(order=order)
    else:
        self._cancel_order(order=order, account_before=account_before)

    self._verify_account_clean()
```

## Test Data Management

### Test Configuration Constants

Use class-level constants for test configuration values that are reused across multiple tests.

**Correct example:**

```python
class TestBinanceOpenOrder(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _SYMBOL: str = "btcusdt"
    _DEFAULT_LEVERAGE: int = 5
```

### Dynamic Test Data

Calculate test data dynamically when needed to avoid hardcoded values that may become invalid.

**Correct example:**

```python
def _calculate_safe_limit_price(self) -> float:
    symbol_info = self._gateway.get_symbol_info(symbol=self._SYMBOL)

    if symbol_info is None:
        return 200000.0

    min_price = symbol_info.min_price or 100.0
    max_price = symbol_info.max_price or 200000.0
    limit_price = min_price * 10

    if limit_price > max_price:
        limit_price = max_price * 0.9

    return limit_price
```

## Summary

| Aspect             | Rule                                                                                                  | Example                                      |
| ------------------ | ----------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Class structure    | Follow standard organization with CONSTANTS, PROPERTIES, CONSTRUCTOR, PUBLIC METHODS, PRIVATE METHODS | See class organization                       |
| Test method naming | Must start with `test_` and be descriptive                                                            | `test_open_market_order_and_close`           |
| Test structure     | Follow Arrange-Act-Assert pattern                                                                     | Arrange data → Act → Assert results          |
| Assertions         | Always include descriptive messages                                                                   | `assert x == y, "X should equal Y"`          |
| Helper methods     | Private methods with `_` prefix, action-based names                                                   | `_create_gateway()`, `_assert_order_valid()` |
| Cleanup            | Verify clean state at end of tests                                                                    | `_verify_account_clean()`                    |
| Constants          | Use class-level constants for configuration                                                           | `_SYMBOL: str = "btcusdt"`                   |
| Error handling     | Use `skipTest()` for missing preconditions, `fail()` for test failures                                | `self.skipTest("message")`                   |

## Benefits

- **Consistency**: All tests follow the same structure and patterns
- **Readability**: Clear test names and organization make tests easy to understand
- **Maintainability**: Helper methods reduce duplication and make tests easier to update
- **Reliability**: Proper cleanup and verification ensure tests don't leave system in bad state
- **Debugging**: Descriptive assertion messages make failures easy to diagnose
