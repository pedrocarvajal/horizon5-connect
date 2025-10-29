# Type Annotations

Standards for using type annotations in Python.

## General Rules

| Case                 | Correct                      | Incorrect                        |
| -------------------- | ---------------------------- | -------------------------------- |
| Instance variable    | `_gateway: GatewayService`   | `_gateway: type[GatewayService]` |
| Class variable       | `_registry: type[BaseClass]` | `_registry: BaseClass`           |
| Instance return      | `-> GatewayService`          | `-> type[GatewayService]`        |
| Class return         | `-> type[GatewayService]`    | `-> GatewayService`              |
| Optional             | `Order \| None`              | `Optional[Order]`                |
| Union                | `int \| float`               | `Union[int, float]`              |
| Generic lists        | `list[str]`                  | `List[str]`                      |
| Generic dictionaries | `dict[str, int]`             | `Dict[str, int]`                 |

## Instances vs Classes

**Instances** (common case):

```python
class AssetService:
    _gateway: GatewayService
    _analytic: AnalyticService

    def __init__(self) -> None:
        self._gateway = GatewayService()
        self._analytic = AnalyticService()
```

**Classes** (factories/registries):

```python
class StrategyFactory:
    _strategies: dict[str, type[StrategyInterface]]

    def register(self, name: str, cls: type[StrategyInterface]) -> None:
        self._strategies[name] = cls
```

## Collections

```python
_strategies: list[StrategyInterface]
_timeframes: list[Timeframe]
_candlesticks: dict[Timeframe, list[CandlestickModel]]
_config: dict[str, Any]
```

## Optional and Union Types

```python
def get_order(order_id: str) -> Order | None:
    pass

def process(value: int | float) -> str | bool:
    pass
```

## Properties

Properties must return the attribute type:

```python
@property
def gateway(self) -> GatewayService:
    return self._gateway

@property
def strategies(self) -> list[StrategyInterface]:
    return self._strategies
```

## Pydantic Models

Use private attributes with `computed_field` for properties with logic:

```python
class CandlestickModel(BaseModel):
    _symbol: str
    _open_price: float
    _high_price: float
    _low_price: float
    _close_price: float

    @computed_field
    @property
    def symbol(self) -> str:
        return self._symbol

    @symbol.setter
    def symbol(self, value: str) -> None:
        self._symbol = value

    @computed_field
    @property
    def open_price(self) -> float:
        return self._open_price

    @open_price.setter
    def open_price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Open price must be greater than 0")
        self._open_price = value
```

## Using Any

Use `Any` only when necessary:

```python
def setup(self, **kwargs: Any) -> None:
    pass

_config: dict[str, Any]
```

Avoid:

```python
def calculate(data: Any) -> Any:
    pass
```
