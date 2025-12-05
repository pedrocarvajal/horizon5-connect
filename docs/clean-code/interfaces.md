# Interface Guidelines

Guide on how an interface should be structured and organized.

- An interface must pass all linters configured in the project using `make run-linter-checks FILE=path/to/file.py` or directly `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- An interface must be organized based on guideline 1.0
- For code style and formatting, review guideline 2.0
- Interfaces define contracts: public properties and public methods that implementing classes must provide
- For variable naming conventions, see [variables.md](./commons/variables.md)
- For complex types, create models instead of using `Dict[str, Any]` or similar. See [models.md](./commons/models.md)

# Guidelines

## 1.0 Interface Hierarchy

```python
class NameInterface(ABC):
    # Public properties (abstract)
    # {Blank separator line}

    # Constructor requirements (if special initialization is needed)
    # {Blank separator line}

    # Public methods (abstract, sorted alphabetically)
    # {Blank separator line}

    # Public getters (@property @abstractmethod)
    # {Blank separator line}

    # Public setters (@<name>.setter @abstractmethod)
    # {Blank separator line}
```

**Important**: The interface is the "public face" of a class. All public getters and setters must be defined in the interface, not in the implementing class directly.

## 2.0 How to Define Interfaces

### 2.1 Public Properties

Use `@property` with `@abstractmethod` to define required public properties:

```python
from abc import ABC, abstractmethod

class AssetInterface(ABC):
    @property
    @abstractmethod
    def symbol(self) -> str:
        pass

    @property
    @abstractmethod
    def gateway_name(self) -> str:
        pass
```

### 2.2 Public Methods

Define abstract methods that implementing classes must provide:

```python
class StrategyInterface(ABC):
    @abstractmethod
    def on_tick(self, tick: TickModel) -> None:
        pass

    @abstractmethod
    def on_new_minute(self) -> None:
        pass

    @abstractmethod
    def setup(self) -> None:
        pass
```

### 2.3 Public Getters

Define getters in the interface using `@property` with `@abstractmethod`. The implementing class will provide the implementation:

```python
class OrderbookInterface(ABC):
    @property
    @abstractmethod
    def balance(self) -> float:
        pass

    @property
    @abstractmethod
    def nav(self) -> float:
        pass

    @property
    @abstractmethod
    def exposure(self) -> float:
        pass
```

### 2.4 Public Setters

Define setters in the interface using `@<name>.setter` with `@abstractmethod`:

```python
class OrderbookInterface(ABC):
    @property
    @abstractmethod
    def margin_call_active(self) -> bool:
        pass

    @margin_call_active.setter
    @abstractmethod
    def margin_call_active(self, value: bool) -> None:
        pass
```

### 2.5 Constructor Requirements

Document special initialization requirements through abstract properties that must be set during construction:

```python
class PortfolioInterface(ABC):
    @property
    @abstractmethod
    def identifier(self) -> str:
        pass

    @abstractmethod
    def setup_assets(self) -> None:
        pass
```

### 2.6 Imports

Group imports in this order, separated by blank lines:

```python
from abc import ABC, abstractmethod
from typing import List, Optional

from models.tick import TickModel
```

Order: standard library, third-party, local imports.

### 2.7 Multi-line Parameters

Avoid:

```python
def execute_order(self, symbol: str, side: OrderSide, volume: float, price: Optional[float]) -> OrderModel:
```

Preferred:

```python
def execute_order(
    self,
    symbol: str,
    side: OrderSide,
    volume: float,
    price: Optional[float],
) -> OrderModel:
```

### 2.8 Complex Type Hints

Avoid:

```python
def get_strategies(self) -> List[Type[StrategyInterface]]:
```

Preferred for long type hints:

```python
def get_strategies(
    self,
) -> List[Type[StrategyInterface]]:
```

## 3.0 Anti-patterns to Avoid

- **Fat interfaces**: Interfaces with too many methods. Split into smaller, focused interfaces (Interface Segregation Principle).
- **Implementation details**: Never include private methods or implementation logic in interfaces.
- **Concrete dependencies**: Interfaces should depend on abstractions, not concrete classes.
- **Missing type hints**: All properties and methods must have complete type annotations.
- **Inconsistent naming**: Interface names must end with `Interface` suffix (e.g., `AssetInterface`, `StrategyInterface`).
- **Getters/setters in implementing class only**: All public getters and setters must be defined in the interface first.
