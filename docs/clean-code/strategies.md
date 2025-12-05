# Strategy Guidelines

Guide on how a strategy should be structured and organized.

- A strategy must follow class guidelines. See [classes.md](./classes.md)
- A strategy must pass all linters using `make run-linter-checks FILE=path/to/file.py` or `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- A strategy extends `StrategyService` which implements `StrategyInterface`

# 1.0 Strategy Structure

```python
class MyStrategy(StrategyService):
    # Class-level properties
    _enabled = False
    _name = "MyStrategy"
    _settings: Dict[str, Any]

    # Constructor __init__
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._settings = kwargs.get("settings", {})
        self._candles = {
            # Candle services with indicators
        }

    # Lifecycle hooks (override as needed)
    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)

    def on_new_hour(self) -> None:
        super().on_new_hour()

    # Private methods for trading logic
    def _check_entry_conditions(self) -> None:
        pass
```

# 2.0 Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `_enabled` | `bool` | Default enabled state (usually `False`) |
| `_name` | `str` | Strategy display name |

# 3.0 Constructor

Must call `super().__init__(**kwargs)` and configure candles/indicators.

```python
def __init__(self, **kwargs: Any) -> None:
    super().__init__(**kwargs)

    self._settings = kwargs.get("settings", {
        "take_profit_percentage": 0.03,
        "stop_loss_percentage": 0.15,
    })

    self._candles = {
        Timeframe.ONE_HOUR: CandleService(
            timeframe=Timeframe.ONE_HOUR,
            indicators=[
                MAIndicator(
                    key="ema5",
                    period=5,
                    price_to_use="close_price",
                    exponential=True,
                ),
            ],
        )
    }
```

# 4.0 Lifecycle Hooks

Override these methods to implement trading logic. **Always call `super()` first**.

| Method | When Called | Use Case |
|--------|-------------|----------|
| `on_tick(tick)` | Every market tick | Update current tick, fast checks |
| `on_new_minute()` | New minute starts | Minute-based signals |
| `on_new_hour()` | New hour starts | Hourly analysis, entry checks |
| `on_new_day()` | New day starts | Daily calculations, reset states |
| `on_new_week()` | New week starts | Weekly analysis |
| `on_new_month()` | New month starts | Monthly rebalancing |
| `on_transaction(order)` | Order status changes | Handle order events, recovery logic |
| `on_end()` | Execution ends | Cleanup, final reporting |

Example:

```python
def on_tick(self, tick: TickModel) -> None:
    super().on_tick(tick)
    self._tick = tick

def on_new_hour(self) -> None:
    super().on_new_hour()
    self._check_entry_conditions()

def on_transaction(self, order: OrderModel) -> None:
    super().on_transaction(order)
    if order.status.is_closed() and order.profit < 0:
        self._open_recovery_order(order)
```

# 5.0 Available Properties (from StrategyInterface)

These getters are defined in `StrategyInterface` and implemented in `StrategyService`:

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Strategy unique identifier |
| `name` | `str` | Strategy display name |
| `enabled` | `bool` | Whether strategy is enabled |
| `backtest` | `bool` | Whether running in backtest mode |
| `asset` | `AssetService` | Asset this strategy trades |
| `orderbook` | `OrderbookService` | Order management service |
| `allocation` | `float` | Capital allocation |
| `nav` | `float` | Net asset value |
| `exposure` | `float` | Total market exposure |
| `balance` | `float` | Current cash balance |
| `orders` | `List[OrderModel]` | All orders |
| `is_live` | `bool` | Whether in live trading mode |
| `is_available_to_open_orders` | `bool` | Whether can open new orders |

**Note**: Do not define new public getters/setters directly in your strategy class. If you need new public accessors, they should be added to `StrategyInterface` first.

# 6.0 Available Methods (from StrategyService)

## 6.1 `open_order`

Use this method to open orders. **Do not create orders manually**.

```python
self.open_order(
    side=OrderSide.BUY,
    price=current_price,
    take_profit_price=take_profit_price,
    stop_loss_price=stop_loss_price,
    volume=volume,
    variables={"layer": 0},
)
```

# 7.0 Working with Candles and Indicators

## 7.1 Defining Candles

Use `CandleService` with indicators in `__init__`:

```python
self._candles = {
    Timeframe.ONE_HOUR: CandleService(
        timeframe=Timeframe.ONE_HOUR,
        indicators=[
            MAIndicator(key="ema5", period=5, price_to_use="close_price", exponential=True),
        ],
    )
}
```

## 7.2 Accessing Indicator Values

```python
candle_service = self._candles[Timeframe.ONE_HOUR]
candles = candle_service.candles
current_ema5 = candles[-1]["i"]["ema5"]["value"]
previous_ema5 = candles[-2]["i"]["ema5"]["value"]
```

# 8.0 Working with Orderbook

## 8.1 Query Orders

```python
open_buy_orders = self.orderbook.where(
    side=OrderSide.BUY,
    status=OrderStatus.OPEN,
)
```

# 9.0 File Location

Strategies are located in `strategies/` directory with their own folder:

- `strategies/ema5_breakout/__init__.py` � EMA5 Breakout strategy
- `strategies/mean_reversion/__init__.py` � Mean Reversion strategy

# 10.0 Example

```python
from typing import Any, Dict

from enums.order_side import OrderSide
from enums.timeframe import Timeframe
from indicators.ma import MAIndicator
from models.order import OrderModel
from models.tick import TickModel
from services.candle import CandleService
from services.strategy import StrategyService


class MyStrategy(StrategyService):
    _enabled = False
    _name = "MyStrategy"
    _settings: Dict[str, Any]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self._settings = kwargs.get("settings", {
            "take_profit_percentage": 0.03,
            "stop_loss_percentage": 0.15,
        })

        self._candles = {
            Timeframe.ONE_HOUR: CandleService(
                timeframe=Timeframe.ONE_HOUR,
                indicators=[
                    MAIndicator(key="ema5", period=5, price_to_use="close_price", exponential=True),
                ],
            )
        }

    def on_tick(self, tick: TickModel) -> None:
        super().on_tick(tick)
        self._tick = tick

    def on_new_hour(self) -> None:
        super().on_new_hour()
        self._check_entry_conditions()

    def on_transaction(self, order: OrderModel) -> None:
        super().on_transaction(order)

    def _check_entry_conditions(self) -> None:
        pass
```

# 11.0 Anti-patterns to Avoid

- **Missing `super()` calls**: Always call parent method in lifecycle hooks
- **Creating orders manually**: Use `self.open_order()` method
- **Building candles manually**: Use `CandleService` with indicators
- **Direct orderbook manipulation**: Use `self.orderbook.where()` for queries, `self.open_order()` for creation
- **Trading logic in `on_tick`**: Use `on_tick` only for fast updates. Heavy logic goes in `on_new_hour`, `on_new_day`, etc.
- **Accessing `_tick` without null check**: Always verify `self._tick is not None` before using
- **Ignoring `is_live` check**: Use `self.is_live` to differentiate backtest from live behavior
