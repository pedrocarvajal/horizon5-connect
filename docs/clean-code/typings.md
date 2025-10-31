# Type Annotations

Standards for using type annotations in Python.

## Required Imports

Always import from `typing` for type annotations:

```python
from typing import Any, Dict, List, Optional, Union
```

## General Rules

| Case                 | Correct                      | Incorrect                        |
| -------------------- | ---------------------------- | -------------------------------- |
| Instance variable    | `_gateway: GatewayService`   | `_gateway: type[GatewayService]` |
| Class variable       | `_registry: type[BaseClass]` | `_registry: BaseClass`           |
| Instance return      | `-> GatewayService`          | `-> type[GatewayService]`        |
| Class return         | `-> type[GatewayService]`    | `-> GatewayService`              |
| Optional             | `Optional[Order]`            | `Order \| None`                  |
| Union                | `Union[int, float]`          | `int \| float`                   |
| Generic lists        | `List[str]`                  | `list[str]`                      |
| Generic dictionaries | `Dict[str, int]`             | `dict[str, int]`                 |

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
from typing import Dict

class StrategyFactory:
    _strategies: Dict[str, type[StrategyInterface]]

    def register(self, name: str, cls: type[StrategyInterface]) -> None:
        self._strategies[name] = cls
```

## Collections

```python
from typing import Any, Dict, List

_strategies: List[StrategyInterface]
_config: Dict[str, Any]
```

## Optional and Union Types

```python
from typing import Optional, Union

def get_order(order_id: str) -> Optional[Order]:
    pass

def process(value: Union[int, float]) -> Union[str, bool]:
    pass
```

## Properties

Properties must return the attribute type:

```python
from typing import List

@property
def gateway(self) -> GatewayService:
    return self._gateway

@property
def strategies(self) -> List[StrategyInterface]:
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
from typing import Any, Dict

def setup(self, **kwargs: Any) -> None:
    pass

_config: Dict[str, Any]
```

Avoid:

```python
def calculate(data: Any) -> Any:
    pass
```

## Rationale

Este proyecto usa el estándar de `typing` explícito (`Optional`, `Union`, `List`, `Dict`) en lugar de la sintaxis moderna de Python 3.10+ (`|`, `list`, `dict`) por las siguientes razones:

1. **Compatibilidad con Python 3.9**: Las versiones anteriores no soportan la sintaxis moderna
2. **Claridad**: `Optional[X]` es más explícito que `X | None`
3. **Consistencia**: Evita mezclar estilos en el codebase
4. **Compatibilidad con herramientas**: Algunas librerías aún esperan el estándar de `typing`

### Configuración de Ruff

Las siguientes reglas están deshabilitadas en `pyproject.toml`:

```toml
ignore = [
    "UP006",   # list vs List, dict vs Dict
    "UP007",   # Union[X, Y] vs X | Y
    "UP035",   # typing.List/Dict deprecated
    "UP045",   # Optional[X] vs X | None
]
```
