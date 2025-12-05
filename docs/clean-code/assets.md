# Asset Guidelines

Guide on how an asset should be structured and organized.

- An asset must follow class guidelines. See [classes.md](./classes.md)
- An asset must pass all linters using `make run-linter-checks FILE=path/to/file.py` or `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- An asset extends `AssetService` which implements `AssetInterface`

# 1.0 Asset Structure

```python
class Asset(AssetService):
    # Class-level properties (required)
    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]

    # Constructor __init__
    def __init__(self) -> None:
        super().__init__()
        self._strategies = [
            # Strategy instances
        ]
```

# 2.0 Required Properties

| Property        | Type                      | Description                             |
| --------------- | ------------------------- | --------------------------------------- |
| `_symbol`       | `str`                     | Trading pair symbol (e.g., `"BTCUSDT"`) |
| `_gateway_name` | `str`                     | Gateway identifier (e.g., `"binance"`)  |
| `_strategies`   | `List[StrategyInterface]` | List of strategy instances              |

# 3.0 Constructor

Must call `super().__init__()` and configure strategies.

```python
def __init__(self) -> None:
    super().__init__()

    self._strategies = [
        EMA5BreakoutStrategy(
            id="ema5_breakout",
            allocation=1000,
            leverage=3,
            enabled=True,
        ),
    ]
```

# 4.0 Strategy Configuration

Each strategy instance requires:

| Parameter    | Type    | Description                         |
| ------------ | ------- | ----------------------------------- |
| `id`         | `str`   | Unique strategy identifier          |
| `allocation` | `float` | Capital allocation for the strategy |
| `leverage`   | `int`   | Leverage multiplier                 |
| `enabled`    | `bool`  | Whether strategy is active          |

# 5.0 Available Properties (from AssetInterface)

These getters are defined in `AssetInterface` and implemented in `AssetService`:

| Property                | Type                      | Description                        |
| ----------------------- | ------------------------- | ---------------------------------- |
| `symbol`                | `str`                     | Returns `_symbol` value            |
| `gateway`               | `GatewayService`          | Returns configured gateway         |
| `strategies`            | `List[StrategyInterface]` | Returns list of strategies         |
| `is_historical_filling` | `bool`                    | Whether processing historical data |

**Note**: Do not define new public getters/setters directly in your asset class. If you need new public accessors, they should be added to `AssetInterface` first.

# 6.0 Lifecycle Hooks (inherited, do not override unless necessary)

| Method                  | When Called             | Purpose                       |
| ----------------------- | ----------------------- | ----------------------------- |
| `setup(**kwargs)`       | Before execution starts | Configures runtime parameters |
| `on_tick(tick)`         | On each market tick     | Propagates to strategies      |
| `on_transaction(order)` | On order completion     | Propagates to strategies      |
| `on_end()`              | When execution ends     | Cleanup and finalization      |

# 7.0 File Location

Assets are located in `assets/` directory with their own folder:

- `assets/btcusdt/__init__.py` � BTCUSDT asset
- `assets/ethusdt/__init__.py` � ETHUSDT asset

# 8.0 Example

```python
from typing import List

from interfaces.strategy import StrategyInterface
from services.asset import AssetService
from strategies.ema5_breakout import EMA5BreakoutStrategy


class Asset(AssetService):
    _symbol = "BTCUSDT"
    _gateway_name = "binance"
    _strategies: List[StrategyInterface]

    def __init__(self) -> None:
        super().__init__()

        self._strategies = [
            EMA5BreakoutStrategy(
                id="ema5_breakout",
                allocation=1000,
                leverage=3,
                enabled=True,
            ),
        ]
```

# 9.0 Anti-patterns to Avoid

- **Missing `super().__init__()`**: Always call parent constructor
- **Trading logic in asset**: Assets only configure strategies. Trading logic belongs in strategies.
- **Overriding lifecycle hooks**: Use inherited hooks unless you need to extend behavior (call `super()` if overriding)
- **Hardcoding gateway configuration**: Use `_gateway_name` property, let `AssetService` handle gateway creation
- **Strategy classes instead of instances**: Use strategy instances (`EMA5BreakoutStrategy(...)`, not `EMA5BreakoutStrategy`)
